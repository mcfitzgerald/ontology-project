"""
Vertex AI monitoring utilities for token counting and cost estimation.
Provides real-time cost tracking and usage limits to prevent runaway costs.
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import threading
import time

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    from google.cloud import storage
    VERTEX_AI_AVAILABLE = True
    
    # Initialize Vertex AI with project settings if available
    try:
        from ..config.settings import (
            GOOGLE_GENAI_USE_VERTEXAI,
            GOOGLE_CLOUD_PROJECT,
            GOOGLE_CLOUD_LOCATION
        )
        
        if GOOGLE_GENAI_USE_VERTEXAI and GOOGLE_CLOUD_PROJECT != 'your-project-id':
            vertexai.init(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_LOCATION)
            logging.info(f"Vertex AI initialized with project: {GOOGLE_CLOUD_PROJECT}")
    except ImportError:
        # Running standalone, settings not available
        pass
        
except ImportError:
    VERTEX_AI_AVAILABLE = False
    logging.warning("Vertex AI SDK not available. Cost monitoring features will be limited.")


@dataclass
class ModelPricing:
    """Pricing information for Vertex AI models (as of 2025)."""
    input_per_1k_tokens: float
    output_per_1k_tokens: float
    
    @property
    def input_per_million(self) -> float:
        """Cost per million input tokens."""
        return self.input_per_1k_tokens * 1000
    
    @property
    def output_per_million(self) -> float:
        """Cost per million output tokens."""
        return self.output_per_1k_tokens * 1000


# Vertex AI Pricing (USD) - Update these as needed
VERTEX_AI_PRICING = {
    # Gemini 2.0 Flash (new model)
    "gemini-2.0-flash": ModelPricing(
        input_per_1k_tokens=0.00035,   # $0.35 per 1M tokens
        output_per_1k_tokens=0.00105   # $1.05 per 1M tokens
    ),
    # Gemini 1.5 Flash
    "gemini-1.5-flash": ModelPricing(
        input_per_1k_tokens=0.00035,   # $0.35 per 1M tokens
        output_per_1k_tokens=0.00105   # $1.05 per 1M tokens
    ),
    # Gemini 1.5 Pro
    "gemini-1.5-pro": ModelPricing(
        input_per_1k_tokens=0.00125,   # $1.25 per 1M tokens
        output_per_1k_tokens=0.00375   # $3.75 per 1M tokens
    ),
    # Add more models as needed
}


@dataclass
class UsageStats:
    """Track usage statistics for cost monitoring."""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_requests: int = 0
    total_errors: int = 0
    total_cost: float = 0.0
    last_reset: datetime = field(default_factory=datetime.now)
    
    def reset(self):
        """Reset all counters."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_requests = 0
        self.total_errors = 0
        self.total_cost = 0.0
        self.last_reset = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "total_cost": self.total_cost,
            "last_reset": self.last_reset.isoformat()
        }


class TokenCounter:
    """Utility for counting tokens before making requests."""
    
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        self.model_name = model_name
        self._model = None
    
    @property
    def model(self):
        """Lazy load the model for token counting."""
        if self._model is None and VERTEX_AI_AVAILABLE:
            self._model = GenerativeModel(self.model_name)
        return self._model
    
    def count_tokens(self, content: str) -> Dict[str, int]:
        """
        Count tokens in the given content.
        
        Args:
            content: Text content to count tokens for
            
        Returns:
            Dictionary with token count information
        """
        if not VERTEX_AI_AVAILABLE:
            # Rough estimation if SDK not available
            # Approximate: 1 token ≈ 4 characters
            estimated_tokens = len(content) // 4
            return {
                "total_tokens": estimated_tokens,
                "billable_characters": len(content),
                "estimated": True
            }
        
        try:
            response = self.model.count_tokens(content)
            return {
                "total_tokens": response.total_tokens,
                "billable_characters": response.total_billable_characters,
                "estimated": False
            }
        except Exception as e:
            logging.error(f"Error counting tokens: {e}")
            # Fallback to estimation
            estimated_tokens = len(content) // 4
            return {
                "total_tokens": estimated_tokens,
                "billable_characters": len(content),
                "estimated": True,
                "error": str(e)
            }
    
    def estimate_cost(self, 
                     input_text: str, 
                     expected_output_ratio: float = 0.5) -> Dict[str, float]:
        """
        Estimate the cost of a request before making it.
        
        Args:
            input_text: The input prompt text
            expected_output_ratio: Expected output tokens as ratio of input (default 0.5)
            
        Returns:
            Dictionary with cost estimates
        """
        # Count input tokens
        input_count = self.count_tokens(input_text)
        input_tokens = input_count["total_tokens"]
        
        # Estimate output tokens
        estimated_output_tokens = int(input_tokens * expected_output_ratio)
        
        # Get pricing for the model
        pricing = VERTEX_AI_PRICING.get(self.model_name)
        if not pricing:
            logging.warning(f"No pricing info for model {self.model_name}, using default")
            pricing = VERTEX_AI_PRICING.get("gemini-2.0-flash")
        
        # Calculate costs
        input_cost = (input_tokens / 1000) * pricing.input_per_1k_tokens
        output_cost = (estimated_output_tokens / 1000) * pricing.output_per_1k_tokens
        total_cost = input_cost + output_cost
        
        return {
            "input_tokens": input_tokens,
            "estimated_output_tokens": estimated_output_tokens,
            "input_cost": input_cost,
            "estimated_output_cost": output_cost,
            "estimated_total_cost": total_cost,
            "model": self.model_name,
            "is_estimated": input_count.get("estimated", False)
        }


class SafeVertexAIClient:
    """
    Wrapper for Vertex AI client with built-in cost controls and monitoring.
    Prevents runaway costs by enforcing limits and tracking usage.
    """
    
    def __init__(self,
                 model_name: str = "gemini-2.0-flash",
                 daily_request_limit: int = 1000,
                 daily_cost_limit: float = 10.0,
                 hourly_request_limit: int = 100,
                 persist_stats: bool = True,
                 stats_file: Optional[Path] = None):
        """
        Initialize the safe client with limits.
        
        Args:
            model_name: Vertex AI model to use
            daily_request_limit: Maximum requests per day
            daily_cost_limit: Maximum cost per day in USD
            hourly_request_limit: Maximum requests per hour
            persist_stats: Whether to persist usage stats to disk
            stats_file: Path to stats file (auto-generated if None)
        """
        self.model_name = model_name
        self.daily_request_limit = daily_request_limit
        self.daily_cost_limit = daily_cost_limit
        self.hourly_request_limit = hourly_request_limit
        self.persist_stats = persist_stats
        
        # Setup stats file
        if stats_file is None:
            stats_file = Path.home() / ".adk_agents" / "vertex_ai_usage.json"
        self.stats_file = stats_file
        self.stats_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.token_counter = TokenCounter(model_name)
        self._model = None
        self._lock = threading.Lock()
        
        # Load or initialize stats
        self.daily_stats = self._load_stats()
        self.hourly_stats = UsageStats()
        self._last_hour_check = datetime.now()
        
        # Pricing info
        self.pricing = VERTEX_AI_PRICING.get(model_name, VERTEX_AI_PRICING["gemini-2.0-flash"])
    
    @property
    def model(self):
        """Lazy load the Vertex AI model."""
        if self._model is None and VERTEX_AI_AVAILABLE:
            self._model = GenerativeModel(self.model_name)
        return self._model
    
    def _load_stats(self) -> UsageStats:
        """Load usage statistics from disk."""
        if self.persist_stats and self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    data = json.load(f)
                    stats = UsageStats(
                        total_input_tokens=data.get("total_input_tokens", 0),
                        total_output_tokens=data.get("total_output_tokens", 0),
                        total_requests=data.get("total_requests", 0),
                        total_errors=data.get("total_errors", 0),
                        total_cost=data.get("total_cost", 0.0),
                        last_reset=datetime.fromisoformat(data.get("last_reset", datetime.now().isoformat()))
                    )
                    # Reset if it's a new day
                    if stats.last_reset.date() < datetime.now().date():
                        stats.reset()
                    return stats
            except Exception as e:
                logging.error(f"Error loading stats: {e}")
        
        return UsageStats()
    
    def _save_stats(self):
        """Save usage statistics to disk."""
        if self.persist_stats:
            try:
                with open(self.stats_file, 'w') as f:
                    json.dump(self.daily_stats.to_dict(), f, indent=2)
            except Exception as e:
                logging.error(f"Error saving stats: {e}")
    
    def _check_hourly_reset(self):
        """Check if we need to reset hourly stats."""
        now = datetime.now()
        if (now - self._last_hour_check).total_seconds() > 3600:
            self.hourly_stats.reset()
            self._last_hour_check = now
    
    def _check_limits(self, estimated_cost: float) -> Tuple[bool, str]:
        """
        Check if request would exceed any limits.
        
        Returns:
            Tuple of (allowed, reason_if_denied)
        """
        with self._lock:
            self._check_hourly_reset()
            
            # Check daily request limit
            if self.daily_stats.total_requests >= self.daily_request_limit:
                return False, f"Daily request limit exceeded ({self.daily_request_limit})"
            
            # Check hourly request limit
            if self.hourly_stats.total_requests >= self.hourly_request_limit:
                return False, f"Hourly request limit exceeded ({self.hourly_request_limit})"
            
            # Check daily cost limit
            if self.daily_stats.total_cost + estimated_cost > self.daily_cost_limit:
                return False, f"Daily cost limit would be exceeded (${self.daily_cost_limit})"
            
            return True, ""
    
    def _update_stats(self, input_tokens: int, output_tokens: int, cost: float, error: bool = False):
        """Update usage statistics."""
        with self._lock:
            # Update daily stats
            self.daily_stats.total_input_tokens += input_tokens
            self.daily_stats.total_output_tokens += output_tokens
            self.daily_stats.total_requests += 1
            self.daily_stats.total_cost += cost
            if error:
                self.daily_stats.total_errors += 1
            
            # Update hourly stats
            self.hourly_stats.total_input_tokens += input_tokens
            self.hourly_stats.total_output_tokens += output_tokens
            self.hourly_stats.total_requests += 1
            self.hourly_stats.total_cost += cost
            if error:
                self.hourly_stats.total_errors += 1
            
            # Save stats
            self._save_stats()
    
    def generate_content(self, 
                        prompt: str,
                        stream: bool = False,
                        **kwargs) -> Tuple[Optional[Any], Dict[str, Any]]:
        """
        Generate content with cost monitoring and limits.
        
        Args:
            prompt: The input prompt
            stream: Whether to stream the response
            **kwargs: Additional arguments for generate_content
            
        Returns:
            Tuple of (response, metadata) where metadata includes cost info
        """
        if not VERTEX_AI_AVAILABLE:
            return None, {"error": "Vertex AI SDK not available"}
        
        # Estimate cost
        cost_estimate = self.token_counter.estimate_cost(prompt)
        
        # Check limits
        allowed, reason = self._check_limits(cost_estimate["estimated_total_cost"])
        if not allowed:
            metadata = {
                "allowed": False,
                "reason": reason,
                "cost_estimate": cost_estimate,
                "daily_usage": self.get_usage_summary()
            }
            logging.warning(f"Request blocked: {reason}")
            return None, metadata
        
        # Make the request
        start_time = time.time()
        try:
            response = self.model.generate_content(
                prompt,
                stream=stream,
                **kwargs
            )
            
            # Calculate actual cost
            # Note: This is simplified - in production you'd extract actual token counts from response
            if hasattr(response, 'usage_metadata'):
                actual_input_tokens = response.usage_metadata.prompt_token_count
                actual_output_tokens = response.usage_metadata.candidates_token_count
            else:
                # Fallback to estimates
                actual_input_tokens = cost_estimate["input_tokens"]
                actual_output_tokens = len(response.text.split()) * 1.3  # Rough estimate
            
            actual_cost = (
                (actual_input_tokens / 1000) * self.pricing.input_per_1k_tokens +
                (actual_output_tokens / 1000) * self.pricing.output_per_1k_tokens
            )
            
            # Update stats
            self._update_stats(actual_input_tokens, actual_output_tokens, actual_cost)
            
            # Prepare metadata
            metadata = {
                "allowed": True,
                "model": self.model_name,
                "input_tokens": actual_input_tokens,
                "output_tokens": actual_output_tokens,
                "actual_cost": actual_cost,
                "response_time": time.time() - start_time,
                "daily_usage": self.get_usage_summary()
            }
            
            return response, metadata
            
        except Exception as e:
            # Update error stats
            self._update_stats(
                cost_estimate["input_tokens"], 
                0, 
                cost_estimate["input_cost"],  # Only charge for input on errors
                error=True
            )
            
            metadata = {
                "allowed": True,
                "error": str(e),
                "cost_estimate": cost_estimate,
                "response_time": time.time() - start_time,
                "daily_usage": self.get_usage_summary()
            }
            logging.error(f"Error generating content: {e}")
            return None, metadata
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get current usage summary."""
        with self._lock:
            daily_remaining_cost = self.daily_cost_limit - self.daily_stats.total_cost
            daily_remaining_requests = self.daily_request_limit - self.daily_stats.total_requests
            hourly_remaining_requests = self.hourly_request_limit - self.hourly_stats.total_requests
            
            return {
                "daily": {
                    "requests": self.daily_stats.total_requests,
                    "cost": round(self.daily_stats.total_cost, 4),
                    "input_tokens": self.daily_stats.total_input_tokens,
                    "output_tokens": self.daily_stats.total_output_tokens,
                    "errors": self.daily_stats.total_errors,
                    "remaining_cost": round(daily_remaining_cost, 4),
                    "remaining_requests": daily_remaining_requests,
                    "limit_cost": self.daily_cost_limit,
                    "limit_requests": self.daily_request_limit
                },
                "hourly": {
                    "requests": self.hourly_stats.total_requests,
                    "cost": round(self.hourly_stats.total_cost, 4),
                    "remaining_requests": hourly_remaining_requests,
                    "limit_requests": self.hourly_request_limit
                }
            }
    
    def reset_daily_stats(self):
        """Manually reset daily statistics."""
        with self._lock:
            self.daily_stats.reset()
            self._save_stats()
            logging.info("Daily statistics reset")
    
    def estimate_remaining_requests(self) -> Dict[str, int]:
        """Estimate how many more requests can be made within limits."""
        with self._lock:
            avg_cost_per_request = (
                self.daily_stats.total_cost / max(1, self.daily_stats.total_requests)
            )
            
            if avg_cost_per_request > 0:
                remaining_by_cost = int(
                    (self.daily_cost_limit - self.daily_stats.total_cost) / avg_cost_per_request
                )
            else:
                remaining_by_cost = self.daily_request_limit
            
            remaining_by_daily_limit = self.daily_request_limit - self.daily_stats.total_requests
            remaining_by_hourly_limit = self.hourly_request_limit - self.hourly_stats.total_requests
            
            return {
                "by_cost": remaining_by_cost,
                "by_daily_limit": remaining_by_daily_limit,
                "by_hourly_limit": remaining_by_hourly_limit,
                "effective": min(remaining_by_cost, remaining_by_daily_limit, remaining_by_hourly_limit)
            }


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Example 1: Token counting and cost estimation
    counter = TokenCounter("gemini-2.0-flash")
    
    test_prompt = """
    Analyze the manufacturing data and identify patterns that could lead to 
    significant cost savings. Focus on equipment efficiency, downtime patterns,
    and quality issues that impact overall productivity.
    """
    
    # Count tokens and estimate cost
    token_info = counter.count_tokens(test_prompt)
    cost_info = counter.estimate_cost(test_prompt, expected_output_ratio=2.0)
    
    print("Token Count:", token_info)
    print("Cost Estimate:", cost_info)
    
    # Example 2: Safe client with limits
    safe_client = SafeVertexAIClient(
        model_name="gemini-2.0-flash",
        daily_request_limit=100,
        daily_cost_limit=1.0,
        hourly_request_limit=20
    )
    
    # Check current usage
    print("\nCurrent Usage:", safe_client.get_usage_summary())
    
    # Estimate remaining requests
    print("\nRemaining Requests:", safe_client.estimate_remaining_requests())
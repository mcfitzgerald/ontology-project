"""
Rate Limiter for ADK Agents to prevent hitting API limits

Implements token bucket algorithm with configurable:
- Requests per minute limit
- Burst capacity
- Automatic throttling
"""

import asyncio
import time
from typing import Optional, Callable, Any
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass

from adk_agents.config.settings import (
    RATE_LIMIT_ENABLED,
    RATE_LIMIT_REQUESTS_PER_MINUTE,
    RATE_LIMIT_THROTTLE_MS,
    RATE_LIMIT_BURST_SIZE
)


@dataclass
class RateLimitStats:
    """Statistics about rate limiting"""
    total_requests: int = 0
    throttled_requests: int = 0
    current_rpm: float = 0.0
    last_request_time: Optional[datetime] = None
    average_wait_time_ms: float = 0.0


class RateLimiter:
    """
    Token bucket rate limiter for API requests.
    
    Allows burst capacity while maintaining average rate limit.
    """
    
    def __init__(self, 
                 requests_per_minute: int = RATE_LIMIT_REQUESTS_PER_MINUTE,
                 burst_size: int = RATE_LIMIT_BURST_SIZE,
                 enabled: bool = RATE_LIMIT_ENABLED):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum sustained request rate
            burst_size: Maximum burst capacity
            enabled: Whether rate limiting is enabled
        """
        self.enabled = enabled
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        
        # Token bucket parameters
        self.max_tokens = burst_size
        self.tokens = float(burst_size)
        self.refill_rate = requests_per_minute / 60.0  # tokens per second
        self.last_refill_time = time.monotonic()
        
        # Request history for calculating actual RPM
        self.request_times = deque(maxlen=100)
        
        # Statistics
        self.stats = RateLimitStats()
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> float:
        """
        Acquire tokens, waiting if necessary.
        
        Args:
            tokens: Number of tokens to acquire (default 1)
            
        Returns:
            Time waited in seconds
        """
        if not self.enabled:
            return 0.0
        
        start_time = time.monotonic()
        
        async with self._lock:
            # Refill tokens based on elapsed time
            self._refill_tokens()
            
            # Wait for tokens if needed
            wait_time = 0.0
            if self.tokens < tokens:
                tokens_needed = tokens - self.tokens
                wait_time = tokens_needed / self.refill_rate
                await asyncio.sleep(wait_time)
                self._refill_tokens()
                self.stats.throttled_requests += 1
            
            # Consume tokens
            self.tokens -= tokens
            
            # Update statistics
            now = datetime.now()
            self.request_times.append(now)
            self.stats.total_requests += 1
            self.stats.last_request_time = now
            self.stats.current_rpm = self._calculate_current_rpm()
            
            # Update average wait time
            actual_wait = time.monotonic() - start_time
            if self.stats.total_requests > 1:
                self.stats.average_wait_time_ms = (
                    (self.stats.average_wait_time_ms * (self.stats.total_requests - 1) + 
                     actual_wait * 1000) / self.stats.total_requests
                )
            else:
                self.stats.average_wait_time_ms = actual_wait * 1000
            
            return actual_wait
    
    def _refill_tokens(self):
        """Refill tokens based on elapsed time"""
        now = time.monotonic()
        elapsed = now - self.last_refill_time
        
        # Add tokens based on refill rate
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.max_tokens, self.tokens + tokens_to_add)
        self.last_refill_time = now
    
    def _calculate_current_rpm(self) -> float:
        """Calculate current requests per minute"""
        if len(self.request_times) < 2:
            return 0.0
        
        # Remove old requests (older than 1 minute)
        cutoff_time = datetime.now() - timedelta(minutes=1)
        while self.request_times and self.request_times[0] < cutoff_time:
            self.request_times.popleft()
        
        # Calculate RPM
        if len(self.request_times) >= 2:
            time_span = (self.request_times[-1] - self.request_times[0]).total_seconds()
            if time_span > 0:
                return len(self.request_times) * 60.0 / time_span
        
        return float(len(self.request_times))
    
    def get_stats(self) -> RateLimitStats:
        """Get current rate limiting statistics"""
        return self.stats
    
    def reset_stats(self):
        """Reset statistics"""
        self.stats = RateLimitStats()
        self.request_times.clear()
    
    async def execute_with_limit(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with rate limiting.
        
        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result of func
        """
        wait_time = await self.acquire()
        
        # Log if we had to wait
        if wait_time > 0.1:  # More than 100ms
            print(f"Rate limiter: Waited {wait_time:.2f}s before executing request")
        
        # Execute the function
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)


# Global rate limiter instance
_global_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    """Get or create the global rate limiter instance"""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = RateLimiter()
    return _global_rate_limiter


async def rate_limited_execute(func: Callable, *args, **kwargs) -> Any:
    """
    Convenience function to execute with global rate limiter.
    
    Args:
        func: Function to execute
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func
        
    Returns:
        Result of func
    """
    limiter = get_rate_limiter()
    return await limiter.execute_with_limit(func, *args, **kwargs)


def print_rate_limit_stats():
    """Print current rate limiting statistics"""
    limiter = get_rate_limiter()
    stats = limiter.get_stats()
    
    print("\n=== Rate Limiter Statistics ===")
    print(f"Enabled: {limiter.enabled}")
    print(f"Limit: {limiter.requests_per_minute} RPM")
    print(f"Burst Size: {limiter.burst_size}")
    print(f"Total Requests: {stats.total_requests}")
    print(f"Throttled Requests: {stats.throttled_requests}")
    print(f"Current RPM: {stats.current_rpm:.2f}")
    print(f"Average Wait Time: {stats.average_wait_time_ms:.0f}ms")
    if stats.last_request_time:
        print(f"Last Request: {stats.last_request_time.strftime('%H:%M:%S')}")
    print("==============================\n")


# Example usage in async context
async def example_usage():
    """Example of how to use the rate limiter"""
    import aiohttp
    
    # Create a rate limiter
    limiter = RateLimiter(requests_per_minute=30, burst_size=5)
    
    # Example API call function
    async def make_api_call(session, url):
        async with session.get(url) as response:
            return await response.text()
    
    # Make rate-limited API calls
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(10):
            # Each call will be rate limited
            task = limiter.execute_with_limit(
                make_api_call, 
                session, 
                f"https://api.example.com/data/{i}"
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
    
    # Print statistics
    stats = limiter.get_stats()
    print(f"Made {stats.total_requests} requests")
    print(f"Average wait time: {stats.average_wait_time_ms:.0f}ms")
    print(f"Current RPM: {stats.current_rpm:.2f}")


if __name__ == "__main__":
    # Test the rate limiter
    async def test():
        limiter = RateLimiter(requests_per_minute=120, burst_size=5)
        
        print("Testing rate limiter with 120 RPM limit...")
        
        # Simulate rapid requests
        for i in range(20):
            wait_time = await limiter.acquire()
            print(f"Request {i+1}: waited {wait_time*1000:.0f}ms")
            await asyncio.sleep(0.1)  # Simulate some work
        
        print_rate_limit_stats()
    
    asyncio.run(test())
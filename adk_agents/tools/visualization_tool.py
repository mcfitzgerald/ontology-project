"""Visualization tool for creating charts from manufacturing data."""
import io
import base64
import logging
from typing import Dict, Any, List, Optional, Union
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import pandas as pd
import google.genai.types as types
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)

async def create_visualization(
    data: Dict[str, Any],
    chart_type: str,
    title: str,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    tool_context: Optional[ToolContext] = None
) -> Dict[str, Any]:
    """Create a visualization from query results and save as artifact.
    
    Args:
        data: Query results with 'columns' and 'results' keys OR summary with cache_id
        chart_type: Type of chart ('line', 'bar', 'scatter', 'pie')
        title: Chart title
        x_label: X-axis label (optional)
        y_label: Y-axis label (optional)
        tool_context: Tool context for saving artifacts
        
    Returns:
        Dictionary with status and artifact information
    """
    try:
        # Handle cached results
        if 'summary' in data and 'cache_id' in data:
            # Working with a summary from cached results
            summary = data['summary']
            if 'sample_data' in summary:
                # Use sample data for visualization
                data = {
                    'results': summary['sample_data'],
                    'columns': summary.get('columns', [])
                }
            else:
                return {
                    "status": "error",
                    "message": "Summary does not contain sample data for visualization. Retrieve full data using cache_id."
                }
        
        if not data or 'results' not in data or not data['results']:
            return {
                "status": "error",
                "message": "No data available for visualization"
            }
        
        # Extract data
        columns = data.get('columns', [])
        results = data['results']
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(results, columns=columns)
        
        # Create figure
        plt.figure(figsize=(12, 8))
        
        # Generate chart based on type
        if chart_type == 'line':
            _create_line_chart(df, columns)
        elif chart_type == 'bar':
            _create_bar_chart(df, columns)
        elif chart_type == 'scatter':
            _create_scatter_chart(df, columns)
        elif chart_type == 'pie':
            _create_pie_chart(df, columns)
        else:
            return {
                "status": "error",
                "message": f"Unsupported chart type: {chart_type}"
            }
        
        # Add title and labels
        plt.title(title, fontsize=16, pad=20)
        if x_label:
            plt.xlabel(x_label, fontsize=12)
        if y_label:
            plt.ylabel(y_label, fontsize=12)
        
        # Improve layout
        plt.tight_layout()
        
        # Save to bytes
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        img_bytes = img_buffer.read()
        plt.close()
        
        # Save as artifact if tool_context provided
        artifact_name = f"chart_{chart_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        if tool_context:
            try:
                # Create artifact Part
                chart_artifact = types.Part.from_bytes(
                    data=img_bytes,
                    mime_type="image/png"
                )
                
                # Save artifact
                version = await tool_context.save_artifact(
                    filename=artifact_name,
                    artifact=chart_artifact
                )
                
                logger.info(f"Saved visualization '{artifact_name}' as version {version}")
                
                return {
                    "status": "success",
                    "artifact_name": artifact_name,
                    "artifact_version": version,
                    "chart_type": chart_type,
                    "data_points": len(results),
                    "message": f"Chart created and saved as {artifact_name}"
                }
                
            except Exception as e:
                logger.error(f"Failed to save artifact: {e}")
                # Fall through to base64 return
        
        # If no tool_context or artifact save failed, return base64
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        
        return {
            "status": "success",
            "chart_type": chart_type,
            "image_base64": img_base64,
            "data_points": len(results),
            "message": "Chart created successfully (base64 encoded)"
        }
        
    except Exception as e:
        logger.error(f"Visualization creation failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }

def _create_line_chart(df: pd.DataFrame, columns: List[str]):
    """Create a line chart from DataFrame."""
    # Assume first column is x-axis
    if len(columns) < 2:
        raise ValueError("Line chart requires at least 2 columns")
    
    x_col = columns[0]
    
    # Check if x-axis is timestamp
    if 'timestamp' in x_col.lower() or 'time' in x_col.lower():
        # Try to parse as datetime
        try:
            df[x_col] = pd.to_datetime(df[x_col])
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
            plt.gcf().autofmt_xdate()
        except:
            pass
    
    # Plot each numeric column
    for col in columns[1:]:
        try:
            # Convert to numeric, coercing errors to NaN
            numeric_data = pd.to_numeric(df[col], errors='coerce')
            if not numeric_data.isna().all():
                plt.plot(df[x_col], numeric_data, marker='o', label=col, linewidth=2)
        except:
            pass
    
    plt.legend()
    plt.grid(True, alpha=0.3)

def _create_bar_chart(df: pd.DataFrame, columns: List[str]):
    """Create a bar chart from DataFrame."""
    if len(columns) < 2:
        raise ValueError("Bar chart requires at least 2 columns")
    
    x_col = columns[0]
    
    # For multiple y columns, create grouped bars
    y_cols = []
    for col in columns[1:]:
        try:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            if not df[col].isna().all():
                y_cols.append(col)
        except:
            pass
    
    if not y_cols:
        raise ValueError("No numeric columns found for bar chart")
    
    if len(y_cols) == 1:
        plt.bar(df[x_col], df[y_cols[0]])
    else:
        # Grouped bar chart
        x = range(len(df))
        width = 0.8 / len(y_cols)
        
        for i, col in enumerate(y_cols):
            offset = (i - len(y_cols)/2) * width + width/2
            plt.bar([xi + offset for xi in x], df[col], width, label=col)
        
        plt.xticks(x, df[x_col], rotation=45, ha='right')
        plt.legend()
    
    plt.grid(True, axis='y', alpha=0.3)

def _create_scatter_chart(df: pd.DataFrame, columns: List[str]):
    """Create a scatter chart from DataFrame."""
    if len(columns) < 2:
        raise ValueError("Scatter chart requires at least 2 columns")
    
    x_col = columns[0]
    y_col = columns[1]
    
    # Convert to numeric
    df[x_col] = pd.to_numeric(df[x_col], errors='coerce')
    df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
    
    # Remove NaN values
    valid_data = df.dropna(subset=[x_col, y_col])
    
    # Create scatter plot
    plt.scatter(valid_data[x_col], valid_data[y_col], alpha=0.6, s=50)
    
    # Add trend line if enough points
    if len(valid_data) > 3:
        z = np.polyfit(valid_data[x_col], valid_data[y_col], 1)
        p = np.poly1d(z)
        plt.plot(valid_data[x_col], p(valid_data[x_col]), "r--", alpha=0.8, label='Trend')
        plt.legend()
    
    plt.grid(True, alpha=0.3)

def _create_pie_chart(df: pd.DataFrame, columns: List[str]):
    """Create a pie chart from DataFrame."""
    if len(columns) < 2:
        raise ValueError("Pie chart requires at least 2 columns")
    
    # First column is labels, second is values
    labels = df[columns[0]].tolist()
    
    # Find first numeric column for values
    values = None
    for col in columns[1:]:
        try:
            numeric_col = pd.to_numeric(df[col], errors='coerce')
            if not numeric_col.isna().all():
                values = numeric_col.tolist()
                break
        except:
            pass
    
    if values is None:
        raise ValueError("No numeric column found for pie chart")
    
    # Create pie chart
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
    plt.axis('equal')

def create_multi_chart_visualization(
    datasets: List[Dict[str, Any]],
    title: str,
    tool_context: Optional[ToolContext] = None
) -> Dict[str, Any]:
    """Create a multi-panel visualization with multiple datasets.
    
    Args:
        datasets: List of dataset configurations, each with:
            - data: Query results
            - chart_type: Type of chart
            - subplot_title: Title for subplot
        title: Overall figure title
        tool_context: Tool context for saving artifacts
        
    Returns:
        Dictionary with status and artifact information
    """
    try:
        num_charts = len(datasets)
        if num_charts == 0:
            return {
                "status": "error",
                "message": "No datasets provided"
            }
        
        # Calculate subplot layout
        cols = min(2, num_charts)
        rows = (num_charts + cols - 1) // cols
        
        # Create figure with subplots
        fig, axes = plt.subplots(rows, cols, figsize=(12 * cols, 8 * rows))
        if num_charts == 1:
            axes = [axes]
        else:
            axes = axes.flatten() if rows > 1 else axes
        
        # Create each subplot
        for i, dataset in enumerate(datasets):
            plt.subplot(rows, cols, i + 1)
            
            data = dataset.get('data', {})
            chart_type = dataset.get('chart_type', 'line')
            subplot_title = dataset.get('subplot_title', f'Chart {i+1}')
            
            if data and 'results' in data and data['results']:
                df = pd.DataFrame(data['results'], columns=data.get('columns', []))
                
                try:
                    if chart_type == 'line':
                        _create_line_chart(df, data['columns'])
                    elif chart_type == 'bar':
                        _create_bar_chart(df, data['columns'])
                    elif chart_type == 'scatter':
                        _create_scatter_chart(df, data['columns'])
                    elif chart_type == 'pie':
                        _create_pie_chart(df, data['columns'])
                except Exception as e:
                    plt.text(0.5, 0.5, f'Error: {str(e)}', 
                            ha='center', va='center', transform=plt.gca().transAxes)
            else:
                plt.text(0.5, 0.5, 'No data available', 
                        ha='center', va='center', transform=plt.gca().transAxes)
            
            plt.title(subplot_title, fontsize=14)
        
        # Hide any unused subplots
        for i in range(num_charts, len(axes)):
            axes[i].set_visible(False)
        
        # Add overall title
        fig.suptitle(title, fontsize=18, y=0.98)
        plt.tight_layout()
        
        # Save to bytes
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        img_bytes = img_buffer.read()
        plt.close()
        
        # Handle artifact saving (similar to single chart)
        artifact_name = f"multi_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        if tool_context:
            try:
                chart_artifact = types.Part.from_bytes(
                    data=img_bytes,
                    mime_type="image/png"
                )
                version = tool_context.save_artifact(
                    filename=artifact_name,
                    artifact=chart_artifact
                )
                
                return {
                    "status": "success",
                    "artifact_name": artifact_name,
                    "artifact_version": version,
                    "num_charts": num_charts,
                    "message": f"Multi-chart visualization created and saved as {artifact_name}"
                }
            except:
                pass
        
        # Fallback to base64
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        
        return {
            "status": "success",
            "num_charts": num_charts,
            "image_base64": img_base64,
            "message": "Multi-chart visualization created (base64 encoded)"
        }
        
    except Exception as e:
        logger.error(f"Multi-chart visualization failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }
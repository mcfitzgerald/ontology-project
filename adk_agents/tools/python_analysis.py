"""
Python execution tool for advanced analysis and visualization.
"""
import io
import base64
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, Optional
import asyncio
from google.adk.tools import FunctionTool

async def execute_python_analysis(
    code: str,
    data: Optional[Dict[str, Any]] = None,
    purpose: str = "analysis"
) -> Dict[str, Any]:
    """
    Execute Python code for data analysis and visualization.
    
    Args:
        code: Python code to execute
        data: Optional data dict (e.g., SPARQL results as DataFrame)
        purpose: Description of analysis purpose
    
    Returns:
        Dict with results, visualizations, and insights
    """
    # Create execution namespace
    namespace = {
        'pd': pd,
        'np': np,
        'plt': plt,
        'sns': sns,
        'data': data or {}
    }
    
    # Capture outputs
    results = {
        'success': True,
        'purpose': purpose,
        'outputs': [],
        'visualizations': [],
        'insights': []
    }
    
    try:
        # Redirect stdout to capture prints
        from contextlib import redirect_stdout
        stdout_capture = io.StringIO()
        
        with redirect_stdout(stdout_capture):
            # Execute code
            exec(code, namespace)
        
        # Capture text output
        text_output = stdout_capture.getvalue()
        if text_output:
            results['outputs'].append(text_output)
        
        # Check for matplotlib figures
        if plt.get_fignums():
            for fig_num in plt.get_fignums():
                fig = plt.figure(fig_num)
                
                # Save to base64
                buffer = io.BytesIO()
                fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
                buffer.seek(0)
                img_base64 = base64.b64encode(buffer.read()).decode()
                
                results['visualizations'].append({
                    'type': 'matplotlib',
                    'format': 'png',
                    'data': img_base64
                })
                
                plt.close(fig)
        
        # Extract any insights variable if defined
        if 'insights' in namespace:
            results['insights'] = namespace['insights']
        
        # Extract any metrics if defined
        if 'metrics' in namespace:
            results['metrics'] = namespace['metrics']
            
    except Exception as e:
        results['success'] = False
        results['error'] = str(e)
        results['error_type'] = type(e).__name__
    
    return results

# Create ADK tool
python_analysis_tool = FunctionTool(
    execute_python_analysis,
    description="Execute Python code for data analysis, statistical calculations, and visualization"
)
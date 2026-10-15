"""
CPU data preprocessing utilities for LSTM forecasting
"""

import numpy as np
import pandas as pd
from typing import Tuple


def prepare_input_sequence(cpu_values: list, lookback: int = 60) -> np.ndarray:
    """
    Prepare input sequence for LSTM prediction
    
    Args:
        cpu_values: List of CPU values (most recent lookback values)
        lookback: Number of past timesteps required
        
    Returns:
        Numpy array shaped for LSTM input [1, lookback, 1]
    """
    if len(cpu_values) < lookback:
        # Pad with the first value if not enough data
        padding = [cpu_values[0]] * (lookback - len(cpu_values))
        cpu_values = padding + cpu_values
    elif len(cpu_values) > lookback:
        # Use only the most recent values
        cpu_values = cpu_values[-lookback:]
    
    # Convert to numpy array and reshape
    sequence = np.array(cpu_values).reshape(1, lookback, 1)
    
    return sequence


def smooth_cpu_values(cpu_values: list, window_size: int = 5) -> list:
    """
    Apply moving average smoothing to CPU values
    
    Args:
        cpu_values: List of CPU values
        window_size: Window size for moving average
        
    Returns:
        Smoothed CPU values
    """
    if len(cpu_values) < window_size:
        return cpu_values
    
    df = pd.DataFrame({'cpu': cpu_values})
    smoothed = df['cpu'].rolling(window=window_size, min_periods=1).mean().tolist()
    
    return smoothed


def normalize_cpu_value(cpu_value: float) -> float:
    """
    Normalize CPU value to [0, 1] range
    
    Args:
        cpu_value: Raw CPU value
        
    Returns:
        Normalized CPU value
    """
    # Ensure value is between 0 and 1
    return max(0.0, min(1.0, cpu_value))


def denormalize_cpu_value(normalized_value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """
    Denormalize CPU value from [0, 1] range
    
    Args:
        normalized_value: Normalized value
        min_val: Minimum value in original scale
        max_val: Maximum value in original scale
        
    Returns:
        Denormalized CPU value
    """
    return normalized_value * (max_val - min_val) + min_val


def validate_cpu_prediction(prediction: float) -> float:
    """
    Validate and clip CPU prediction to valid range
    
    Args:
        prediction: Raw prediction value
        
    Returns:
        Validated CPU prediction
    """
    # Clip to [0, 1] for CPU usage percentage
    return max(0.0, min(1.0, prediction))

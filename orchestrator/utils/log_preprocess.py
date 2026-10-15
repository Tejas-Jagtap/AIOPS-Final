"""
Log preprocessing utilities for anomaly detection
"""

import re
from typing import List


def clean_log_text(log_text: str) -> str:
    """
    Clean and normalize log text
    
    Args:
        log_text: Raw log text
        
    Returns:
        Cleaned log text
    """
    # Remove timestamps
    log_text = re.sub(r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}[\.,]?\d*', '', log_text)
    
    # Remove IP addresses
    log_text = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', '', log_text)
    
    # Remove URLs
    log_text = re.sub(r'https?://[^\s]+', '', log_text)
    
    # Remove file paths
    log_text = re.sub(r'[A-Za-z]:\\[^\s]+', '', log_text)
    log_text = re.sub(r'/[^\s]+\.[a-z]{2,4}', '', log_text)
    
    # Remove numbers (but keep error codes)
    log_text = re.sub(r'\b\d{5,}\b', '', log_text)
    
    # Remove excessive whitespace
    log_text = re.sub(r'\s+', ' ', log_text)
    
    # Trim
    log_text = log_text.strip()
    
    return log_text


def extract_log_features(log_text: str) -> dict:
    """
    Extract statistical features from log text
    
    Args:
        log_text: Log text
        
    Returns:
        Dictionary of features
    """
    features = {
        'length': len(log_text),
        'lines': log_text.count('\n') + 1,
        'error_count': log_text.lower().count('error'),
        'warning_count': log_text.lower().count('warning'),
        'exception_count': log_text.lower().count('exception'),
        'failure_count': log_text.lower().count('failure'),
        'success_count': log_text.lower().count('success'),
    }
    
    return features


def truncate_log(log_text: str, max_lines: int = 10000) -> str:
    """
    Truncate log to maximum number of lines
    
    Args:
        log_text: Log text
        max_lines: Maximum number of lines
        
    Returns:
        Truncated log text
    """
    lines = log_text.split('\n')
    
    if len(lines) <= max_lines:
        return log_text
    
    # Keep first half and last half
    half = max_lines // 2
    truncated_lines = lines[:half] + ['... truncated ...'] + lines[-half:]
    
    return '\n'.join(truncated_lines)


def preprocess_log(log_text: str, max_lines: int = 10000) -> str:
    """
    Complete preprocessing pipeline for logs
    
    Args:
        log_text: Raw log text
        max_lines: Maximum number of lines
        
    Returns:
        Preprocessed log text
    """
    # Truncate if too long
    log_text = truncate_log(log_text, max_lines)
    
    # Clean
    log_text = clean_log_text(log_text)
    
    return log_text

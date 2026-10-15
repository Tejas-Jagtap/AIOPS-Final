"""
Router package initialization
"""

from . import failure_router
from . import anomaly_router
from . import forecast_router
from . import autoscale_router

__all__ = ['failure_router', 'anomaly_router', 'forecast_router', 'autoscale_router']

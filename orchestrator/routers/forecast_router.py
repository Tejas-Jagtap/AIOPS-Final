"""
FastAPI router for CPU forecasting
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import joblib
import numpy as np
import torch
import torch.nn as nn
from typing import List, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.cpu_preprocess import prepare_input_sequence, validate_cpu_prediction
from utils.prometheus_client import create_prometheus_client


class LSTMModel(nn.Module):
    """LSTM model (must match training architecture)"""
    
    def __init__(self, input_size=1, hidden_size_1=128, hidden_size_2=64, dense_size=32):
        super().__init__()
        self.lstm1 = nn.LSTM(input_size, hidden_size_1, batch_first=True)
        self.dropout1 = nn.Dropout(0.2)
        self.lstm2 = nn.LSTM(hidden_size_1, hidden_size_2, batch_first=True)
        self.dropout2 = nn.Dropout(0.2)
        self.fc1 = nn.Linear(hidden_size_2, dense_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(dense_size, 1)
    
    def forward(self, x):
        out, _ = self.lstm1(x)
        out = self.dropout1(out)
        out, _ = self.lstm2(out)
        out = self.dropout2(out[:, -1, :])
        out = self.relu(self.fc1(out))
        out = self.fc2(out)
        return out


router = APIRouter(prefix="/forecast_cpu", tags=["CPU Forecasting"])

# Global model variables (loaded at startup)
lstm_model = None
cpu_scaler = None
prometheus_client = None


class CPUForecastRequest(BaseModel):
    """Request model for CPU forecasting"""
    cpu_history: Optional[List[float]] = Field(
        None, 
        description="Historical CPU values (optional, will query Prometheus if not provided)"
    )
    namespace: str = Field("default", description="Kubernetes namespace")


class CPUForecastResponse(BaseModel):
    """Response model for CPU forecasting"""
    predicted_cpu: float = Field(..., description="Predicted CPU usage (0.0-1.0)")


def load_forecast_models(
    lstm_path: str = "orchestrator/models/lstm_cpu.pth",
    scaler_path: str = "orchestrator/models/cpu_scaler.pkl",
    prometheus_url: Optional[str] = None
):
    """
    Load CPU forecasting models
    """
    global lstm_model, cpu_scaler, prometheus_client
    
    try:
        # Load LSTM model (PyTorch)
        checkpoint = torch.load(lstm_path, map_location='cpu', weights_only=False)
        lstm_model = LSTMModel()
        lstm_model.load_state_dict(checkpoint['model_state_dict'])
        lstm_model.eval()
        print(f"LSTM model loaded from {lstm_path}")
        
        # Load scaler
        cpu_scaler = joblib.load(scaler_path)
        print(f"CPU scaler loaded from {scaler_path}")
        
        # Initialize Prometheus client if URL provided
        if prometheus_url:
            prometheus_client = create_prometheus_client(prometheus_url)
            print(f"Prometheus client initialized with URL: {prometheus_url}")
        
    except Exception as e:
        print(f"Error loading CPU forecasting models: {e}")
        raise


@router.post("", response_model=CPUForecastResponse)
async def forecast_cpu(request: CPUForecastRequest):
    """
    Forecast CPU usage
    
    Args:
        request: CPU history or namespace
        
    Returns:
        Predicted CPU usage
    """
    if lstm_model is None or cpu_scaler is None:
        raise HTTPException(status_code=500, detail="Models not loaded")
    
    try:
        # Get CPU history
        if request.cpu_history:
            cpu_values = request.cpu_history
        elif prometheus_client:
            # Query Prometheus for historical CPU
            cpu_values = prometheus_client.get_historical_cpu_usage(
                namespace=request.namespace,
                minutes=60,
                step='1m'
            )
            if not cpu_values:
                raise HTTPException(
                    status_code=400,
                    detail="No CPU history available from Prometheus"
                )
        else:
            raise HTTPException(
                status_code=400,
                detail="Either cpu_history must be provided or Prometheus must be configured"
            )
        
        # Prepare input sequence (lookback=60)
        sequence = prepare_input_sequence(cpu_values, lookback=60)
        
        # Scale input
        sequence_scaled = cpu_scaler.transform(sequence.reshape(-1, 1)).reshape(1, 60, 1)
        
        # Predict (PyTorch)
        with torch.no_grad():
            x_tensor = torch.FloatTensor(sequence_scaled)
            prediction_scaled = lstm_model(x_tensor).numpy()
        
        # Inverse transform
        prediction = cpu_scaler.inverse_transform(prediction_scaled.reshape(-1, 1))[0][0]
        
        # Validate and clip to valid range
        prediction = validate_cpu_prediction(float(prediction))
        
        return CPUForecastResponse(predicted_cpu=prediction)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecasting error: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    prometheus_healthy = prometheus_client.health_check() if prometheus_client else None
    
    return {
        "status": "healthy",
        "lstm_loaded": lstm_model is not None,
        "scaler_loaded": cpu_scaler is not None,
        "prometheus_configured": prometheus_client is not None,
        "prometheus_healthy": prometheus_healthy
    }

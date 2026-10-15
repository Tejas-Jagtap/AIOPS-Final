"""
FastAPI router for log anomaly detection
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import joblib
import numpy as np
import torch
import torch.nn as nn
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.log_preprocess import preprocess_log


class Autoencoder(nn.Module):
    """Autoencoder model (must match training architecture)"""
    
    def __init__(self, input_dim: int, encoding_dim: int = 32):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.BatchNorm1d(128),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.BatchNorm1d(64),
            nn.Dropout(0.3),
            nn.Linear(64, encoding_dim),
            nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, 64),
            nn.ReLU(),
            nn.BatchNorm1d(64),
            nn.Dropout(0.3),
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.BatchNorm1d(128),
            nn.Dropout(0.3),
            nn.Linear(128, input_dim),
            nn.Sigmoid(),
        )
    
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded


router = APIRouter(prefix="/detect_anomaly", tags=["Anomaly Detection"])

# Global model variables (loaded at startup)
tfidf_vectorizer = None
autoencoder_model = None
anomaly_threshold = None


class AnomalyDetectionRequest(BaseModel):
    """Request model for anomaly detection"""
    log: str = Field(..., description="Console log text")


class AnomalyDetectionResponse(BaseModel):
    """Response model for anomaly detection"""
    anomaly_score: float = Field(..., description="Anomaly score (reconstruction error)")
    is_anomaly: bool = Field(..., description="Whether the log is classified as anomalous")


def load_anomaly_models(
    tfidf_path: str = "orchestrator/models/tfidf.pkl",
    autoencoder_path: str = "orchestrator/models/autoencoder.pth",
    threshold_path: str = "orchestrator/models/anomaly_threshold.pkl"
):
    """
    Load anomaly detection models
    """
    global tfidf_vectorizer, autoencoder_model, anomaly_threshold
    
    try:
        # Load TF-IDF vectorizer
        tfidf_vectorizer = joblib.load(tfidf_path)
        print(f"TF-IDF vectorizer loaded from {tfidf_path}")
        
        # Load autoencoder (PyTorch)
        checkpoint = torch.load(autoencoder_path, map_location='cpu', weights_only=False)
        input_dim = checkpoint['input_dim']
        encoding_dim = checkpoint['encoding_dim']
        autoencoder_model = Autoencoder(input_dim, encoding_dim)
        autoencoder_model.load_state_dict(checkpoint['model_state_dict'])
        autoencoder_model.eval()
        print(f"Autoencoder model loaded from {autoencoder_path}")
        
        # Load threshold
        threshold_data = joblib.load(threshold_path)
        anomaly_threshold = threshold_data['threshold']
        print(f"Anomaly threshold loaded: {anomaly_threshold}")
        
    except Exception as e:
        print(f"Error loading anomaly detection models: {e}")
        raise


@router.post("", response_model=AnomalyDetectionResponse)
async def detect_anomaly(request: AnomalyDetectionRequest):
    """
    Detect anomalies in console logs
    
    Args:
        request: Log text
        
    Returns:
        Anomaly score and classification
    """
    if tfidf_vectorizer is None or autoencoder_model is None or anomaly_threshold is None:
        raise HTTPException(status_code=500, detail="Models not loaded")
    
    try:
        # Preprocess log
        cleaned_log = preprocess_log(request.log)
        
        # Transform with TF-IDF
        tfidf_features = tfidf_vectorizer.transform([cleaned_log]).toarray()
        
        # Get reconstruction from autoencoder (PyTorch)
        with torch.no_grad():
            x_tensor = torch.FloatTensor(tfidf_features)
            reconstruction = autoencoder_model(x_tensor).numpy()
        
        # Calculate reconstruction error (anomaly score)
        mse = np.mean(np.power(tfidf_features - reconstruction, 2), axis=1)
        anomaly_score = float(mse[0])
        
        # Classify as anomaly if score exceeds threshold
        is_anomaly = anomaly_score > anomaly_threshold
        
        return AnomalyDetectionResponse(
            anomaly_score=anomaly_score,
            is_anomaly=is_anomaly
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection error: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "tfidf_loaded": tfidf_vectorizer is not None,
        "autoencoder_loaded": autoencoder_model is not None,
        "threshold_loaded": anomaly_threshold is not None,
        "threshold_value": float(anomaly_threshold) if anomaly_threshold is not None else None
    }

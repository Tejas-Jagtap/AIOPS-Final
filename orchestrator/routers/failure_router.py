"""
FastAPI router for CI/CD failure prediction
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import joblib
import numpy as np
from typing import Optional


router = APIRouter(prefix="/predict_failure", tags=["Failure Prediction"])

# Global model variable (loaded at startup)
failure_model = None


class FailurePredictionRequest(BaseModel):
    """Request model for failure prediction"""
    duration: float = Field(..., description="Build duration in seconds", ge=0)
    warnings: int = Field(..., description="Number of warnings in build", ge=0)
    errors: int = Field(..., description="Number of errors in build", ge=0)
    failures: int = Field(0, description="Number of build step failures", ge=0)
    log_length: int = Field(0, description="Length of console log in characters", ge=0)
    tests_failed: int = Field(0, description="Number of failed tests", ge=0)
    tests_passed: int = Field(0, description="Number of passed tests", ge=0)


class FailurePredictionResponse(BaseModel):
    """Response model for failure prediction"""
    failure_probability: float = Field(..., description="Probability of build failure (0.0-1.0)")


def load_failure_model(model_path: str = "orchestrator/models/xgboost_failure.bin"):
    """
    Load the failure prediction model
    
    Args:
        model_path: Path to the model file
    """
    global failure_model
    try:
        failure_model = joblib.load(model_path)
        print(f"Failure prediction model loaded from {model_path}")
    except Exception as e:
        print(f"Error loading failure prediction model: {e}")
        raise


@router.post("", response_model=FailurePredictionResponse)
async def predict_failure(request: FailurePredictionRequest):
    """
    Predict CI/CD build failure probability
    
    Args:
        request: Build metadata
        
    Returns:
        Failure probability
    """
    if failure_model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    try:
        # Prepare features (must match training feature order)
        features = np.array([[
            request.duration,
            request.warnings,
            request.errors,
            request.failures,
            request.log_length,
            request.tests_failed,
            request.tests_passed,
            request.tests_failed + request.tests_passed  # tests_total
        ]])
        
        # Predict probability
        probability = failure_model.predict_proba(features)[0][1]
        
        return FailurePredictionResponse(failure_probability=float(probability))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": failure_model is not None
    }

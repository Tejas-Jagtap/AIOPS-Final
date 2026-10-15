"""
FastAPI router for predictive autoscaling
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import autoscaler components
autoscaler_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'autoscaler')
sys.path.append(autoscaler_path)

router = APIRouter(prefix="/autoscale", tags=["Autoscaling"])

# Global autoscaler (initialized at startup)
predictive_scaler = None


class AutoscaleRequest(BaseModel):
    """Request model for autoscaling"""
    deployment_name: str = Field(..., description="Name of the Kubernetes deployment")
    namespace: str = Field("default", description="Kubernetes namespace")
    predicted_cpu: Optional[float] = Field(None, description="Predicted CPU usage (0.0-1.0)")
    anomaly_score: Optional[float] = Field(None, description="Current anomaly score")
    failure_probability: Optional[float] = Field(None, description="Current failure probability")


class AutoscaleResponse(BaseModel):
    """Response model for autoscaling"""
    action: str = Field(..., description="Scaling action taken (scale_up, scale_down, no_action)")
    current_replicas: int = Field(..., description="Current number of replicas")
    new_replicas: int = Field(..., description="New number of replicas after scaling")
    reason: str = Field(..., description="Reason for the scaling decision")


def initialize_autoscaler(k8s_client, prometheus_client):
    """
    Initialize the predictive autoscaler
    
    Args:
        k8s_client: Kubernetes client
        prometheus_client: Prometheus client
    """
    global predictive_scaler
    
    try:
        from scaler import PredictiveScaler
        
        predictive_scaler = PredictiveScaler(
            k8s_client=k8s_client,
            prometheus_client=prometheus_client
        )
        print("Predictive autoscaler initialized")
    except Exception as e:
        print(f"Error initializing autoscaler: {e}")
        raise


@router.post("", response_model=AutoscaleResponse)
async def autoscale(request: AutoscaleRequest):
    """
    Perform predictive autoscaling
    
    Args:
        request: Autoscaling parameters
        
    Returns:
        Scaling action and results
    """
    if predictive_scaler is None:
        raise HTTPException(
            status_code=503,
            detail="Autoscaler not available. Kubernetes cluster not connected. "
                   "Start Minikube and restart the orchestrator."
        )
    
    try:
        # Perform autoscaling decision
        result = predictive_scaler.scale(
            deployment_name=request.deployment_name,
            namespace=request.namespace,
            predicted_cpu=request.predicted_cpu,
            anomaly_score=request.anomaly_score,
            failure_probability=request.failure_probability
        )
        
        return AutoscaleResponse(
            action=result['action'],
            current_replicas=result['current_replicas'],
            new_replicas=result['new_replicas'],
            reason=result['reason']
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Autoscaling error: {str(e)}")


@router.get("/status/{deployment_name}")
async def get_autoscaler_status(deployment_name: str, namespace: str = "default"):
    """
    Get autoscaler status for a deployment
    
    Args:
        deployment_name: Deployment name
        namespace: Namespace
        
    Returns:
        Autoscaler status
    """
    if predictive_scaler is None:
        raise HTTPException(status_code=500, detail="Autoscaler not initialized")
    
    try:
        status = predictive_scaler.get_status(deployment_name, namespace)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "autoscaler_initialized": predictive_scaler is not None
    }

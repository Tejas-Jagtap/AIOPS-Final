"""
AIOps Orchestrator - Main FastAPI Application
"""

import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Ensure project root is on the path so model paths resolve correctly
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import routers
from routers import failure_router, anomaly_router, forecast_router, autoscale_router

# Import utilities
from utils.k8s_client import create_k8s_client
from utils.prometheus_client import create_prometheus_client


# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup: Load all ML models
    print("=" * 60)
    print("AIOps Orchestrator - Starting Up")
    print("=" * 60)
    
    try:
        # Load failure prediction model
        print("\n[1/5] Loading failure prediction model...")
        failure_router.load_failure_model()
        
        # Load anomaly detection models
        print("\n[2/5] Loading anomaly detection models...")
        anomaly_router.load_anomaly_models()
        
        # Load CPU forecasting models
        print("\n[3/5] Loading CPU forecasting models...")
        prometheus_url = os.getenv('PROMETHEUS_URL', 'http://localhost:9090')
        forecast_router.load_forecast_models(prometheus_url=prometheus_url)
        
        # Initialize Kubernetes client (optional — may not be available)
        print("\n[4/5] Initializing Kubernetes client...")
        try:
            in_cluster = os.getenv('K8S_IN_CLUSTER', 'false').lower() == 'true'
            kubeconfig_path = os.getenv('KUBECONFIG', None)
            k8s_client = create_k8s_client(in_cluster=in_cluster, kubeconfig_path=kubeconfig_path)
            
            # Initialize autoscaler
            print("\n[5/5] Initializing predictive autoscaler...")
            prom_client = create_prometheus_client(prometheus_url)
            autoscale_router.initialize_autoscaler(k8s_client, prom_client)
        except Exception as k8s_err:
            print(f"\n[WARNING] Kubernetes/Autoscaler not available: {k8s_err}")
            print("  → Autoscale endpoint will return 503. Other endpoints work fine.")
        
        print("\n" + "=" * 60)
        print("AIOps Orchestrator - Ready!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nERROR during startup: {e}")
        raise
    
    yield
    
    # Shutdown
    print("\nAIOps Orchestrator - Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="AIOps Orchestrator",
    description="Predictive AIOps system for CI/CD failure prediction, log anomaly detection, CPU forecasting, and autoscaling",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(failure_router.router)
app.include_router(anomaly_router.router)
app.include_router(forecast_router.router)
app.include_router(autoscale_router.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AIOps Orchestrator",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "failure_prediction": "/predict_failure",
            "anomaly_detection": "/detect_anomaly",
            "cpu_forecasting": "/forecast_cpu",
            "autoscaling": "/autoscale",
            "documentation": "/docs"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AIOps Orchestrator"
    }


@app.get("/info")
async def info():
    """Service information"""
    return {
        "service": "AIOps Orchestrator",
        "version": "1.0.0",
        "description": "Predictive AIOps system combining ML models for intelligent operations",
        "capabilities": [
            "CI/CD build failure prediction (XGBoost)",
            "Console log anomaly detection (TF-IDF + Autoencoder)",
            "CPU workload forecasting (LSTM)",
            "Predictive Kubernetes autoscaling"
        ],
        "models": {
            "failure_prediction": {
                "algorithm": "XGBoost",
                "input": ["duration", "warnings", "errors", "tests_failed", "tests_passed"],
                "output": "failure_probability"
            },
            "anomaly_detection": {
                "algorithm": "TF-IDF + Autoencoder",
                "input": ["log"],
                "output": ["anomaly_score", "is_anomaly"]
            },
            "cpu_forecasting": {
                "algorithm": "LSTM",
                "input": ["cpu_history"],
                "output": "predicted_cpu"
            },
            "autoscaling": {
                "algorithm": "Rule-based decision engine",
                "inputs": ["predicted_cpu", "anomaly_score", "failure_probability"],
                "output": ["action", "current_replicas", "new_replicas"]
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("ORCHESTRATOR_HOST", "0.0.0.0")
    port = int(os.getenv("ORCHESTRATOR_PORT", "8000"))
    
    # Run server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )

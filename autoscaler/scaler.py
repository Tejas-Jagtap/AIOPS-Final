"""
Predictive autoscaler implementation
"""

import os
from typing import Dict, Any, Optional
from decision_engine import DecisionEngine


class PredictiveScaler:
    """
    Predictive autoscaler that uses ML predictions to scale Kubernetes deployments
    """
    
    def __init__(
        self,
        k8s_client,
        prometheus_client,
        cpu_threshold_high: float = 0.7,
        cpu_threshold_low: float = 0.3,
        anomaly_threshold: float = 0.5,
        failure_threshold: float = 0.6,
        min_replicas: int = 1,
        max_replicas: int = 10,
        scale_up_increment: int = 2,
        scale_down_decrement: int = 1,
        cooldown_seconds: int = 300
    ):
        """
        Initialize predictive autoscaler
        
        Args:
            k8s_client: Kubernetes client instance
            prometheus_client: Prometheus client instance
            cpu_threshold_high: CPU threshold for scale up
            cpu_threshold_low: CPU threshold for scale down
            anomaly_threshold: Anomaly score threshold
            failure_threshold: Failure probability threshold
            min_replicas: Minimum replicas
            max_replicas: Maximum replicas
            scale_up_increment: Scale up increment
            scale_down_decrement: Scale down decrement
            cooldown_seconds: Cooldown period
        """
        self.k8s_client = k8s_client
        self.prometheus_client = prometheus_client
        
        # Initialize decision engine
        self.decision_engine = DecisionEngine(
            cpu_threshold_high=cpu_threshold_high,
            cpu_threshold_low=cpu_threshold_low,
            anomaly_threshold=anomaly_threshold,
            failure_threshold=failure_threshold,
            min_replicas=min_replicas,
            max_replicas=max_replicas,
            scale_up_increment=scale_up_increment,
            scale_down_decrement=scale_down_decrement,
            cooldown_seconds=cooldown_seconds
        )
        
        print(f"PredictiveScaler initialized with:")
        print(f"  CPU thresholds: {cpu_threshold_low:.2f} - {cpu_threshold_high:.2f}")
        print(f"  Replica range: {min_replicas} - {max_replicas}")
        print(f"  Cooldown: {cooldown_seconds}s")
    
    def scale(
        self,
        deployment_name: str,
        namespace: str = 'default',
        predicted_cpu: Optional[float] = None,
        anomaly_score: Optional[float] = None,
        failure_probability: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Perform predictive autoscaling
        
        Args:
            deployment_name: Name of deployment
            namespace: Kubernetes namespace
            predicted_cpu: Predicted CPU usage
            anomaly_score: Anomaly score
            failure_probability: Failure probability
            
        Returns:
            Dictionary with scaling results
        """
        # Get current replica count
        current_replicas = self.k8s_client.get_deployment_replicas(deployment_name, namespace)
        
        if current_replicas == 0:
            return {
                'action': 'error',
                'current_replicas': 0,
                'new_replicas': 0,
                'reason': f"Deployment {deployment_name} not found in namespace {namespace}"
            }
        
        # Make scaling decision
        deployment_key = f"{namespace}/{deployment_name}"
        decision = self.decision_engine.make_decision(
            deployment_key=deployment_key,
            current_replicas=current_replicas,
            predicted_cpu=predicted_cpu,
            anomaly_score=anomaly_score,
            failure_probability=failure_probability
        )
        
        # Apply scaling if needed
        if decision['action'] == 'scale_up' or decision['action'] == 'scale_down':
            success = self.k8s_client.scale_deployment(
                name=deployment_name,
                replicas=decision['target_replicas'],
                namespace=namespace
            )
            
            if success:
                new_replicas = decision['target_replicas']
            else:
                decision['action'] = 'error'
                new_replicas = current_replicas
                decision['reasons'].append("Failed to scale deployment")
        else:
            new_replicas = current_replicas
        
        # Prepare response
        response = {
            'action': decision['action'],
            'current_replicas': current_replicas,
            'new_replicas': new_replicas,
            'reason': '; '.join(decision['reasons']),
            'deployment_name': deployment_name,
            'namespace': namespace
        }
        
        # Add metrics to response
        if predicted_cpu is not None:
            response['predicted_cpu'] = predicted_cpu
        if anomaly_score is not None:
            response['anomaly_score'] = anomaly_score
        if failure_probability is not None:
            response['failure_probability'] = failure_probability
        
        return response
    
    def get_status(self, deployment_name: str, namespace: str = 'default') -> Dict[str, Any]:
        """
        Get current status of a deployment
        
        Args:
            deployment_name: Name of deployment
            namespace: Kubernetes namespace
            
        Returns:
            Dictionary with deployment status
        """
        # Get deployment status
        status = self.k8s_client.get_deployment_status(deployment_name, namespace)
        
        if not status:
            return {
                'error': f"Deployment {deployment_name} not found in namespace {namespace}"
            }
        
        # Get current CPU usage from Prometheus
        current_cpu = None
        if self.prometheus_client:
            try:
                current_cpu = self.prometheus_client.get_current_cpu_usage(namespace=namespace)
            except Exception as e:
                print(f"Error getting CPU usage: {e}")
        
        # Add CPU to status
        if current_cpu is not None:
            status['current_cpu'] = current_cpu
        
        # Check cooldown status
        deployment_key = f"{namespace}/{deployment_name}"
        in_cooldown = self.decision_engine.is_in_cooldown(deployment_key)
        status['in_cooldown'] = in_cooldown
        
        if in_cooldown:
            from datetime import datetime
            last_scale_time = self.decision_engine.last_scale_time[deployment_key]
            cooldown_remaining = self.decision_engine.cooldown_seconds - (
                datetime.now() - last_scale_time
            ).total_seconds()
            status['cooldown_remaining_seconds'] = max(0, int(cooldown_remaining))
        
        return status


def create_predictive_scaler(k8s_client, prometheus_client) -> PredictiveScaler:
    """
    Factory function to create predictive scaler with environment configuration
    
    Args:
        k8s_client: Kubernetes client
        prometheus_client: Prometheus client
        
    Returns:
        PredictiveScaler instance
    """
    return PredictiveScaler(
        k8s_client=k8s_client,
        prometheus_client=prometheus_client,
        cpu_threshold_high=float(os.getenv('AUTOSCALER_CPU_HIGH', '0.7')),
        cpu_threshold_low=float(os.getenv('AUTOSCALER_CPU_LOW', '0.3')),
        anomaly_threshold=float(os.getenv('AUTOSCALER_ANOMALY_THRESHOLD', '0.5')),
        failure_threshold=float(os.getenv('AUTOSCALER_FAILURE_THRESHOLD', '0.6')),
        min_replicas=int(os.getenv('AUTOSCALER_MIN_REPLICAS', '1')),
        max_replicas=int(os.getenv('AUTOSCALER_MAX_REPLICAS', '10')),
        scale_up_increment=int(os.getenv('AUTOSCALER_SCALE_UP_INCREMENT', '2')),
        scale_down_decrement=int(os.getenv('AUTOSCALER_SCALE_DOWN_DECREMENT', '1')),
        cooldown_seconds=int(os.getenv('AUTOSCALER_COOLDOWN_SECONDS', '300'))
    )

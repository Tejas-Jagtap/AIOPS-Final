"""
Predictive autoscaling decision engine
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class DecisionEngine:
    """
    Decision engine for predictive autoscaling
    Evaluates CPU forecasts, anomaly scores, and failure probabilities
    """
    
    def __init__(
        self,
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
        Initialize decision engine
        
        Args:
            cpu_threshold_high: CPU threshold for scale up (0.0-1.0)
            cpu_threshold_low: CPU threshold for scale down (0.0-1.0)
            anomaly_threshold: Anomaly score threshold
            failure_threshold: Failure probability threshold
            min_replicas: Minimum number of replicas
            max_replicas: Maximum number of replicas
            scale_up_increment: Number of replicas to add when scaling up
            scale_down_decrement: Number of replicas to remove when scaling down
            cooldown_seconds: Cooldown period between scaling operations
        """
        self.cpu_threshold_high = cpu_threshold_high
        self.cpu_threshold_low = cpu_threshold_low
        self.anomaly_threshold = anomaly_threshold
        self.failure_threshold = failure_threshold
        self.min_replicas = min_replicas
        self.max_replicas = max_replicas
        self.scale_up_increment = scale_up_increment
        self.scale_down_decrement = scale_down_decrement
        self.cooldown_seconds = cooldown_seconds
        
        # Track last scaling actions
        self.last_scale_time: Dict[str, datetime] = {}
    
    def is_in_cooldown(self, deployment_key: str) -> bool:
        """
        Check if deployment is in cooldown period
        
        Args:
            deployment_key: Unique key for deployment (namespace/name)
            
        Returns:
            True if in cooldown, False otherwise
        """
        if deployment_key not in self.last_scale_time:
            return False
        
        elapsed = (datetime.now() - self.last_scale_time[deployment_key]).total_seconds()
        return elapsed < self.cooldown_seconds
    
    def update_last_scale_time(self, deployment_key: str):
        """
        Update last scale time for a deployment
        
        Args:
            deployment_key: Unique key for deployment
        """
        self.last_scale_time[deployment_key] = datetime.now()
    
    def calculate_target_replicas(
        self,
        current_replicas: int,
        predicted_cpu: Optional[float] = None,
        anomaly_score: Optional[float] = None,
        failure_probability: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate target replica count using priority-based decision policy.

        Priority order (matches Algorithm 1 in the paper):
          1. If anomaly detected  → trigger alert (non-blocking)
          2. If high failure prob → HOLD (avoid scaling for likely-failing builds)
          3. If high predicted CPU → Scale Up
          4. If low predicted CPU  → Scale Down (with cooldown check)
          5. Otherwise             → Maintain

        Args:
            current_replicas: Current number of replicas
            predicted_cpu: Predicted CPU usage (0.0-1.0)
            anomaly_score: Anomaly score
            failure_probability: Failure probability (0.0-1.0)

        Returns:
            Dictionary with scaling decision
        """
        reasons = []
        alert = False

        # Step 1: Check for log anomaly — trigger alert (non-blocking)
        if anomaly_score is not None and anomaly_score > self.anomaly_threshold:
            alert = True
            reasons.append(f"Log anomaly detected (score={anomaly_score:.2f})")

        # Step 2: If failure probability is high → HOLD (skip scaling)
        if failure_probability is not None and failure_probability > self.failure_threshold:
            reasons.append(
                f"High failure probability ({failure_probability:.2f}) — holding to avoid scaling for failing build"
            )
            return {
                'action': 'no_action',
                'target_replicas': current_replicas,
                'current_replicas': current_replicas,
                'reasons': reasons,
                'predicted_cpu': predicted_cpu,
                'anomaly_score': anomaly_score,
                'failure_probability': failure_probability,
                'alert': alert,
            }

        # Step 3: Evaluate predicted CPU for scaling
        if predicted_cpu is not None:
            if predicted_cpu >= self.cpu_threshold_high and current_replicas < self.max_replicas:
                target_replicas = min(
                    current_replicas + self.scale_up_increment,
                    self.max_replicas,
                )
                reasons.append(f"High predicted CPU ({predicted_cpu:.2f}) — scaling up")
                return {
                    'action': 'scale_up',
                    'target_replicas': target_replicas,
                    'current_replicas': current_replicas,
                    'reasons': reasons,
                    'predicted_cpu': predicted_cpu,
                    'anomaly_score': anomaly_score,
                    'failure_probability': failure_probability,
                    'alert': alert,
                }

            if predicted_cpu <= self.cpu_threshold_low and current_replicas > self.min_replicas:
                target_replicas = max(
                    current_replicas - self.scale_down_decrement,
                    self.min_replicas,
                )
                reasons.append(f"Low predicted CPU ({predicted_cpu:.2f}) — scaling down")
                return {
                    'action': 'scale_down',
                    'target_replicas': target_replicas,
                    'current_replicas': current_replicas,
                    'reasons': reasons,
                    'predicted_cpu': predicted_cpu,
                    'anomaly_score': anomaly_score,
                    'failure_probability': failure_probability,
                    'alert': alert,
                }

        # Step 5: No action needed
        if not reasons:
            reasons.append("All metrics within normal range")

        return {
            'action': 'no_action',
            'target_replicas': current_replicas,
            'current_replicas': current_replicas,
            'reasons': reasons,
            'predicted_cpu': predicted_cpu,
            'anomaly_score': anomaly_score,
            'failure_probability': failure_probability,
            'alert': alert,
        }
    
    def make_decision(
        self,
        deployment_key: str,
        current_replicas: int,
        predicted_cpu: Optional[float] = None,
        anomaly_score: Optional[float] = None,
        failure_probability: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Make scaling decision with cooldown check
        
        Args:
            deployment_key: Unique key for deployment
            current_replicas: Current number of replicas
            predicted_cpu: Predicted CPU usage
            anomaly_score: Anomaly score
            failure_probability: Failure probability
            
        Returns:
            Dictionary with scaling decision
        """
        # Check cooldown
        if self.is_in_cooldown(deployment_key):
            cooldown_remaining = self.cooldown_seconds - (
                datetime.now() - self.last_scale_time[deployment_key]
            ).total_seconds()
            
            return {
                'action': 'no_action',
                'target_replicas': current_replicas,
                'current_replicas': current_replicas,
                'reasons': [f"In cooldown period ({cooldown_remaining:.0f}s remaining)"],
                'predicted_cpu': predicted_cpu,
                'anomaly_score': anomaly_score,
                'failure_probability': failure_probability
            }
        
        # Calculate target replicas
        decision = self.calculate_target_replicas(
            current_replicas=current_replicas,
            predicted_cpu=predicted_cpu,
            anomaly_score=anomaly_score,
            failure_probability=failure_probability
        )
        
        # Update cooldown if action is taken
        if decision['action'] != 'no_action':
            self.update_last_scale_time(deployment_key)
        
        return decision

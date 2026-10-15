"""
Prometheus client for querying metrics at runtime
"""

import requests
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta


class PrometheusClient:
    """Client for querying Prometheus at runtime"""
    
    def __init__(self, prometheus_url: str):
        """
        Initialize Prometheus client
        
        Args:
            prometheus_url: Base URL of Prometheus instance
        """
        self.prometheus_url = prometheus_url.rstrip('/')
        self.api_url = f"{self.prometheus_url}/api/v1"
        self.session = requests.Session()
    
    def query(self, query: str, time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Execute instant query
        
        Args:
            query: PromQL query
            time: Evaluation timestamp (default: now)
            
        Returns:
            Query result
        """
        try:
            url = f"{self.api_url}/query"
            params = {'query': query}
            
            if time:
                params['time'] = time.timestamp()
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error executing query: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def query_range(self, query: str, start: datetime, end: datetime, step: str = '1m') -> Dict[str, Any]:
        """
        Execute range query
        
        Args:
            query: PromQL query
            start: Start time
            end: End time
            step: Query resolution
            
        Returns:
            Query result
        """
        try:
            url = f"{self.api_url}/query_range"
            params = {
                'query': query,
                'start': start.timestamp(),
                'end': end.timestamp(),
                'step': step
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error executing range query: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def get_current_cpu_usage(self, namespace: str = 'default', pod_name: Optional[str] = None) -> float:
        """
        Get current CPU usage
        
        Args:
            namespace: Kubernetes namespace
            pod_name: Specific pod name (optional)
            
        Returns:
            Current CPU usage (0.0-1.0)
        """
        if pod_name:
            query = f'rate(container_cpu_usage_seconds_total{{namespace="{namespace}", pod="{pod_name}"}}[5m])'
        else:
            query = f'sum(rate(container_cpu_usage_seconds_total{{namespace="{namespace}"}}[5m]))'
        
        result = self.query(query)
        
        if result.get('status') == 'success':
            data = result.get('data', {}).get('result', [])
            if data:
                value = float(data[0]['value'][1])
                return value
        
        return 0.0
    
    def get_historical_cpu_usage(self, namespace: str = 'default', 
                                minutes: int = 60, step: str = '1m') -> List[float]:
        """
        Get historical CPU usage values
        
        Args:
            namespace: Kubernetes namespace
            minutes: Number of minutes of history
            step: Query resolution
            
        Returns:
            List of CPU usage values
        """
        end = datetime.now()
        start = end - timedelta(minutes=minutes)
        
        query = f'sum(rate(container_cpu_usage_seconds_total{{namespace="{namespace}"}}[5m]))'
        result = self.query_range(query, start, end, step)
        
        cpu_values = []
        if result.get('status') == 'success':
            data = result.get('data', {}).get('result', [])
            if data:
                for timestamp, value in data[0].get('values', []):
                    cpu_values.append(float(value))
        
        return cpu_values
    
    def get_current_memory_usage(self, namespace: str = 'default') -> float:
        """
        Get current memory usage in bytes
        
        Args:
            namespace: Kubernetes namespace
            
        Returns:
            Current memory usage in bytes
        """
        query = f'sum(container_memory_usage_bytes{{namespace="{namespace}"}})'
        result = self.query(query)
        
        if result.get('status') == 'success':
            data = result.get('data', {}).get('result', [])
            if data:
                value = float(data[0]['value'][1])
                return value
        
        return 0.0
    
    def get_pod_count(self, namespace: str = 'default') -> int:
        """
        Get current pod count
        
        Args:
            namespace: Kubernetes namespace
            
        Returns:
            Number of pods
        """
        query = f'count(kube_pod_info{{namespace="{namespace}"}})'
        result = self.query(query)
        
        if result.get('status') == 'success':
            data = result.get('data', {}).get('result', [])
            if data:
                value = int(float(data[0]['value'][1]))
                return value
        
        return 0
    
    def health_check(self) -> bool:
        """
        Check if Prometheus is reachable
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            url = f"{self.prometheus_url}/-/healthy"
            response = self.session.get(url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False


def create_prometheus_client(prometheus_url: str) -> PrometheusClient:
    """
    Factory function to create Prometheus client
    
    Args:
        prometheus_url: Prometheus URL
        
    Returns:
        PrometheusClient instance
    """
    return PrometheusClient(prometheus_url)

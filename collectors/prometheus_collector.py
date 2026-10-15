"""
Prometheus Data Collector
Collects CPU, memory, and pod metrics from Prometheus HTTP API
"""

import os
import requests
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


class PrometheusCollector:
    """Collects metrics from Prometheus"""
    
    def __init__(self, prometheus_url: str):
        """
        Initialize Prometheus collector
        
        Args:
            prometheus_url: Base URL of Prometheus instance (e.g., http://localhost:9090)
        """
        self.prometheus_url = prometheus_url.rstrip('/')
        self.api_url = f"{self.prometheus_url}/api/v1"
        self.session = requests.Session()
        
    def query(self, query: str) -> Dict[str, Any]:
        """
        Execute instant query
        
        Args:
            query: PromQL query
            
        Returns:
            Query result
        """
        try:
            url = f"{self.api_url}/query"
            params = {'query': query}
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error executing query '{query}': {e}")
            return {}
    
    def query_range(self, query: str, start: datetime, end: datetime, step: str = '1m') -> Dict[str, Any]:
        """
        Execute range query
        
        Args:
            query: PromQL query
            start: Start time
            end: End time
            step: Query resolution step width (e.g., '1m', '5m')
            
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
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error executing range query '{query}': {e}")
            return {}
    
    def get_cpu_usage(self, namespace: str = 'default', 
                     pod_name: Optional[str] = None,
                     start: Optional[datetime] = None,
                     end: Optional[datetime] = None,
                     step: str = '1m') -> pd.DataFrame:
        """
        Get CPU usage metrics
        
        Args:
            namespace: Kubernetes namespace
            pod_name: Specific pod name (optional)
            start: Start time (defaults to 1 hour ago)
            end: End time (defaults to now)
            step: Query resolution
            
        Returns:
            DataFrame with CPU metrics
        """
        if end is None:
            end = datetime.now()
        if start is None:
            start = end - timedelta(hours=1)
        
        # Build query
        if pod_name:
            query = f'rate(container_cpu_usage_seconds_total{{namespace="{namespace}", pod="{pod_name}"}}[5m])'
        else:
            query = f'sum(rate(container_cpu_usage_seconds_total{{namespace="{namespace}"}}[5m])) by (pod)'
        
        result = self.query_range(query, start, end, step)
        
        return self._parse_range_result(result, 'cpu_usage')
    
    def get_memory_usage(self, namespace: str = 'default',
                        pod_name: Optional[str] = None,
                        start: Optional[datetime] = None,
                        end: Optional[datetime] = None,
                        step: str = '1m') -> pd.DataFrame:
        """
        Get memory usage metrics
        
        Args:
            namespace: Kubernetes namespace
            pod_name: Specific pod name (optional)
            start: Start time (defaults to 1 hour ago)
            end: End time (defaults to now)
            step: Query resolution
            
        Returns:
            DataFrame with memory metrics
        """
        if end is None:
            end = datetime.now()
        if start is None:
            start = end - timedelta(hours=1)
        
        # Build query
        if pod_name:
            query = f'container_memory_usage_bytes{{namespace="{namespace}", pod="{pod_name}"}}'
        else:
            query = f'sum(container_memory_usage_bytes{{namespace="{namespace}"}}) by (pod)'
        
        result = self.query_range(query, start, end, step)
        
        return self._parse_range_result(result, 'memory_usage_bytes')
    
    def get_pod_count(self, namespace: str = 'default',
                     start: Optional[datetime] = None,
                     end: Optional[datetime] = None,
                     step: str = '1m') -> pd.DataFrame:
        """
        Get pod count metrics
        
        Args:
            namespace: Kubernetes namespace
            start: Start time (defaults to 1 hour ago)
            end: End time (defaults to now)
            step: Query resolution
            
        Returns:
            DataFrame with pod count
        """
        if end is None:
            end = datetime.now()
        if start is None:
            start = end - timedelta(hours=1)
        
        # Build query
        query = f'count(kube_pod_info{{namespace="{namespace}"}})'
        
        result = self.query_range(query, start, end, step)
        
        return self._parse_range_result(result, 'pod_count')
    
    def get_node_cpu_usage(self, start: Optional[datetime] = None,
                          end: Optional[datetime] = None,
                          step: str = '1m') -> pd.DataFrame:
        """
        Get node-level CPU usage
        
        Args:
            start: Start time (defaults to 1 hour ago)
            end: End time (defaults to now)
            step: Query resolution
            
        Returns:
            DataFrame with node CPU metrics
        """
        if end is None:
            end = datetime.now()
        if start is None:
            start = end - timedelta(hours=1)
        
        query = 'sum(rate(node_cpu_seconds_total{mode!="idle"}[5m])) by (instance)'
        
        result = self.query_range(query, start, end, step)
        
        return self._parse_range_result(result, 'node_cpu_usage')
    
    def _parse_range_result(self, result: Dict[str, Any], metric_name: str) -> pd.DataFrame:
        """
        Parse Prometheus range query result into DataFrame
        
        Args:
            result: Query result from Prometheus
            metric_name: Name for the metric column
            
        Returns:
            DataFrame with timestamp and metric columns
        """
        data = []
        
        if result.get('status') != 'success':
            print(f"Query failed: {result}")
            return pd.DataFrame()
        
        result_data = result.get('data', {}).get('result', [])
        
        for series in result_data:
            metric_labels = series.get('metric', {})
            values = series.get('values', [])
            
            for timestamp, value in values:
                row = {
                    'timestamp': datetime.fromtimestamp(timestamp),
                    metric_name: float(value)
                }
                # Add metric labels
                row.update(metric_labels)
                data.append(row)
        
        df = pd.DataFrame(data)
        
        if not df.empty:
            df = df.sort_values('timestamp')
        
        return df
    
    def collect_workload_metrics(self, namespace: str = 'default',
                                 hours: int = 24,
                                 step: str = '1m',
                                 output_dir: str = 'training/data/prometheus') -> pd.DataFrame:
        """
        Collect comprehensive workload metrics
        
        Args:
            namespace: Kubernetes namespace
            hours: Number of hours of historical data
            step: Query resolution
            output_dir: Directory to save data
            
        Returns:
            Combined DataFrame with all metrics
        """
        print(f"Collecting metrics for namespace: {namespace}")
        
        end = datetime.now()
        start = end - timedelta(hours=hours)
        
        print(f"Time range: {start} to {end}")
        
        # Collect CPU metrics
        print("Collecting CPU metrics...")
        cpu_df = self.get_cpu_usage(namespace, start=start, end=end, step=step)
        
        # Collect memory metrics
        print("Collecting memory metrics...")
        memory_df = self.get_memory_usage(namespace, start=start, end=end, step=step)
        
        # Collect pod count
        print("Collecting pod count...")
        pod_df = self.get_pod_count(namespace, start=start, end=end, step=step)
        
        # Merge dataframes
        if not cpu_df.empty:
            combined_df = cpu_df.copy()
            
            if not memory_df.empty:
                combined_df = pd.merge(combined_df, memory_df, on=['timestamp', 'pod'], how='outer')
            
            if not pod_df.empty:
                # Pod count doesn't have pod label, merge only on timestamp
                pod_df_agg = pod_df.groupby('timestamp').first().reset_index()
                combined_df = pd.merge(combined_df, pod_df_agg[['timestamp', 'pod_count']], 
                                      on='timestamp', how='left')
            
            # Save to CSV
            os.makedirs(output_dir, exist_ok=True)
            timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"{output_dir}/metrics_{namespace}_{timestamp_str}.csv"
            combined_df.to_csv(output_file, index=False)
            print(f"Saved metrics to {output_file}")
            
            return combined_df
        
        return pd.DataFrame()
    
    def collect_cpu_for_lstm(self, namespace: str = 'default',
                            hours: int = 168,  # 1 week
                            step: str = '1m',
                            output_dir: str = 'training/data/prometheus') -> pd.DataFrame:
        """
        Collect CPU metrics specifically for LSTM training
        
        Args:
            namespace: Kubernetes namespace
            hours: Number of hours of historical data (default: 1 week)
            step: Query resolution
            output_dir: Directory to save data
            
        Returns:
            DataFrame with aggregated CPU metrics
        """
        print(f"Collecting CPU metrics for LSTM training...")
        
        end = datetime.now()
        start = end - timedelta(hours=hours)
        
        # Get aggregated CPU usage across all pods
        query = f'sum(rate(container_cpu_usage_seconds_total{{namespace="{namespace}"}}[5m]))'
        result = self.query_range(query, start, end, step)
        
        df = self._parse_range_result(result, 'cpu_usage')
        
        if not df.empty:
            # Sort by timestamp
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # Save to CSV
            os.makedirs(output_dir, exist_ok=True)
            output_file = f"{output_dir}/cpu_timeseries.csv"
            df.to_csv(output_file, index=False)
            print(f"Saved {len(df)} CPU samples to {output_file}")
            
            return df
        
        return pd.DataFrame()


def main():
    """Main function for standalone execution"""
    # Load configuration from environment variables
    prometheus_url = os.getenv('PROMETHEUS_URL', 'http://localhost:9090')
    namespace = os.getenv('K8S_NAMESPACE', 'default')
    
    # Create collector
    collector = PrometheusCollector(prometheus_url)
    
    # Collect workload metrics
    df = collector.collect_workload_metrics(namespace=namespace, hours=24)
    
    print(f"\nCollected {len(df)} metric samples")
    print(f"\nMetrics summary:")
    print(df.describe())
    
    # Collect CPU data for LSTM
    cpu_df = collector.collect_cpu_for_lstm(namespace=namespace, hours=168)
    print(f"\nCollected {len(cpu_df)} CPU samples for LSTM training")


if __name__ == '__main__':
    main()

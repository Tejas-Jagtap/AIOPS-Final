"""
Kubernetes client wrapper for managing deployments and scaling
"""

import os
from typing import Optional, Dict, Any
from kubernetes import client, config
from kubernetes.client.rest import ApiException


class KubernetesClient:
    """Wrapper for Kubernetes API operations"""
    
    def __init__(self, in_cluster: bool = False, kubeconfig_path: Optional[str] = None):
        """
        Initialize Kubernetes client
        
        Args:
            in_cluster: Whether running inside a Kubernetes cluster
            kubeconfig_path: Path to kubeconfig file (if not in-cluster)
        """
        try:
            if in_cluster:
                config.load_incluster_config()
            else:
                if kubeconfig_path:
                    config.load_kube_config(config_file=kubeconfig_path)
                else:
                    config.load_kube_config()
            
            self.apps_v1 = client.AppsV1Api()
            self.core_v1 = client.CoreV1Api()
            
            print("Kubernetes client initialized successfully")
        except Exception as e:
            print(f"Error initializing Kubernetes client: {e}")
            raise
    
    def get_deployment(self, name: str, namespace: str = 'default') -> Optional[client.V1Deployment]:
        """
        Get deployment by name
        
        Args:
            name: Deployment name
            namespace: Namespace
            
        Returns:
            Deployment object or None
        """
        try:
            deployment = self.apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
            return deployment
        except ApiException as e:
            if e.status == 404:
                print(f"Deployment {name} not found in namespace {namespace}")
                return None
            print(f"Error getting deployment: {e}")
            raise
    
    def get_deployment_replicas(self, name: str, namespace: str = 'default') -> int:
        """
        Get current replica count for a deployment
        
        Args:
            name: Deployment name
            namespace: Namespace
            
        Returns:
            Current replica count
        """
        deployment = self.get_deployment(name, namespace)
        if deployment:
            return deployment.spec.replicas
        return 0
    
    def scale_deployment(self, name: str, replicas: int, namespace: str = 'default') -> bool:
        """
        Scale a deployment to specified replica count
        
        Args:
            name: Deployment name
            replicas: Target replica count
            namespace: Namespace
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current deployment
            deployment = self.get_deployment(name, namespace)
            if not deployment:
                return False
            
            # Update replica count
            deployment.spec.replicas = replicas
            
            # Patch deployment
            self.apps_v1.patch_namespaced_deployment(
                name=name,
                namespace=namespace,
                body=deployment
            )
            
            print(f"Scaled deployment {name} to {replicas} replicas")
            return True
        except ApiException as e:
            print(f"Error scaling deployment: {e}")
            return False
    
    def get_pod_metrics(self, namespace: str = 'default') -> list:
        """
        Get pods in a namespace
        
        Args:
            namespace: Namespace
            
        Returns:
            List of pod objects
        """
        try:
            pods = self.core_v1.list_namespaced_pod(namespace=namespace)
            return pods.items
        except ApiException as e:
            print(f"Error getting pods: {e}")
            return []
    
    def get_pod_count(self, namespace: str = 'default', label_selector: Optional[str] = None) -> int:
        """
        Get count of pods in a namespace
        
        Args:
            namespace: Namespace
            label_selector: Label selector (e.g., 'app=myapp')
            
        Returns:
            Number of pods
        """
        try:
            pods = self.core_v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=label_selector
            )
            return len(pods.items)
        except ApiException as e:
            print(f"Error getting pod count: {e}")
            return 0
    
    def get_deployment_status(self, name: str, namespace: str = 'default') -> Dict[str, Any]:
        """
        Get detailed deployment status
        
        Args:
            name: Deployment name
            namespace: Namespace
            
        Returns:
            Dictionary with deployment status
        """
        deployment = self.get_deployment(name, namespace)
        if not deployment:
            return {}
        
        status = {
            'name': name,
            'namespace': namespace,
            'replicas': deployment.spec.replicas,
            'ready_replicas': deployment.status.ready_replicas or 0,
            'available_replicas': deployment.status.available_replicas or 0,
            'unavailable_replicas': deployment.status.unavailable_replicas or 0,
            'updated_replicas': deployment.status.updated_replicas or 0,
        }
        
        return status
    
    def list_deployments(self, namespace: str = 'default') -> list:
        """
        List all deployments in a namespace
        
        Args:
            namespace: Namespace
            
        Returns:
            List of deployment names
        """
        try:
            deployments = self.apps_v1.list_namespaced_deployment(namespace=namespace)
            return [d.metadata.name for d in deployments.items]
        except ApiException as e:
            print(f"Error listing deployments: {e}")
            return []


def create_k8s_client(in_cluster: Optional[bool] = None, kubeconfig_path: Optional[str] = None) -> KubernetesClient:
    """
    Factory function to create Kubernetes client
    
    Args:
        in_cluster: Whether running inside cluster (auto-detect if None)
        kubeconfig_path: Path to kubeconfig file
        
    Returns:
        KubernetesClient instance
    """
    if in_cluster is None:
        # Auto-detect: if KUBERNETES_SERVICE_HOST is set, we're in-cluster
        in_cluster = 'KUBERNETES_SERVICE_HOST' in os.environ
    
    return KubernetesClient(in_cluster=in_cluster, kubeconfig_path=kubeconfig_path)

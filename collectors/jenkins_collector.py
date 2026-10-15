"""
Jenkins Data Collector
Collects build metadata and console logs from Jenkins REST API
"""

import os
import json
import requests
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd
from requests.auth import HTTPBasicAuth


class JenkinsCollector:
    """Collects build data and console logs from Jenkins"""
    
    def __init__(self, jenkins_url: str, username: str, token: str):
        """
        Initialize Jenkins collector
        
        Args:
            jenkins_url: Base URL of Jenkins instance (e.g., http://localhost:8080)
            username: Jenkins username
            token: Jenkins API token
        """
        self.jenkins_url = jenkins_url.rstrip('/')
        self.auth = HTTPBasicAuth(username, token)
        self.session = requests.Session()
        self.session.auth = self.auth
        
    def get_jobs(self) -> List[str]:
        """
        Get list of all job names
        
        Returns:
            List of job names
        """
        try:
            url = f"{self.jenkins_url}/api/json?tree=jobs[name]"
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            return [job['name'] for job in data.get('jobs', [])]
        except Exception as e:
            print(f"Error fetching jobs: {e}")
            return []
    
    def get_build_numbers(self, job_name: str, max_builds: int = 100) -> List[int]:
        """
        Get build numbers for a job
        
        Args:
            job_name: Name of the Jenkins job
            max_builds: Maximum number of builds to retrieve
            
        Returns:
            List of build numbers
        """
        try:
            # Use allBuilds instead of builds to get ALL builds (not just recent ones)
            url = f"{self.jenkins_url}/job/{job_name}/api/json?tree=allBuilds[number]"
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Try allBuilds first, fall back to builds
            builds_data = data.get('allBuilds', data.get('builds', []))
            builds = [build['number'] for build in builds_data]
            
            # Sort descending (newest first) and limit
            builds = sorted(builds, reverse=True)[:max_builds]
            return builds
        except Exception as e:
            print(f"Error fetching build numbers for {job_name}: {e}")
            return []
    
    def get_build_metadata(self, job_name: str, build_number: int) -> Dict[str, Any]:
        """
        Get metadata for a specific build
        
        Args:
            job_name: Name of the Jenkins job
            build_number: Build number
            
        Returns:
            Dictionary containing build metadata
        """
        try:
            url = f"{self.jenkins_url}/job/{job_name}/{build_number}/api/json"
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Extract relevant metadata
            metadata = {
                'job_name': job_name,
                'build_number': build_number,
                'result': data.get('result', 'UNKNOWN'),
                'duration': data.get('duration', 0) / 1000,  # Convert to seconds
                'timestamp': data.get('timestamp', 0) / 1000,  # Convert to seconds
                'url': data.get('url', ''),
            }
            
            # Count test results if available
            actions = data.get('actions', [])
            for action in actions:
                if action.get('_class') == 'hudson.tasks.junit.TestResultAction':
                    metadata['tests_failed'] = action.get('failCount', 0)
                    metadata['tests_passed'] = action.get('passCount', 0)
                    metadata['tests_skipped'] = action.get('skipCount', 0)
                    metadata['tests_total'] = action.get('totalCount', 0)
            
            return metadata
        except Exception as e:
            print(f"Error fetching metadata for {job_name} #{build_number}: {e}")
            return {}
    
    def get_console_log(self, job_name: str, build_number: int) -> str:
        """
        Get console log for a specific build
        
        Args:
            job_name: Name of the Jenkins job
            build_number: Build number
            
        Returns:
            Console log text
        """
        try:
            url = f"{self.jenkins_url}/job/{job_name}/{build_number}/consoleText"
            response = self.session.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching console log for {job_name} #{build_number}: {e}")
            return ""
    
    def extract_log_features(self, log_text: str) -> Dict[str, int]:
        """
        Extract features from console log
        
        Args:
            log_text: Console log text
            
        Returns:
            Dictionary with extracted features
        """
        features = {
            'warnings': log_text.lower().count('warning'),
            'errors': log_text.lower().count('error'),
            'failures': log_text.lower().count('failure'),
            'log_length': len(log_text),
        }
        return features
    
    def collect_job_data(self, job_name: str, max_builds: int = 100, 
                        save_logs: bool = True, output_dir: str = 'training/data/jenkins') -> pd.DataFrame:
        """
        Collect all data for a job
        
        Args:
            job_name: Name of the Jenkins job
            max_builds: Maximum number of builds to collect
            save_logs: Whether to save console logs
            output_dir: Directory to save data
            
        Returns:
            DataFrame with build metadata and features
        """
        print(f"Collecting data for job: {job_name}")
        
        build_numbers = self.get_build_numbers(job_name, max_builds)
        print(f"Found {len(build_numbers)} builds")
        
        data = []
        for build_number in build_numbers:
            print(f"Processing build #{build_number}...")
            
            # Get metadata
            metadata = self.get_build_metadata(job_name, build_number)
            if not metadata:
                continue
            
            # Get console log
            console_log = self.get_console_log(job_name, build_number)
            
            # Extract log features
            log_features = self.extract_log_features(console_log)
            
            # Combine metadata and features
            build_data = {**metadata, **log_features}
            data.append(build_data)
            
            # Save console log if requested
            if save_logs and console_log:
                os.makedirs(f"{output_dir}/logs/{job_name}", exist_ok=True)
                log_file = f"{output_dir}/logs/{job_name}/build_{build_number}.log"
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write(console_log)
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Save metadata
        if not df.empty:
            os.makedirs(f"{output_dir}/metadata", exist_ok=True)
            csv_file = f"{output_dir}/metadata/{job_name}.csv"
            df.to_csv(csv_file, index=False)
            print(f"Saved metadata to {csv_file}")
        
        return df
    
    def collect_all_jobs(self, max_builds_per_job: int = 100, 
                        output_dir: str = 'training/data/jenkins') -> pd.DataFrame:
        """
        Collect data for all jobs
        
        Args:
            max_builds_per_job: Maximum builds per job
            output_dir: Directory to save data
            
        Returns:
            Combined DataFrame with all job data
        """
        jobs = self.get_jobs()
        print(f"Found {len(jobs)} jobs")
        
        all_data = []
        for job in jobs:
            df = self.collect_job_data(job, max_builds_per_job, output_dir=output_dir)
            if not df.empty:
                all_data.append(df)
        
        # Combine all data
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            
            # Save combined data
            os.makedirs(output_dir, exist_ok=True)
            combined_file = f"{output_dir}/all_builds.csv"
            combined_df.to_csv(combined_file, index=False)
            print(f"Saved combined data to {combined_file}")
            
            return combined_df
        
        return pd.DataFrame()


def main():
    """Main function for standalone execution"""
    # Load configuration from environment variables
    jenkins_url = os.getenv('JENKINS_URL', 'http://localhost:8080')
    jenkins_user = os.getenv('JENKINS_USER', 'admin')
    jenkins_token = os.getenv('JENKINS_TOKEN', '')
    
    if not jenkins_token:
        print("Error: JENKINS_TOKEN environment variable not set")
        return
    
    # Create collector
    collector = JenkinsCollector(jenkins_url, jenkins_user, jenkins_token)
    
    # Collect data for all jobs
    df = collector.collect_all_jobs(max_builds_per_job=50)
    
    print(f"\nCollected {len(df)} builds total")
    print(f"\nBuild results distribution:")
    print(df['result'].value_counts())


if __name__ == '__main__':
    main()

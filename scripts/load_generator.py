"""
Load Generator for Demo Todo App
Generates realistic traffic to create real Prometheus metrics
"""

import requests
import random
import time
import threading
from datetime import datetime

BASE_URL = "http://localhost:3000"

# Sample todo texts
TODO_TEXTS = [
    "Review pull request",
    "Update documentation",
    "Fix critical bug",
    "Deploy to staging",
    "Write unit tests",
    "Database migration",
    "Performance optimization",
    "Security audit",
    "Code review meeting",
    "Sprint planning",
    "Refactor legacy code",
    "API endpoint testing",
    "Container deployment",
    "CI/CD pipeline fix",
    "Log analysis",
    "Metrics dashboard",
    "Alert configuration",
    "Load testing",
    "Backup verification",
    "Scaling assessment"
]

class LoadGenerator:
    def __init__(self):
        self.running = False
        self.stats = {
            'requests': 0,
            'errors': 0,
            'todos_created': 0,
            'todos_deleted': 0
        }
    
    def get_todos(self):
        """Fetch all todos"""
        try:
            response = requests.get(f"{BASE_URL}/api/todos", timeout=5)
            self.stats['requests'] += 1
            if response.status_code == 200:
                return response.json().get('todos', [])
            else:
                self.stats['errors'] += 1
        except Exception as e:
            self.stats['errors'] += 1
            print(f"Error fetching todos: {e}")
        return []
    
    def create_todo(self, text=None):
        """Create a new todo"""
        if text is None:
            text = random.choice(TODO_TEXTS)
        try:
            response = requests.post(
                f"{BASE_URL}/api/todos",
                json={"text": text},
                timeout=5
            )
            self.stats['requests'] += 1
            if response.status_code == 201:
                self.stats['todos_created'] += 1
                return response.json().get('todo')
            else:
                self.stats['errors'] += 1
        except Exception as e:
            self.stats['errors'] += 1
            print(f"Error creating todo: {e}")
        return None
    
    def toggle_todo(self, todo_id, completed):
        """Toggle todo completion status"""
        try:
            response = requests.put(
                f"{BASE_URL}/api/todos/{todo_id}",
                json={"completed": completed},
                timeout=5
            )
            self.stats['requests'] += 1
            if response.status_code != 200:
                self.stats['errors'] += 1
        except Exception as e:
            self.stats['errors'] += 1
            print(f"Error toggling todo: {e}")
    
    def delete_todo(self, todo_id):
        """Delete a specific todo"""
        try:
            response = requests.delete(
                f"{BASE_URL}/api/todos/{todo_id}",
                timeout=5
            )
            self.stats['requests'] += 1
            if response.status_code == 200:
                self.stats['todos_deleted'] += 1
            else:
                self.stats['errors'] += 1
        except Exception as e:
            self.stats['errors'] += 1
            print(f"Error deleting todo: {e}")
    
    def get_health(self):
        """Check health endpoint"""
        try:
            response = requests.get(f"{BASE_URL}/api/health", timeout=5)
            self.stats['requests'] += 1
            if response.status_code != 200:
                self.stats['errors'] += 1
        except Exception as e:
            self.stats['errors'] += 1
    
    def get_metrics(self):
        """Fetch metrics endpoint"""
        try:
            response = requests.get(f"{BASE_URL}/api/metrics", timeout=5)
            if response.status_code == 200:
                return response.text
        except Exception as e:
            print(f"Error fetching metrics: {e}")
        return None
    
    def generate_workload(self, intensity='medium', duration_minutes=5):
        """
        Generate realistic workload
        intensity: 'low', 'medium', 'high'
        """
        intensities = {
            'low': {'rps': 0.5, 'create_prob': 0.1, 'toggle_prob': 0.2, 'delete_prob': 0.05},
            'medium': {'rps': 2, 'create_prob': 0.2, 'toggle_prob': 0.3, 'delete_prob': 0.1},
            'high': {'rps': 5, 'create_prob': 0.3, 'toggle_prob': 0.4, 'delete_prob': 0.15}
        }
        
        config = intensities.get(intensity, intensities['medium'])
        sleep_time = 1 / config['rps']
        end_time = time.time() + (duration_minutes * 60)
        
        print(f"\n🚀 Starting load generation ({intensity} intensity)")
        print(f"   Target RPS: {config['rps']}")
        print(f"   Duration: {duration_minutes} minutes")
        print(f"   Press Ctrl+C to stop early\n")
        
        self.running = True
        
        try:
            while time.time() < end_time and self.running:
                # Get current todos
                todos = self.get_todos()
                
                # Random action based on probability
                rand = random.random()
                
                if rand < config['create_prob']:
                    # Create a new todo
                    self.create_todo()
                elif rand < config['create_prob'] + config['toggle_prob'] and todos:
                    # Toggle a random todo
                    todo = random.choice(todos)
                    self.toggle_todo(todo['id'], not todo.get('completed', False))
                elif rand < config['create_prob'] + config['toggle_prob'] + config['delete_prob'] and todos:
                    # Delete a random todo
                    todo = random.choice(todos)
                    self.delete_todo(todo['id'])
                else:
                    # Just check health
                    self.get_health()
                
                # Print progress every 10 requests
                if self.stats['requests'] % 10 == 0:
                    elapsed = duration_minutes - ((end_time - time.time()) / 60)
                    print(f"   [{elapsed:.1f}/{duration_minutes}min] Requests: {self.stats['requests']}, "
                          f"Errors: {self.stats['errors']}, "
                          f"Created: {self.stats['todos_created']}, "
                          f"Deleted: {self.stats['todos_deleted']}")
                
                time.sleep(sleep_time + random.uniform(-0.1, 0.1))
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Load generation stopped by user")
        
        self.running = False
        self._print_summary()
    
    def _print_summary(self):
        """Print load test summary"""
        print("\n" + "="*50)
        print("📊 LOAD TEST SUMMARY")
        print("="*50)
        print(f"   Total Requests: {self.stats['requests']}")
        print(f"   Errors: {self.stats['errors']}")
        print(f"   Error Rate: {(self.stats['errors']/max(1,self.stats['requests'])*100):.2f}%")
        print(f"   Todos Created: {self.stats['todos_created']}")
        print(f"   Todos Deleted: {self.stats['todos_deleted']}")
        print("="*50)
        
        # Show current metrics
        print("\n📈 Current Application Metrics:")
        metrics = self.get_metrics()
        if metrics:
            for line in metrics.split('\n'):
                if not line.startswith('#') and line.strip():
                    print(f"   {line}")
        print()


def main():
    print("="*50)
    print("🎯 DEMO TODO APP - LOAD GENERATOR")
    print("="*50)
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if app is running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ App is healthy and ready")
        else:
            print(f"⚠️  App returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to app: {e}")
        print("\n   Make sure the demo-todo-app is running:")
        print("   cd demo-todo-app && npm run dev")
        return
    
    generator = LoadGenerator()
    
    # Run with medium intensity for 5 minutes
    generator.generate_workload(intensity='medium', duration_minutes=5)


if __name__ == "__main__":
    main()

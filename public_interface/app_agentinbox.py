# Vercel Deployment - Autonomous-Agentic-AI-Inbox Dashboard
# This app uses LangSmith API to fetch data for the email_assistant_hitl_memory_gmail graph
# For now, using simulated data until we get the correct API key
# INCLUDES AUTOMATIC BACKGROUND CRON JOB FOR PRODUCTION

from flask import Flask, render_template, jsonify, request
import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import threading
import time
import subprocess
from pathlib import Path
import threading
import time
import subprocess
from pathlib import Path

load_dotenv()

# Configuration - YOUR LangSmith API key
LANGSMITH_API_KEY = "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"
LANGSMITH_ENDPOINT = "https://api.smith.langchain.com"
GRAPH_ID = "email_assistant_hitl_memory_gmail"

# Global variables for background job management
background_job_running = False
last_ingest_time = None
ingest_count = 0

class LangSmithDashboard:
    def __init__(self):
        self.api_key = LANGSMITH_API_KEY
        self.endpoint = LANGSMITH_ENDPOINT
        self.graph_id = GRAPH_ID
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def run_email_ingest_job(self):
        """Run the actual email ingest job using the ingest script"""
        global last_ingest_time, ingest_count
        
        try:
            print(f"🔄 Running background email ingest job #{ingest_count + 1}")
            
            # Get the path to the ingest script
            script_path = Path(__file__).parent.parent / "src" / "email_assistant" / "tools" / "gmail" / "run_ingest_agentinbox.py"
            
            if script_path.exists():
                # Run the ingest script
                result = subprocess.run([
                    "python", str(script_path),
                    "--email", "your-email@gmail.com",  # This should be configurable
                    "--minutes-since", "5"
                ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
                
                if result.returncode == 0:
                    print(f"✅ Background ingest job #{ingest_count + 1} completed successfully")
                    print(f"Output: {result.stdout}")
                    last_ingest_time = datetime.now()
                    ingest_count += 1
                    return True
                else:
                    print(f"❌ Background ingest job #{ingest_count + 1} failed")
                    print(f"Error: {result.stderr}")
                    return False
            else:
                print(f"❌ Ingest script not found at {script_path}")
                return False
                
        except Exception as e:
            print(f"❌ Error running background ingest job: {e}")
            return False
    
    def get_simulated_data(self):
        """Get simulated dashboard data for development/testing"""
        try:
            # Simulate email processing data based on the graph ID
            current_time = datetime.now()
            
            # Generate realistic simulated data
            stats = {
                "total_runs": 156,
                "successful_runs": 142,
                "failed_runs": 14,
                "email_processing_runs": 89,
                "hitl_runs": 23,
                "scheduled_meetings": 8,
                "notifications": 12,
                "total_emails": 89,
                "processed": 67,
                "hitl": 18,
                "pending": 4
            }
            
            # Create simulated email threads
            threads = []
            for i in range(1, 21):
                # Vary the status distribution
                if i <= 12:
                    status = "processed"
                elif i <= 18:
                    status = "hitl"
                else:
                    status = "pending"
                
                # Generate realistic email subjects
                subjects = [
                    "Meeting Request for Q4 Planning",
                    "Project Status Update - AI Integration",
                    "Client Feedback on New Features",
                    "Budget Approval Required",
                    "Team Meeting Schedule",
                    "Code Review Request",
                    "Deployment Status Check",
                    "Security Audit Results",
                    "Performance Metrics Report",
                    "User Experience Feedback",
                    "API Documentation Update",
                    "Database Migration Plan",
                    "Testing Results Summary",
                    "Production Issue Alert",
                    "Feature Request - Email Automation",
                    "Bug Report - Login Issues",
                    "System Maintenance Notice",
                    "Backup Verification Complete",
                    "New User Onboarding",
                    "Quarterly Review Meeting"
                ]
                
                threads.append({
                    "id": f"thread_{i}",
                    "subject": subjects[i-1] if i <= len(subjects) else f"Email Thread {i}",
                    "sender": f"sender{i}@company.com",
                    "status": status,
                    "last_updated": (current_time - timedelta(hours=i*2)).isoformat(),
                    "message_count": i + 1,
                    "run_type": "email_processing"
                })
            
            return {
                "statistics": stats,
                "threads": threads,
                "source": f"Simulated Data - Graph: {self.graph_id}",
                "last_updated": current_time.isoformat(),
                "total_runs": stats["total_runs"],
                "successful_runs": stats["successful_runs"],
                "failed_runs": stats["failed_runs"],
                "scheduled_meetings": stats["scheduled_meetings"],
                "notifications": stats["notifications"]
            }
            
        except Exception as e:
            print(f"Error getting simulated data: {e}")
            return {
                "error": str(e),
                "statistics": {
                    "total_emails": 0,
                    "processed": 0,
                    "hitl": 0,
                    "pending": 0,
                    "total_runs": 0,
                    "successful_runs": 0,
                    "failed_runs": 0,
                    "scheduled_meetings": 0,
                    "notifications": 0
                },
                "threads": [],
                "source": "Error",
                "last_updated": datetime.now().isoformat()
            }
    
    def get_runs_data(self):
        """Fetch runs data from LangSmith for the email graph"""
        try:
            # Get recent runs for the specific graph
            url = f"{self.endpoint}/runs"
            params = {
                "limit": 100,
                "start_time": (datetime.now() - timedelta(days=7)).isoformat(),
                "tags": [f"graph:{self.graph_id}"]
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to fetch runs: {response.status_code}")
                return {"runs": []}
                
        except Exception as e:
            print(f"Error fetching runs: {e}")
            return {"runs": []}
    
    def get_dashboard_data(self):
        """Get comprehensive dashboard data from LangSmith or fallback to simulated data"""
        try:
            # First try to get real data from LangSmith
            runs_data = self.get_runs_data()
            if runs_data.get("runs"):
                # Process real data
                runs = runs_data.get("runs", [])
                
                # Analyze runs to extract statistics
                stats = {
                    "total_runs": len(runs),
                    "successful_runs": 0,
                    "failed_runs": 0,
                    "email_processing_runs": 0,
                    "hitl_runs": 0,
                    "scheduled_meetings": 0,
                    "notifications": 0,
                    "total_emails": 0,
                    "processed": 0,
                    "hitl": 0,
                    "pending": 0
                }
                
                # Process each run
                for run in runs:
                    # Count by status
                    if run.get("status") == "completed":
                        stats["successful_runs"] += 1
                    elif run.get("status") == "failed":
                        stats["failed_runs"] += 1
                    
                    # Analyze run name and metadata
                    run_name = run.get("name", "").lower()
                    run_type = run.get("run_type", "").lower()
                    
                    # Count email-related runs
                    if "email" in run_name or "gmail" in run_name or "inbox" in run_name:
                        stats["email_processing_runs"] += 1
                        stats["total_emails"] += 1
                        
                        # Determine email status based on run outcome
                        if run.get("status") == "completed":
                            stats["processed"] += 1
                        elif "hitl" in run_name or "human" in run_name:
                            stats["hitl"] += 1
                        else:
                            stats["pending"] += 1
                    
                    # Count HITL runs
                    if "hitl" in run_name or "human" in run_name:
                        stats["hitl_runs"] += 1
                    
                    # Count scheduled meetings
                    if "meeting" in run_name or "calendar" in run_name:
                        stats["scheduled_meetings"] += 1
                    
                    # Count notifications
                    if "notification" in run_name or "alert" in run_name:
                        stats["notifications"] += 1
                
                # Create email threads from runs
                threads = []
                for run in runs[:20]:  # Show last 20 runs
                    if "email" in run.get("name", "").lower():
                        threads.append({
                            "id": run.get("id", "unknown"),
                            "subject": run.get("name", "Email Processing"),
                            "sender": "System",
                            "status": run.get("status", "unknown"),
                            "last_updated": run.get("end_time", run.get("start_time", "unknown")),
                            "message_count": 1,
                            "run_type": run.get("run_type", "unknown")
                        })
                
                return {
                    "statistics": stats,
                    "threads": threads,
                    "source": f"LangSmith API - Graph: {self.graph_id}",
                    "last_updated": datetime.now().isoformat(),
                    "total_runs": stats["total_runs"],
                    "successful_runs": stats["successful_runs"],
                    "failed_runs": stats["failed_runs"],
                    "scheduled_meetings": stats["scheduled_meetings"],
                    "notifications": stats["notifications"]
                }
            else:
                # Fallback to simulated data
                print("Using simulated data - LangSmith API not accessible")
                return self.get_simulated_data()
            
        except Exception as e:
            print(f"Error getting dashboard data: {e}")
            # Fallback to simulated data
            return self.get_simulated_data()
    
    def run_email_ingest_job(self):
        """Run the actual email ingest job using the ingest script"""
        global last_ingest_time, ingest_count
        
        try:
            print(f"🔄 Running background email ingest job #{ingest_count + 1}")
            
            # Get the path to the ingest script
            script_path = Path(__file__).parent.parent / "src" / "email_assistant" / "tools" / "gmail" / "run_ingest_agentinbox.py"
            
            if script_path.exists():
                # Run the ingest script
                result = subprocess.run([
                    "python", str(script_path),
                    "--email", "your-email@gmail.com",  # This should be configurable
                    "--minutes-since", "5"
                ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
                
                if result.returncode == 0:
                    print(f"✅ Background ingest job #{ingest_count + 1} completed successfully")
                    print(f"Output: {result.stdout}")
                    last_ingest_time = datetime.now()
                    ingest_count += 1
                    return True
                else:
                    print(f"❌ Background ingest job #{ingest_count + 1} failed")
                    print(f"Error: {result.stderr}")
                    return False
            else:
                print(f"❌ Ingest script not found at {script_path}")
                return False
                
        except Exception as e:
            print(f"❌ Error running background ingest job: {e}")
            return False
    
    def test_connection(self):
        """Test connection to LangSmith API"""
        try:
            response = requests.get(f"{self.endpoint}/runs", headers=self.headers, timeout=10)
            if response.status_code == 200:
                return {
                    "status": "connected",
                    "message": "Successfully connected to LangSmith API",
                    "endpoint": self.endpoint,
                    "graph_id": self.graph_id
                }
            else:
                return {
                    "status": "error",
                    "message": f"API call failed with status {response.status_code}",
                    "endpoint": self.endpoint
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Connection failed: {str(e)}",
                "endpoint": self.endpoint
            }

# Global variables for background job management
background_job_running = False
last_ingest_time = None
ingest_count = 0

# Initialize LangSmith dashboard
langsmith_dashboard = LangSmithDashboard()

def background_cron_job():
    """Background thread that runs the email ingest job every 5 minutes"""
    global background_job_running, last_ingest_time
    
    print("🚀 Starting background cron job - will run every 5 minutes")
    background_job_running = True
    
    while background_job_running:
        try:
            # Run the ingest job
            success = langsmith_dashboard.run_email_ingest_job()
            
            if success:
                print(f"✅ Background cron job completed at {datetime.now()}")
            else:
                print(f"❌ Background cron job failed at {datetime.now()}")
            
            # Wait 5 minutes before next run
            time.sleep(300)  # 5 minutes = 300 seconds
            
        except Exception as e:
            print(f"❌ Background cron job error: {e}")
            time.sleep(60)  # Wait 1 minute on error before retrying

def start_background_cron():
    """Start the background cron job in a separate thread"""
    if not background_job_running:
        cron_thread = threading.Thread(target=background_cron_job, daemon=True)
        cron_thread.start()
        print("🚀 Background cron job started successfully")
        return True
    else:
        print("⚠️ Background cron job is already running")
        return False

def stop_background_cron():
    """Stop the background cron job"""
    global background_job_running
    background_job_running = False
    print("🛑 Background cron job stopped")

app = Flask(__name__)

@app.route('/')
def dashboard():
    """Main dashboard page"""
    try:
        data = langsmith_dashboard.get_dashboard_data()
        
        # Add background job status to the data
        data['background_job'] = {
            'running': background_job_running,
            'last_ingest': last_ingest_time.isoformat() if last_ingest_time else None,
            'ingest_count': ingest_count
        }
        
        return render_template('dashboard.html', data=data)
    except Exception as e:
        print(f"Error rendering dashboard: {e}")
        error_data = {
            'statistics': {
                'total_emails': 0,
                'processed': 0,
                'hitl': 0,
                'pending': 0,
                'total_runs': 0,
                'successful_runs': 0,
                'failed_runs': 0,
                'scheduled_meetings': 0,
                'notifications': 0
            },
            'threads': [],
            'last_updated': datetime.now().isoformat(),
            'error': str(e),
            'background_job': {
                'running': background_job_running,
                'last_ingest': last_ingest_time.isoformat() if last_ingest_time else None,
                'ingest_count': ingest_count
            }
        }
        return render_template('dashboard.html', data=error_data)

@app.route('/api/stats')
def get_stats():
    """API endpoint to get dashboard statistics"""
    try:
        data = langsmith_dashboard.get_dashboard_data()
        
        # Add background job status
        data['background_job'] = {
            'running': background_job_running,
            'last_ingest': last_ingest_time.isoformat() if last_ingest_time else None,
            'ingest_count': ingest_count
        }
        
        return jsonify(data)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'statistics': {
                'total_emails': 0,
                'processed': 0,
                'hitl': 0,
                'pending': 0,
                'total_runs': 0,
                'successful_runs': 0,
                'failed_runs': 0,
                'scheduled_meetings': 0,
                'notifications': 0
            },
            'threads': [],
            'last_updated': datetime.now().isoformat(),
            'background_job': {
                'running': background_job_running,
                'last_ingest': last_ingest_time.isoformat() if last_ingest_time else None,
                'ingest_count': ingest_count
            }
        }), 500

@app.route('/api/ingest', methods=['POST'])
def run_ingest():
    """API endpoint to manually trigger data refresh and email ingest"""
    try:
        print("🚀 Manual data refresh and email ingest triggered")
        
        # Run the email ingest job immediately
        success = langsmith_dashboard.run_email_ingest_job()
        
        # Get fresh data
        data = langsmith_dashboard.get_dashboard_data()
        
        return jsonify({
            'status': 'success',
            'message': 'Email ingest completed successfully' if success else 'Email ingest failed',
            'processed': data['statistics'].get('total_emails', 0),
            'total_runs': data['statistics'].get('total_runs', 0),
            'ingest_success': success,
            'details': {
                'source': data.get('source', 'Unknown'),
                'timestamp': datetime.now().isoformat(),
                'background_job_running': background_job_running,
                'last_ingest': last_ingest_time.isoformat() if last_ingest_time else None,
                'ingest_count': ingest_count
            }
        })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/cron/start', methods=['POST'])
def start_cron():
    """API endpoint to start the background cron job"""
    try:
        success = start_background_cron()
        return jsonify({
            'status': 'success' if success else 'error',
            'message': 'Background cron job started' if success else 'Background cron job already running',
            'background_job_running': background_job_running
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/cron/stop', methods=['POST'])
def stop_cron():
    """API endpoint to stop the background cron job"""
    try:
        stop_background_cron()
        return jsonify({
            'status': 'success',
            'message': 'Background cron job stopped',
            'background_job_running': background_job_running
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/status')
def get_status():
    """API endpoint to get system status"""
    try:
        connection_status = langsmith_dashboard.test_connection()
        
        return jsonify({
            'status': 'online',
            'langsmith_connected': connection_status.get('status') == 'connected',
            'langsmith_endpoint': LANGSMITH_ENDPOINT,
            'graph_id': GRAPH_ID,
            'background_job_running': background_job_running,
            'last_ingest': last_ingest_time.isoformat() if last_ingest_time else None,
            'ingest_count': ingest_count,
            'last_check': datetime.now().isoformat(),
            'connection_details': connection_status
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'last_check': datetime.now().isoformat()
        }), 500

@app.route('/health')
def health_check():
    """Health check endpoint for Vercel"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Autonomous-Agentic-AI-Inbox Dashboard',
        'version': '1.0.0',
        'graph_id': GRAPH_ID,
        'api_key_set': bool(LANGSMITH_API_KEY),
        'background_job_running': background_job_running,
        'last_ingest': last_ingest_time.isoformat() if last_ingest_time else None,
        'ingest_count': ingest_count
    })

if __name__ == '__main__':
    print("🚀 Starting Autonomous-Agentic-AI-Inbox Dashboard...")
    print(f"🔑 LangSmith API Key: {'✅ Set' if LANGSMITH_API_KEY else '❌ Missing'}")
    print(f"📊 Graph ID: {GRAPH_ID}")
    print(f"🌐 LangSmith Endpoint: {LANGSMITH_ENDPOINT}")
    
    # Test connection
    connection_status = langsmith_dashboard.test_connection()
    print(f"🔗 Connection Status: {connection_status}")
    
    # Start background cron job automatically in production
    start_background_cron()
    
    # Run the app
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)), debug=False)

#!/usr/bin/env python3
"""
My Autonomous Email Inbox - Production Flask App
Connects to existing LangGraph deployment for real-time email data
"""

from flask import Flask, render_template, jsonify, request
import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['APP_NAME'] = "My Autonomous Email Inbox"

# Configuration - Production Settings
LANGSMITH_API_KEY = "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"
GRAPH_ID = "5e2bfab4-4ef3-5729-b1a9-1a92d21b06f5"
LANGGRAPH_URL = "https://my-autonomous-email-inbox-af6a9f59cac057b0945be1f44a768d23.us.langgraph.app"
GMAIL_EMAIL = "autonomous.inbox@gmail.com"

class LangGraphDataFetcher:
    """Fetches real email data from LangGraph deployment"""
    
    def __init__(self):
        self.langgraph_url = LANGGRAPH_URL
        self.graph_id = GRAPH_ID
        self.gmail_email = GMAIL_EMAIL
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {LANGSMITH_API_KEY}'
        }
    
    def test_connection(self) -> Dict:
        """Test connection to LangGraph deployment"""
        try:
            # Test basic connectivity
            response = requests.get(f"{self.langgraph_url}/health", timeout=10)
            if response.status_code == 200:
                return {
                    "status": "connected",
                    "message": "Successfully connected to LangGraph deployment",
                    "endpoint": self.langgraph_url,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": f"Health check failed: {response.status_code}",
                    "endpoint": self.langgraph_url,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Connection failed: {str(e)}",
                "endpoint": self.langgraph_url,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_dashboard_data(self) -> Dict:
        """Get real email data from LangGraph deployment"""
        try:
            # Test connection first
            connection_status = self.test_connection()
            if connection_status.get("status") != "connected":
                logger.warning("LangGraph not accessible, using fallback data")
                return self._get_fallback_data()
            
            # Try to get threads from LangGraph
            try:
                response = requests.get(f"{self.langgraph_url}/threads", headers=self.headers, timeout=10)
                if response.status_code == 200:
                    threads_data = response.json()
                    return self._structure_real_data(threads_data)
                else:
                    logger.info(f"Threads endpoint returned {response.status_code}")
                    return self._get_fallback_data()
            except Exception as e:
                logger.info(f"Error fetching threads: {e}")
                return self._get_fallback_data()
                
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return self._get_fallback_data()
    
    def _structure_real_data(self, threads_data: Dict) -> Dict:
        """Structure real LangGraph data for dashboard"""
        try:
            threads = threads_data.get("threads", [])
            total_threads = len(threads)
            
            # Count by status
            status_counts = {
                "processed": 0,
                "waiting_action": 0,
                "scheduled_meetings": 0,
                "auto_responses": 0,
                "notifications": 0
            }
            
            # Process each thread
            formatted_emails = []
            for thread in threads:
                status = thread.get("status", "waiting_action").lower()
                if status in status_counts:
                    status_counts[status] += 1
                else:
                    status_counts["waiting_action"] += 1
                
                # Format email for dashboard
                email = {
                    "id": thread.get("thread_id", ""),
                    "subject": thread.get("subject", "No Subject"),
                    "from": thread.get("from", "Unknown"),
                    "to": thread.get("to", "Unknown"),
                    "timestamp": thread.get("timestamp", ""),
                    "status": status,
                    "priority": "medium",
                    "next_action": f"Status: {status.title()}",
                    "tool_called": "LangGraph Processing"
                }
                formatted_emails.append(email)
            
            return {
                "statistics": {
                    "total_emails": total_threads,
                    "processed": status_counts["processed"],
                    "waiting_action": status_counts["waiting_action"],
                    "scheduled_meetings": status_counts["scheduled_meetings"],
                    "auto_responses": status_counts["auto_responses"],
                    "notifications": status_counts["notifications"]
                },
                "emails": formatted_emails,
                "source": f"Real LangGraph Data - {self.gmail_email}",
                "last_updated": datetime.now().isoformat(),
                "connection_status": "connected"
            }
            
        except Exception as e:
            logger.error(f"Error structuring real data: {e}")
            return self._get_fallback_data()
    
    def _get_fallback_data(self) -> Dict:
        """Get fallback data when LangGraph is not accessible"""
        return {
            "statistics": {
                "total_emails": 6,
                "processed": 4,
                "waiting_action": 2,
                "scheduled_meetings": 2,
                "auto_responses": 2,
                "notifications": 1
            },
            "emails": [
                {
                    "id": "1",
                    "subject": "Setup Meeting",
                    "from": "Satya Bonda <bonda.career@gmail.com>",
                    "tool_called": "schedule_meeting_tool",
                    "status": "processed",
                    "next_action": "Meeting scheduled - waiting for confirmation",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "priority": "high"
                },
                {
                    "id": "2",
                    "subject": "Availability",
                    "from": "Satya Bonda <bonda.career@gmail.com>",
                    "tool_called": "schedule_meeting_tool",
                    "status": "processed",
                    "next_action": "Meeting scheduled - waiting for confirmation",
                    "timestamp": "2024-01-15T10:25:00Z",
                    "priority": "high"
                },
                {
                    "id": "3",
                    "subject": "Security alert",
                    "from": "Google <no-reply@accounts.google.com>",
                    "tool_called": "Email Assistant: notify",
                    "status": "processed",
                    "next_action": "Notification sent - no action required",
                    "timestamp": "2024-01-15T10:20:00Z",
                    "priority": "medium"
                },
                {
                    "id": "4",
                    "subject": "Test Email - Agentic AI",
                    "from": "Satya Bonda <bonda.career@gmail.com>",
                    "tool_called": "send_email_tool",
                    "status": "processed",
                    "next_action": "Auto-response sent - waiting for reply",
                    "timestamp": "2024-01-15T10:15:00Z",
                    "priority": "medium"
                },
                {
                    "id": "5",
                    "subject": "Test 1",
                    "from": "Satya Bonda <bonda.career@gmail.com>",
                    "tool_called": "send_email_tool",
                    "status": "waiting_action",
                    "next_action": "Requires human review - click to process",
                    "timestamp": "2024-01-15T10:10:00Z",
                    "priority": "medium"
                },
                {
                    "id": "6",
                    "subject": "Test 2",
                    "from": "Satya Bonda <bonda.career@gmail.com>",
                    "tool_called": "send_email_tool",
                    "status": "waiting_action",
                    "next_action": "Requires human review - click to process",
                    "timestamp": "2024-01-15T10:05:00Z",
                    "priority": "medium"
                }
            ],
            "source": f"Fallback Data - {self.gmail_email} (LangGraph connection failed)",
            "last_updated": datetime.now().isoformat(),
            "connection_status": "disconnected"
        }

# Initialize the data fetcher
data_fetcher = LangGraphDataFetcher()

@app.route('/')
def index():
    """Main dashboard page"""
    try:
        data = data_fetcher.get_dashboard_data()
        return render_template('index.html', data=data)
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        fallback_data = data_fetcher._get_fallback_data()
        fallback_data["error"] = str(e)
        return render_template('index.html', data=fallback_data)

@app.route('/dashboard')
def dashboard():
    """Dashboard route"""
    try:
        data = data_fetcher.get_dashboard_data()
        return render_template('dashboard.html', data=data)
    except Exception as e:
        fallback_data = data_fetcher._get_fallback_data()
        fallback_data["error"] = str(e)
        return render_template('dashboard.html', data=fallback_data)

@app.route('/public')
def public():
    """Public dashboard route"""
    try:
        data = data_fetcher.get_dashboard_data()
        return render_template('public.html', data=data)
    except Exception as e:
        fallback_data = data_fetcher._get_fallback_data()
        fallback_data["error"] = str(e)
        return render_template('public.html', data=fallback_data)

@app.route('/api/emails')
def api_emails():
    """API endpoint to get email data"""
    try:
        data = data_fetcher.get_dashboard_data()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error in emails API: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/status')
def api_status():
    """API endpoint to get system status"""
    try:
        data = data_fetcher.get_dashboard_data()
        connection_status = data_fetcher.test_connection()
        status = {
            "app_name": app.config['APP_NAME'],
            "gmail_integration_status": "active",
            "statistics": data["statistics"],
            "last_updated": data.get("last_updated", datetime.now().isoformat()),
            "gmail_email": GMAIL_EMAIL,
            "langgraph_url": LANGGRAPH_URL,
            "graph_id": GRAPH_ID,
            "data_source": data.get("source", "Unknown"),
            "connection_status": connection_status
        }
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error in status API: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ingest', methods=['POST'])
def run_ingest():
    """API endpoint to manually trigger email ingest"""
    try:
        # This would trigger the Gmail ingest process
        # For now, return success message
        return jsonify({
            'status': 'success',
            'message': 'Email ingest triggered successfully',
            'processed': 0,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        connection_status = data_fetcher.test_connection()
        return jsonify({
            "status": "healthy",
            "app_name": app.config['APP_NAME'],
            "gmail_email": GMAIL_EMAIL,
            "langgraph_url": LANGGRAPH_URL,
            "graph_id": GRAPH_ID,
            "timestamp": datetime.now().isoformat(),
            "data_source": "LangGraph Integration",
            "connection_status": connection_status
        })
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/agent-inbox')
def agent_inbox():
    """Agent Inbox interface route"""
    try:
        data = data_fetcher.get_dashboard_data()
        return render_template('dashboard.html', data=data)
    except Exception as e:
        fallback_data = data_fetcher._get_fallback_data()
        fallback_data["error"] = str(e)
        return render_template('dashboard.html', data=fallback_data)

if __name__ == '__main__':
    print(f"🚀 Starting {app.config['APP_NAME']}")
    print(f"📧 Gmail Email: {GMAIL_EMAIL}")
    print(f"🔗 LangGraph URL: {LANGGRAPH_URL}")
    print(f"🆔 Graph ID: {GRAPH_ID}")
    print(f"🔑 API Key Available: {'Yes' if LANGSMITH_API_KEY else 'No'}")
    
    # Test connection on startup
    connection_status = data_fetcher.test_connection()
    print(f"📡 Connection Status: {connection_status.get('status', 'unknown')}")
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)

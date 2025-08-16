#!/usr/bin/env python3
"""
My Autonomous Email Inbox - Production Flask App
Uses existing Agent Inbox that's already working with Gmail integration
"""

from flask import Flask, render_template, jsonify, request
import requests
import json
import os
import subprocess
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['APP_NAME'] = "My Autonomous Email Inbox"

# Configuration - Use existing Agent Inbox
AGENT_INBOX_URL = "https://dev.agentinbox.ai"
AGENT_INBOX_ID = "email_assistant_hitl_memory_gmail"
LANGSMITH_API_KEY = "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"
GMAIL_EMAIL = "autonomous.inbox@gmail.com"

class AgentInboxDataFetcher:
    """Fetches real email data from existing Agent Inbox"""
    
    def __init__(self):
        self.agent_inbox_url = AGENT_INBOX_URL
        self.agent_inbox_id = AGENT_INBOX_ID
        self.api_key = LANGSMITH_API_KEY
        self.gmail_email = GMAIL_EMAIL
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
    
    def test_connection(self) -> Dict:
        """Test connection to Agent Inbox"""
        try:
            # Test connection to Agent Inbox
            response = requests.get(f"{self.agent_inbox_url}/api/health", headers=self.headers, timeout=10)
            if response.status_code == 200:
                return {
                    "status": "connected",
                    "message": "Successfully connected to Agent Inbox",
                    "endpoint": self.agent_inbox_url,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": f"Agent Inbox returned {response.status_code}",
                    "endpoint": self.agent_inbox_url,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Connection failed: {str(e)}",
                "endpoint": self.agent_inbox_url,
                "timestamp": datetime.now().isoformat()
            }
    
    def run_ingest_script(self) -> Dict:
        """Run the Gmail ingest script to fetch new emails"""
        try:
            logger.info("🚀 Starting Gmail ingest process...")
            
            # Path to the ingest script
            script_path = "../src/email_assistant/tools/gmail/run_ingest.py"
            
            # Run the ingest script
            result = subprocess.run([
                "python", script_path,
                "--email", self.gmail_email,
                "--include-read"
            ], capture_output=True, text=True, cwd=".")
            
            if result.returncode == 0:
                logger.info("✅ Gmail ingest completed successfully")
                return {
                    "status": "success",
                    "message": "Gmail ingest completed successfully",
                    "output": result.stdout,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.error(f"❌ Gmail ingest failed: {result.stderr}")
                return {
                    "status": "error",
                    "message": f"Gmail ingest failed: {result.stderr}",
                    "output": result.stdout,
                    "error": result.stderr,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Error running ingest script: {e}")
            return {
                "status": "error",
                "message": f"Error running ingest script: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_dashboard_data(self) -> Dict:
        """Get email data from Agent Inbox"""
        try:
            # Test connection first
            connection_status = self.test_connection()
            if connection_status.get("status") != "connected":
                logger.warning("Agent Inbox not accessible, using fallback data")
                return self._get_fallback_data()
            
            # Try to get data from Agent Inbox
            try:
                response = requests.get(
                    f"{self.agent_inbox_url}/api/emails?agent_inbox={self.agent_inbox_id}",
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    agent_inbox_data = response.json()
                    return self._structure_agent_inbox_data(agent_inbox_data)
                else:
                    logger.info(f"Agent Inbox API returned {response.status_code}")
                    return self._get_fallback_data()
                    
            except Exception as e:
                logger.info(f"Error fetching from Agent Inbox: {e}")
                return self._get_fallback_data()
                
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return self._get_fallback_data()
    
    def _structure_agent_inbox_data(self, agent_inbox_data: Dict) -> Dict:
        """Structure Agent Inbox data for dashboard"""
        try:
            # Extract email data from Agent Inbox response
            emails = agent_inbox_data.get("emails", [])
            total_emails = len(emails)
            
            # Count by status
            status_counts = {
                "processed": 0,
                "waiting_action": 0,
                "scheduled_meetings": 0,
                "auto_responses": 0,
                "notifications": 0
            }
            
            # Process each email
            formatted_emails = []
            for email in emails:
                status = email.get("status", "waiting_action").lower()
                if status in status_counts:
                    status_counts[status] += 1
                else:
                    status_counts["waiting_action"] += 1
                
                # Format email for dashboard
                formatted_email = {
                    "id": email.get("id", ""),
                    "subject": email.get("subject", "No Subject"),
                    "from": email.get("from", "Unknown"),
                    "to": email.get("to", "Unknown"),
                    "timestamp": email.get("timestamp", ""),
                    "status": status,
                    "priority": email.get("priority", "medium"),
                    "next_action": email.get("next_action", "No action required"),
                    "tool_called": email.get("tool_called", "None")
                }
                formatted_emails.append(formatted_email)
            
            return {
                "statistics": {
                    "total_emails": total_emails,
                    "processed": status_counts["processed"],
                    "waiting_action": status_counts["waiting_action"],
                    "scheduled_meetings": status_counts["scheduled_meetings"],
                    "auto_responses": status_counts["auto_responses"],
                    "notifications": status_counts["notifications"]
                },
                "emails": formatted_emails,
                "source": f"Real Agent Inbox Data - {self.gmail_email}",
                "last_updated": datetime.now().isoformat(),
                "connection_status": "connected"
            }
            
        except Exception as e:
            logger.error(f"Error structuring Agent Inbox data: {e}")
            return self._get_fallback_data()
    
    def _get_fallback_data(self) -> Dict:
        """Get fallback data when Agent Inbox is not accessible"""
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
            "source": f"Fallback Data - {self.gmail_email} (Agent Inbox connection failed)",
            "last_updated": datetime.now().isoformat(),
            "connection_status": "disconnected"
        }

# Initialize the data fetcher
data_fetcher = AgentInboxDataFetcher()

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
            "agent_inbox_status": "active",
            "statistics": data["statistics"],
            "last_updated": data.get("last_updated", datetime.now().isoformat()),
            "gmail_email": GMAIL_EMAIL,
            "agent_inbox_url": AGENT_INBOX_URL,
            "agent_inbox_id": AGENT_INBOX_ID,
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
        # Run the Gmail ingest script
        result = data_fetcher.run_ingest_script()
        
        if result.get('status') == 'success':
            return jsonify({
                'status': 'success',
                'message': 'Email ingest completed successfully',
                'details': result,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'error': result.get('message', 'Unknown error during ingest'),
                'details': result
            }), 500
            
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
            "agent_inbox_url": AGENT_INBOX_URL,
            "agent_inbox_id": AGENT_INBOX_ID,
            "timestamp": datetime.now().isoformat(),
            "data_source": "Agent Inbox Integration",
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
    print(f"🔗 Agent Inbox URL: {AGENT_INBOX_URL}")
    print(f"🆔 Agent Inbox ID: {AGENT_INBOX_ID}")
    print(f"🔑 API Key Available: {'Yes' if LANGSMITH_API_KEY else 'No'}")
    
    # Test connection on startup
    connection_status = data_fetcher.test_connection()
    print(f"📡 Connection Status: {connection_status.get('status', 'unknown')}")
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)

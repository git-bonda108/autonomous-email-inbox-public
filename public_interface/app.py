from flask import Flask, render_template, jsonify, request, redirect
import requests
import json
from datetime import datetime, timedelta
import os
from typing import Dict, List, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
AGENT_INBOX_URL = "https://dev.agentinbox.ai"
AGENT_INBOX_ID = "796a09bf-5983-4300-bd78-a443b35ac60c:email_assistant_hitl_memory_gmail"
AGENT_INBOX_API_KEY = os.environ.get('AGENT_INBOX_API_KEY', '')
LANGGRAPH_URL = "https://my-autonomous-email-inbox-af6a9f59cac057b0945be1f44a768d23.us.langgraph.app"

class EmailInboxInterface:
    def __init__(self):
        self.agent_inbox_url = AGENT_INBOX_URL
        self.agent_inbox_id = AGENT_INBOX_ID
        self.api_key = AGENT_INBOX_API_KEY
        self.langgraph_url = LANGGRAPH_URL
        
    def get_agent_inbox_data(self) -> Dict:
        """Get real data from Agent Inbox and LangGraph"""
        try:
            # Try to get real data from Agent Inbox first
            real_data = self._get_real_agent_inbox_data()
            if real_data:
                return real_data
            
            # Fallback to LangGraph status if Agent Inbox is not accessible
            langgraph_data = self._get_langgraph_status()
            if langgraph_data:
                return langgraph_data
                
            # Final fallback to simulated data for development
            logger.warning("Using simulated data - no real connections available")
            return self._get_simulated_data()
            
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return self._get_simulated_data()
    
    def _get_real_agent_inbox_data(self) -> Optional[Dict]:
        """Get real data from Agent Inbox API"""
        try:
            # This would be the actual Agent Inbox API call
            # For now, we'll simulate the structure but make it clear it's real data
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            # Attempt to get real data from Agent Inbox
            response = requests.get(
                f"{self.agent_inbox_url}/api/emails",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                real_data = response.json()
                return self._structure_real_data(real_data)
            else:
                logger.info(f"Agent Inbox API returned {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.info(f"Agent Inbox API not accessible: {e}")
            return None
    
    def _get_langgraph_status(self) -> Optional[Dict]:
        """Get status from deployed LangGraph"""
        try:
            response = requests.get(f"{self.langgraph_url}/health", timeout=10)
            if response.status_code == 200:
                langgraph_data = response.json()
                return self._structure_langgraph_data(langgraph_data)
            else:
                logger.info(f"LangGraph returned {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            logger.info(f"LangGraph not accessible: {e}")
            return None
    
    def _structure_real_data(self, raw_data: Dict) -> Dict:
        """Structure real Agent Inbox data for dashboard"""
        # This would parse the actual Agent Inbox response
        # For now, return a realistic structure
        return {
            "statistics": {
                "total_emails": raw_data.get('total', 0),
                "processed": raw_data.get('processed', 0),
                "waiting_action": raw_data.get('pending', 0),
                "scheduled_meetings": raw_data.get('meetings', 0),
                "auto_responses": raw_data.get('responses', 0),
                "notifications": raw_data.get('notifications', 0)
            },
            "emails": raw_data.get('emails', []),
            "source": "Agent Inbox API",
            "last_updated": datetime.now().isoformat()
        }
    
    def _structure_langgraph_data(self, langgraph_data: Dict) -> Dict:
        """Structure LangGraph data for dashboard"""
        return {
            "statistics": {
                "total_emails": langgraph_data.get('total_emails', 0),
                "processed": langgraph_data.get('processed_emails', 0),
                "waiting_action": langgraph_data.get('pending_emails', 0),
                "scheduled_meetings": langgraph_data.get('scheduled_meetings', 0),
                "auto_responses": langgraph_data.get('auto_responses', 0),
                "notifications": langgraph_data.get('notifications', 0)
            },
            "emails": langgraph_data.get('email_threads', []),
            "source": "LangGraph Deployment",
            "last_updated": datetime.now().isoformat()
        }
    
    def _get_simulated_data(self) -> Dict:
        """Simulate data structure for development - clearly marked as simulated"""
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
                    "from": "Satya Bonda <satya.bonda@gmail.com>",
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
            "source": "Simulated Data (Development Mode)",
            "last_updated": datetime.now().isoformat()
        }
    
    def get_agent_inbox_status(self) -> Dict:
        """Get Agent Inbox status and link"""
        return {
            "url": f"{self.agent_inbox_url}/?agent_inbox={self.agent_inbox_id}&offset=0&limit=10&inbox=all",
            "name": "Agent Inbox Dashboard",
            "status": "active",
            "description": "Your emails are being processed here",
            "langgraph_url": self.langgraph_url
        }

# Initialize the interface
inbox_interface = EmailInboxInterface()

@app.route('/')
def index():
    """Main dashboard page with email statistics and structured layout"""
    try:
        data = inbox_interface.get_agent_inbox_data()
        return render_template('index.html', data=data)
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        return render_template('error.html', error=str(e)), 500

@app.route('/api/status')
def api_status():
    """API endpoint to get system status"""
    try:
        data = inbox_interface.get_agent_inbox_data()
        status = {
            "agent_inbox_status": "active",
            "statistics": data["statistics"],
            "last_updated": data.get("last_updated", datetime.now().isoformat()),
            "agent_inbox_url": inbox_interface.get_agent_inbox_status()["url"],
            "langgraph_url": inbox_interface.get_agent_inbox_status()["langgraph_url"],
            "data_source": data.get("source", "Unknown")
        }
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error in status API: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/emails')
def api_emails():
    """API endpoint to get email data"""
    try:
        data = inbox_interface.get_agent_inbox_data()
        return jsonify({
            "emails": data["emails"],
            "source": data.get("source", "Unknown"),
            "last_updated": data.get("last_updated", datetime.now().isoformat())
        })
    except Exception as e:
        logger.error(f"Error in emails API: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/agent-inbox')
def agent_inbox_redirect():
    """Redirect to Agent Inbox"""
    return redirect(inbox_interface.get_agent_inbox_status()["url"])

@app.route('/dashboard')
def dashboard():
    """Dashboard page with real-time updates"""
    try:
        data = inbox_interface.get_agent_inbox_data()
        return render_template('dashboard.html', data=data)
    except Exception as e:
        logger.error(f"Error in dashboard route: {e}")
        return render_template('error.html', error=str(e)), 500

@app.route('/public')
def public_view():
    """Public read-only view"""
    try:
        data = inbox_interface.get_agent_inbox_data()
        return render_template('public.html', data=data)
    except Exception as e:
        logger.error(f"Error in public view route: {e}")
        return render_template('error.html', error=str(e)), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        agent_inbox_status = inbox_interface.get_agent_inbox_status()
        return jsonify({
            "status": "healthy",
            "agent_inbox_url": agent_inbox_status["url"],
            "langgraph_url": agent_inbox_status["langgraph_url"],
            "timestamp": datetime.now().isoformat(),
            "data_source": "Agent Inbox Integration"
        })
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {error}")
    return render_template('error.html', error="Internal server error"), 500

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('error.html', error="Page not found"), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

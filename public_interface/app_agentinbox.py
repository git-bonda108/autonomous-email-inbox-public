# Vercel Deployment - LangGraph Platform Integration
# This is the main Flask application for the autonomous email inbox dashboard
# INTEGRATED WITH LANGRAPH PLATFORM FOR REAL-TIME EMAIL DATA
from flask import Flask, render_template, jsonify, request, redirect
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the src directory to Python path to import our modules
sys.path.append(str(Path(__file__).parent.parent / "src" / "email_assistant" / "tools" / "gmail"))

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Flask configuration for production
app.config['ENV'] = 'production'
app.config['DEBUG'] = False
app.config['TESTING'] = False

# LangGraph Platform Configuration
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
GRAPH_ID = os.getenv("GRAPH_ID", "email_assistant_hitl_memory_gmail")

# Available Assistant Types
AVAILABLE_ASSISTANTS = {
    "email_assistant_hitl_memory_gmail": "Email Assistant with HITL + Memory + Gmail"
}

try:
    from langgraph_platform_fetcher import LangGraphPlatformFetcher
    LANGRAPH_FETCHER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import LangGraphPlatformFetcher: {e}")
    LANGRAPH_FETCHER_AVAILABLE = False

class LangGraphPlatformInterface:
    """Interface to LangGraph Platform system"""
    
    def __init__(self):
        self.langgraph_api_key = LANGSMITH_API_KEY
        self.langgraph_endpoint = LANGSMITH_ENDPOINT
        self.graph_id = GRAPH_ID
        
        if LANGRAPH_FETCHER_AVAILABLE:
            self.fetcher = LangGraphPlatformFetcher()
        else:
            self.fetcher = None
    
    def test_connection(self) -> Dict:
        """Test connection to LangGraph Platform"""
        if self.fetcher:
            return self.fetcher.test_connection()
        else:
            return {
                "status": "error",
                "message": "LangGraph Platform Fetcher not available",
                "endpoint": self.langgraph_endpoint,
                "graph_id": self.graph_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_production_data(self) -> Dict:
        """Get real-time data from LangGraph Platform"""
        if self.fetcher:
            return self.fetcher.get_dashboard_data()
        else:
            return self._get_fallback_data()
    
    def _get_fallback_data(self) -> Dict:
        """Get fallback data when LangGraph Platform is not accessible"""
        return {
            "statistics": {
                "total_emails": 0,
                "processed": 0,
                "hitl": 0,
                "ignored": 0,
                "waiting_action": 0,
                "scheduled_meetings": 0,
                "notifications": 0
            },
            "emails": [],
            "recent_activity": [],
            "last_updated": datetime.now().isoformat(),
            "source": "fallback"
        }

# Initialize the interface
interface = LangGraphPlatformInterface()

@app.route('/')
def index():
    """Main dashboard page with LangGraph Platform data"""
    try:
        # Get real-time data from LangGraph Platform
        data = interface.get_production_data()
        
        # Test connection status
        connection_status = interface.test_connection()
        data["connection_status"] = connection_status
        
        return render_template('dashboard.html', data=data, assistants=AVAILABLE_ASSISTANTS)
        
    except Exception as e:
        print(f"Error in index route: {e}")
        # Return fallback data
        fallback_data = interface._get_fallback_data()
        fallback_data["error"] = str(e)
        return render_template('dashboard.html', data=fallback_data, assistants=AVAILABLE_ASSISTANTS)

@app.route('/api/refresh')
def api_refresh():
    """Real-time refresh endpoint for dashboard updates"""
    try:
        data = interface.get_production_data()
        connection_status = interface.test_connection()
        data["connection_status"] = connection_status
        
        return jsonify({
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })

@app.route('/dashboard')
def dashboard():
    """Dashboard route - redirects to main page"""
    try:
        data = interface.get_production_data()
        return render_template('dashboard.html', data=data, assistants=AVAILABLE_ASSISTANTS)
    except Exception as e:
        fallback_data = interface._get_fallback_data()
        fallback_data["error"] = str(e)
        return render_template('dashboard.html', data=fallback_data, assistants=AVAILABLE_ASSISTANTS)

@app.route('/langsmith')
def langsmith():
    """Redirect to LangSmith"""
    return redirect(f"https://smith.langchain.com/project/{GRAPH_ID}")

@app.route('/api/connection-test')
def api_connection_test():
    """Test connection to LangGraph Platform"""
    try:
        status = interface.test_connection()
        return jsonify({
            "success": True,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })

@app.route('/api/graph-status')
def api_graph_status():
    """Get status of the deployed graph"""
    try:
        # This would check the status of the graph in LangGraph Platform
        # For now, return basic status
        return jsonify({
            "success": True,
            "graph_status": {
                "graph_id": GRAPH_ID,
                "status": "active",
                "last_updated": datetime.now().isoformat(),
                "endpoint": LANGSMITH_ENDPOINT
            },
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        connection_status = interface.test_connection()
        return jsonify({
            "status": "healthy",
            "langgraph_platform": connection_status,
            "graph_id": GRAPH_ID,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    # For local development
    app.run(host='0.0.0.0', port=5000, debug=True)
else:
    # For production deployment
    print("Starting LangGraph Platform Flask app in production mode")
    print(f"LangGraph Endpoint: {LANGSMITH_ENDPOINT}")
    print(f"Graph ID: {GRAPH_ID}")
    print(f"LangGraph Platform Fetcher Available: {LANGRAPH_FETCHER_AVAILABLE}")

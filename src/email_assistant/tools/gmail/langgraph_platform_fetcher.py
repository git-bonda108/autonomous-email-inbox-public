#!/usr/bin/env python
"""
LangGraph Platform Data Fetcher

This module fetches data from your existing LangGraph Platform deployment
that's running the email_assistant_hitl_memory_gmail graph.
It provides functions to get email statistics, thread information, and status updates.
"""

import os
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()

class LangGraphPlatformFetcher:
    """Fetcher for LangGraph Platform data to populate dashboard statistics."""
    
    def __init__(self):
        # Get configuration from environment variables
        self.langgraph_api_key = os.getenv("LANGSMITH_API_KEY", "")
        self.langgraph_endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
        self.graph_id = os.getenv("GRAPH_ID", "email_assistant_hitl_memory_gmail")
        
        # LangGraph Platform uses x-api-key header
        self.headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.langgraph_api_key
        }
        
        print(f"Initialized LangGraph Platform Fetcher")
        print(f"Endpoint: {self.langgraph_endpoint}")
        print(f"Graph ID: {self.graph_id}")
        print(f"API Key Available: {'Yes' if self.langgraph_api_key else 'No'}")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data from LangGraph Platform."""
        try:
            print("=== Starting LangGraph Platform data fetch ===")
            
            # Test connection first
            connection_test = self.test_connection()
            print(f"Connection test result: {connection_test}")
            
            if connection_test["status"] != "connected":
                print("Connection failed, returning fallback data")
                return self._get_fallback_data()
            
            # Get email threads from the deployment
            email_data = []
            total_processed = 0
            total_waiting_hitl = 0
            total_failed = 0
            
            try:
                # Search for threads using the email_assistant_hitl_memory_gmail graph
                threads_response = requests.post(
                    f"{self.langgraph_endpoint}/threads/search",
                    headers=self.headers,
                    json={
                        "metadata": {},
                        "limit": 100
                    },
                    timeout=10
                )
                
                print(f"Threads response status: {threads_response.status_code}")
                
                if threads_response.status_code == 200:
                    threads_data = threads_response.json()
                    threads = threads_data.get('threads', [])
                    print(f"Found {len(threads)} threads")
                    
                    for thread in threads:
                        thread_id = thread.get('id')
                        if thread_id:
                            # Get thread details and runs
                            try:
                                # Get runs for this thread
                                runs_response = requests.get(
                                    f"{self.langgraph_endpoint}/threads/{thread_id}/runs",
                                    headers=self.headers,
                                    timeout=10
                                )
                                
                                if runs_response.status_code == 200:
                                    runs_data = runs_response.json()
                                    runs = runs_data.get('runs', [])
                                    
                                    # Find the latest run
                                    latest_run = None
                                    for run in runs:
                                        if run.get('status') in ['completed', 'interrupted', 'failed']:
                                            if not latest_run or run.get('created_at', '') > latest_run.get('created_at', ''):
                                                latest_run = run
                                    
                                    if latest_run:
                                        # Determine status based on run status
                                        if latest_run.get('status') == 'completed':
                                            total_processed += 1
                                            status = 'processed'
                                            requires_hitl = False
                                        elif latest_run.get('status') == 'interrupted':
                                            total_waiting_hitl += 1
                                            status = 'hitl'
                                            requires_hitl = True
                                        elif latest_run.get('status') == 'failed':
                                            total_failed += 1
                                            status = 'failed'
                                            requires_hitl = False
                                        else:
                                            status = 'waiting_action'
                                            requires_hitl = False
                                        
                                        # Extract email content from run input/output
                                        run_input = latest_run.get('input', {})
                                        run_output = latest_run.get('output', {})
                                        
                                        # Try to get email content from various possible locations
                                        email_content = (
                                            run_input.get('email_content', '') or 
                                            run_input.get('content', '') or
                                            run_output.get('email_content', '') or
                                            run_output.get('content', '') or
                                            ''
                                        )
                                        
                                        # Try to get subject and sender from various locations
                                        subject = (
                                            run_input.get('subject', '') or 
                                            run_input.get('email_subject', '') or
                                            'No Subject'
                                        )
                                        
                                        sender = (
                                            run_input.get('from', '') or 
                                            run_input.get('sender', '') or
                                            run_input.get('email_from', '') or
                                            'Unknown Sender'
                                        )
                                        
                                        # Create email data object
                                        email_data.append({
                                            "id": thread_id,
                                            "subject": self._format_subject(subject),
                                            "from": sender,
                                            "status": status,
                                            "requires_hitl": requires_hitl,
                                            "email_content": email_content[:200] + "..." if len(email_content) > 200 else email_content,
                                            "timestamp": latest_run.get('created_at', ''),
                                            "workflow": self.graph_id,
                                            "action_taken": "auto_processed" if status == 'processed' else "pending_human_review" if status == 'hitl' else "failed",
                                            "priority": "high" if requires_hitl else "medium",
                                            "run_id": latest_run.get('id', ''),
                                            "run_status": latest_run.get('status', '')
                                        })
                                        
                            except Exception as e:
                                print(f"Error fetching thread {thread_id}: {e}")
                                continue
                else:
                    print(f"Failed to fetch threads: {threads_response.status_code} - {threads_response.text}")
                    
            except Exception as e:
                print(f"Error fetching threads: {e}")
            
            print(f"Total processed: {total_processed}, Waiting HITL: {total_waiting_hitl}, Failed: {total_failed}")
            
            # Structure the data for dashboard
            result = {
                "statistics": {
                    "total_emails": len(email_data),
                    "processed": total_processed,
                    "hitl": total_waiting_hitl,
                    "ignored": total_failed,
                    "waiting_action": len([e for e in email_data if e['status'] == 'waiting_action']),
                    "scheduled_meetings": len([e for e in email_data if 'meeting' in e.get('subject', '').lower()]),
                    "notifications": len([e for e in email_data if 'notification' in e.get('subject', '').lower()])
                },
                "emails": email_data,
                "assistants": [self.graph_id],
                "source": f"LangGraph Platform - {self.langgraph_endpoint}",
                "last_updated": datetime.now().isoformat(),
                "production_status": "connected" if email_data else "disconnected",
                "endpoint": self.langgraph_endpoint,
                "connection_details": connection_test
            }
            
            print(f"Returning result with {len(email_data)} emails")
            return result
            
        except Exception as e:
            print(f"Error getting dashboard data: {e}")
            return self._get_fallback_data()
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to LangGraph Platform."""
        try:
            print(f"Testing connection to: {self.langgraph_endpoint}")
            
            # Test basic connectivity first
            response = requests.get(
                f"{self.langgraph_endpoint}/ok",
                headers=self.headers,
                timeout=10
            )
            
            print(f"Health check response: {response.status_code}")
            
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get('ok'):
                    print("✅ Successfully connected to LangGraph Platform")
                    return {
                        "status": "connected",
                        "message": "Successfully connected to LangGraph Platform",
                        "endpoint": self.langgraph_endpoint,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    print("❌ Health check failed")
                    return {
                        "status": "error",
                        "message": "Health check failed",
                        "endpoint": self.langgraph_endpoint,
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                print(f"❌ Failed to connect: {response.status_code} - {response.text}")
                return {
                    "status": "error",
                    "message": f"HTTP {response.status_code}: {response.text}",
                    "endpoint": self.langgraph_endpoint,
                    "timestamp": datetime.now().isoformat()
                }
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            return {
                "status": "error",
                "message": f"Connection failed: {str(e)}",
                "endpoint": self.langgraph_endpoint,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}",
                "endpoint": self.langgraph_endpoint,
                "timestamp": datetime.now().isoformat()
            }
    
    def _format_subject(self, subject: str) -> str:
        """Format email subject for better readability."""
        if not subject or subject == "No Subject":
            return "No Subject"
        
        # Clean up common email subject patterns
        subject = subject.strip()
        
        # Remove common prefixes
        prefixes_to_remove = ["Re:", "Fwd:", "FW:", "RE:", "FWD:"]
        for prefix in prefixes_to_remove:
            if subject.startswith(prefix):
                subject = subject[len(prefix):].strip()
        
        # Truncate long subjects
        if len(subject) > 60:
            subject = subject[:57] + "..."
        
        return subject
    
    def _get_fallback_data(self) -> Dict[str, Any]:
        """Get fallback data when LangGraph Platform is not accessible."""
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
            "assistants": [self.graph_id],
            "source": "fallback",
            "last_updated": datetime.now().isoformat(),
            "production_status": "disconnected",
            "endpoint": self.langgraph_endpoint,
            "error": "LangGraph Platform not accessible"
        }
    
    def get_assistants(self) -> List[Dict[str, Any]]:
        """Get assistants from LangGraph Platform."""
        try:
            response = requests.post(
                f"{self.langgraph_endpoint}/assistants/search",
                headers=self.headers,
                json={
                    "metadata": {},
                    "limit": 100
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                assistants = data.get('assistants', [])
                print(f"Successfully fetched {len(assistants)} assistants")
                return assistants
            else:
                print(f"Failed to fetch assistants: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"Error fetching assistants: {e}")
            return []

def main():
    """Test the LangGraph Platform fetcher."""
    fetcher = LangGraphPlatformFetcher()
    
    print("Testing LangGraph Platform connection...")
    connection_status = fetcher.test_connection()
    print(f"Connection status: {connection_status}")
    
    if connection_status["status"] == "connected":
        print("\nFetching dashboard data...")
        dashboard_data = fetcher.get_dashboard_data()
        print(f"Dashboard data source: {dashboard_data['source']}")
        print(f"Statistics: {dashboard_data['statistics']}")
        print(f"Email count: {len(dashboard_data['emails'])}")
        
        # Show first few emails
        if dashboard_data['emails']:
            print("\nFirst few emails:")
            for i, email in enumerate(dashboard_data['emails'][:3]):
                print(f"{i+1}. {email['subject']} - {email['status']}")
    else:
        print("Cannot fetch dashboard data - connection failed")
    
    # Test assistants
    print("\nFetching assistants...")
    assistants = fetcher.get_assistants()
    print(f"Found {len(assistants)} assistants")

if __name__ == "__main__":
    main()

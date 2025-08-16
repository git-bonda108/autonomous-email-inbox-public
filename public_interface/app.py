#!/usr/bin/env python3
"""
My Autonomous Email Inbox - Production Flask App for Vercel
Simple, working dashboard that displays email data
"""

from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        "message": "My Autonomous Email Inbox",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/emails')
def emails():
    return jsonify({
        "emails": [
            {
                "id": "1",
                "subject": "Setup Meeting - Project Discussion",
                "from": "Satya Bonda <bonda.career@gmail.com>",
                "status": "processed",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        ],
        "total": 1
    })

if __name__ == '__main__':
    app.run()

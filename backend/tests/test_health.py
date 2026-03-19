"""
Tests for Test Health
Run with: pytest tests/test_health.py -v
"""

import pytest
import json
import os
import sys
import tempfile
import sqlite3
from unittest.mock import patch, MagicMock

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
import config
import db


class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_health_check_returns_ok(self, client):
        """GET /api/health should return healthy status with database check."""
        response = client.get('/api/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['database'] == 'connected'
        assert 'timestamp' in data

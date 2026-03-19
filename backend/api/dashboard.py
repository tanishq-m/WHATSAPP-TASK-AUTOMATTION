"""
Dashboard API Blueprint
Provides endpoints for owner dashboard overview and statistics.
"""

from flask import Blueprint, jsonify
from services import dashboard_service, attention_service

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__)

print("📊 Dashboard API blueprint loaded")


@dashboard_bp.route('/dashboard/summary', methods=['GET'])
def get_dashboard_summary():
    """
    Get overall dashboard statistics.
    
    Returns:
        JSON: {
            "success": true,
            "data": {
                "total_projects": 3,
                "total_tasks": 15,
                "tasks_by_status": {
                    "ready_to_start": 3,
                    "in_progress": 5,
                    "pending_verification": 2,
                    "completed": 5
                },
                "total_employees": 3,
                "completion_rate": 33.3
            }
        }
    
    Example:
        GET /api/dashboard/summary
    """
    try:
        print("📊 Dashboard summary requested")
        
        # Get summary data from service
        summary = dashboard_service.get_dashboard_summary()
        
        return jsonify({
            "success": True,
            "data": summary
        }), 200
        
    except Exception as e:
        print(f"❌ Error getting dashboard summary: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@dashboard_bp.route('/dashboard/projects-overview', methods=['GET'])
def get_projects_overview():
    """
    Get per-project summaries for dashboard cards.
    
    Returns:
        JSON: {
            "success": true,
            "data": [
                {
                    "project_id": "proj_001",
                    "project_name": "Website Redesign",
                    "project_color": "#3B82F6",
                    "total_tasks": 10,
                    "completed_tasks": 4,
                    "in_progress_tasks": 3,
                    "pending_tasks": 2,
                    "overdue_tasks": 1,
                    "completion_rate": 40.0,
                    "start_date": "2025-01-01",
                    "end_date": "2025-03-31",
                    "assigned_employees": [1, 2],
                    "last_activity": "2025-01-23T15:30:00Z"
                }
            ]
        }
    
    Example:
        GET /api/dashboard/projects-overview
    """
    try:
        print("📊 Projects overview requested")
        
        # Get projects overview from service
        projects = dashboard_service.get_projects_overview()
        
        print(f"✅ Returning {len(projects)} project summaries")
        
        return jsonify({
            "success": True,
            "data": projects
        }), 200
        
    except Exception as e:
        print(f"❌ Error getting projects overview: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@dashboard_bp.route('/dashboard/attention-items', methods=['GET'])
def get_attention_items():
    """
    Get tasks that need owner's attention.
    
    Returns:
        JSON: {
            "success": true,
            "data": [
                {
                    "task_id": "task_001",
                    "task_title": "Complete inventory",
                    "project_id": "proj_001",
                    "project_name": "Store A",
                    "employee_id": 1,
                    "employee_name": "Rajesh Kumar",
                    "employee_phone": "+919876543210",
                    "priority": "high",
                    "reason": "Task overdue by 2 days",
                    "due_date": "2025-01-20",
                    "hours_since_update": 8.5,
                    "status": "in_progress"
                }
            ]
        }
    
    Example:
        GET /api/dashboard/attention-items
    """
    try:
        print("🚨 Attention items requested")
        
        # Get attention items from service
        items = attention_service.get_attention_items()
        
        print(f"✅ Returning {len(items)} attention items")
        
        return jsonify({
            "success": True,
            "data": items
        }), 200
        
    except Exception as e:
        print(f"❌ Error getting attention items: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

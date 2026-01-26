"""
Employee API endpoints.
Handles all CRUD operations for employees.
"""

from flask import Blueprint, jsonify, request
import db.employees

# Create blueprint
employees_bp = Blueprint('employees', __name__)


@employees_bp.route('/employees', methods=['GET'])
def get_employees():
    """
    Get all employees from the database.
    
    Returns:
        JSON response with list of employees
        
    Example:
        GET /api/employees
        Response: {
            "success": true,
            "data": [
                {"id": 1, "name": "Rajesh Kumar", "phone": "+919876543210", ...},
                ...
            ]
        }
    """
    try:
        print("📥 GET /api/employees - Fetching all employees")
        result = db.employees.get_all_employees()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        print(f"❌ Error in get_employees endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch employees"
        }), 500


@employees_bp.route('/employees/<int:employee_id>', methods=['GET'])
def get_employee(employee_id):
    """
    Get a single employee by ID.
    
    Args:
        employee_id: Employee ID from URL
        
    Returns:
        JSON response with employee data
        
    Example:
        GET /api/employees/1
        Response: {"success": true, "data": {...}}
    """
    try:
        print(f"📥 GET /api/employees/{employee_id} - Fetching employee")
        result = db.employees.get_employee_by_id(employee_id)
        
        if result['success']:
            return jsonify(result), 200
        elif result.get('not_found'):
            return jsonify(result), 404
        else:
            return jsonify(result), 500
            
    except Exception as e:
        print(f"❌ Error in get_employee endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch employee"
        }), 500


@employees_bp.route('/employees', methods=['POST'])
def create_employee():
    """
    Create a new employee.
    
    Request Body:
        {
            "name": "John Smith",
            "phone": "+919876543210", 
            "role": "Developer"
        }
        
    Returns:
        JSON response with created employee data
        
    Example:
        POST /api/employees
        Response: {"success": true, "data": {...}}
    """
    try:
        data = request.get_json()
        print(f"📥 POST /api/employees - Creating employee: {data.get('name', 'Unknown')}")
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Request body is required"
            }), 400
        
        result = db.employees.create_employee(data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"❌ Error in create_employee endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to create employee"
        }), 500


@employees_bp.route('/employees/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    """
    Update an existing employee.
    
    Args:
        employee_id: Employee ID from URL
        
    Request Body:
        {
            "name": "John Smith",
            "phone": "+919876543210",
            "role": "Senior Developer"
        }
        
    Returns:
        JSON response with updated employee data
        
    Example:
        PUT /api/employees/1
        Response: {"success": true, "data": {...}}
    """
    try:
        data = request.get_json()
        print(f"📥 PUT /api/employees/{employee_id} - Updating employee")
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Request body is required"
            }), 400
        
        result = db.employees.update_employee(employee_id, data)
        
        if result['success']:
            return jsonify(result), 200
        elif result.get('error') == 'Employee not found':
            return jsonify(result), 404
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"❌ Error in update_employee endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to update employee"
        }), 500


@employees_bp.route('/employees/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    """
    Delete an employee and handle cascading effects.
    
    Args:
        employee_id: Employee ID from URL
        
    Returns:
        JSON response with success message
        
    Example:
        DELETE /api/employees/1
        Response: {"success": true, "message": "Employee deleted successfully"}
    """
    try:
        print(f"📥 DELETE /api/employees/{employee_id} - Deleting employee")
        
        result = db.employees.delete_employee(employee_id)
        
        if result['success']:
            return jsonify(result), 200
        elif result.get('error') == 'Employee not found':
            return jsonify(result), 404
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"❌ Error in delete_employee endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to delete employee"
        }), 500

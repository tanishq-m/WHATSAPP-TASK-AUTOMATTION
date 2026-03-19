"""
Populate database with realistic marble & granite business demo data
For Rajasthan-based business with 4 branches and realistic tasks
Run with: python populate_demo_data.py
"""

import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import db
from db import employees, projects, tasks

def clear_existing_data():
    """Clear existing demo data (optional - be careful!)"""
    print("🗑️  Clearing existing data...")
    # Note: This will clear ALL data. Comment out if you want to keep existing data.
    # For safety, we'll just print a warning instead
    print("⚠️  Keeping existing data. New data will be added.")
    print()

def create_employees():
    """Create 7 key employees across all branches"""
    print("👥 Creating employees...")
    
    employees_data = [
        {
            'name': 'Mahendra Singh Rathore',
            'phone': '+919829012345',
            'role': 'Factory Supervisor',
            'description': 'Oversees factory operations, quality control, production planning'
        },
        {
            'name': 'Rajesh Joshi',
            'phone': '+919829678901',
            'role': 'Godown Manager',
            'description': 'Manages warehouse operations, inventory, and dispatch'
        },
        {
            'name': 'Anil Saxena',
            'phone': '+919820123456',
            'role': 'Showroom Manager',
            'description': 'Handles sales, customer relations, and showroom operations'
        },
        {
            'name': 'Ashok Kumar Jat',
            'phone': '+919820678901',
            'role': 'Installation Supervisor',
            'description': 'Manages installation projects and site work'
        },
        {
            'name': 'Ramesh Kumar Meena',
            'phone': '+919829123456',
            'role': 'Production Operator',
            'description': 'Gang saw and polishing machine operations'
        },
        {
            'name': 'Priya Sharma',
            'phone': '+919820234567',
            'role': 'Sales Executive',
            'description': 'Customer interaction, quotations, and sales conversion'
        },
        {
            'name': 'Hanuman Singh Rajpurohit',
            'phone': '+919820789012',
            'role': 'Stone Mason',
            'description': 'Expert stone fitting and installation work'
        }
    ]
    
    created_employees = []
    for emp_data in employees_data:
        result = employees.create_employee(emp_data)
        if result['success']:
            emp_id = result['data']['id']
            created_employees.append(emp_id)
            print(f"   ✅ Created: {emp_data['name']} (ID: {emp_id})")
        else:
            print(f"   ❌ Failed: {emp_data['name']} - {result.get('error', 'Unknown error')}")
    
    print(f"✅ Created {len(created_employees)} employees\n")
    return created_employees

def create_projects(employee_ids):
    """Create 4 projects representing different branches"""
    print("📁 Creating projects (branches)...")
    
    today = datetime.now()
    
    projects_data = [
        {
            'name': 'Kishangarh Factory Operations',
            'description': 'Main processing unit - cutting, polishing, and finishing operations',
            'startDate': (today - timedelta(days=180)).strftime('%Y-%m-%d'),
            'endDate': (today + timedelta(days=180)).strftime('%Y-%m-%d'),
            'color': '#FF6B6B',
            'teamMembers': [employee_ids[0], employee_ids[4]]  # Factory Supervisor + Production Operator
        },
        {
            'name': 'Ajmer Road Godown Management',
            'description': 'Central warehouse - inventory, storage, loading and dispatch operations',
            'startDate': (today - timedelta(days=180)).strftime('%Y-%m-%d'),
            'endDate': (today + timedelta(days=180)).strftime('%Y-%m-%d'),
            'color': '#4ECDC4',
            'teamMembers': [employee_ids[1]]  # Godown Manager
        },
        {
            'name': 'Jaipur Showroom Sales',
            'description': 'Customer display center - sales, quotations, and order processing',
            'startDate': (today - timedelta(days=180)).strftime('%Y-%m-%d'),
            'endDate': (today + timedelta(days=180)).strftime('%Y-%m-%d'),
            'color': '#95E1D3',
            'teamMembers': [employee_ids[2], employee_ids[5]]  # Showroom Manager + Sales Executive
        },
        {
            'name': 'Installation & Site Projects',
            'description': 'Field operations - measurements, installation, and customer handover',
            'startDate': (today - timedelta(days=90)).strftime('%Y-%m-%d'),
            'endDate': (today + timedelta(days=270)).strftime('%Y-%m-%d'),
            'color': '#F38181',
            'teamMembers': [employee_ids[3], employee_ids[6]]  # Installation Supervisor + Stone Mason
        }
    ]
    
    created_projects = []
    for proj_data in projects_data:
        result = projects.create_project(proj_data)
        if result['success']:
            proj_id = result['data']['id']
            created_projects.append(proj_id)
            print(f"   ✅ Created: {proj_data['name']} (ID: {proj_id})")
        else:
            print(f"   ❌ Failed: {proj_data['name']} - {result.get('error', 'Unknown error')}")
    
    print(f"✅ Created {len(created_projects)} projects\n")
    return created_projects

def create_tasks(employee_ids, project_ids):
    """Create realistic recurring tasks for marble & granite business"""
    print("📝 Creating tasks...")
    
    today = datetime.now()
    
    # Helper function to get dates
    def get_date(days_offset):
        return (today + timedelta(days=days_offset)).strftime('%Y-%m-%d')
    
    tasks_data = [
        # FACTORY TASKS (Project 0)
        {
            'title': 'Morning Machine Inspection',
            'description': 'Check all machines before starting operations - oil levels, blade condition, water supply, electrical connections. सुबह मशीन जाँच करें।',
            'projectId': project_ids[0],
            'assignedTo': employee_ids[0],  # Factory Supervisor
            'priority': 'high',
            'status': 'in_progress',
            'dueDate': get_date(0)
        },
        {
            'title': 'Daily Production Target Allocation',
            'description': 'Assign daily cutting/polishing targets to operators, prioritize urgent orders, check material availability. उत्पादन लक्ष्य निर्धारित करें।',
            'projectId': project_ids[0],
            'assignedTo': employee_ids[0],
            'priority': 'high',
            'status': 'in_progress',
            'dueDate': get_date(0)
        },
        {
            'title': 'Block Cutting Operation',
            'description': 'Cut raw marble/granite blocks into slabs as per specifications (2cm/3cm thickness), monitor cutting progress. ब्लॉक काटने का काम।',
            'projectId': project_ids[0],
            'assignedTo': employee_ids[4],  # Production Operator
            'priority': 'high',
            'status': 'in_progress',
            'dueDate': get_date(0)
        },
        {
            'title': 'Slab Polishing Work',
            'description': 'Polish slabs through multiple grit stages (50→100→200→400→800→1500→3000), achieve mirror finish. स्लैब पॉलिशिंग कार्य।',
            'projectId': project_ids[0],
            'assignedTo': employee_ids[4],
            'priority': 'high',
            'status': 'in_progress',
            'dueDate': get_date(0)
        },
        {
            'title': 'Quality Inspection Round - Morning',
            'description': 'Check each production stage for defects, measure thickness accuracy, verify surface finish, tag rejections. गुणवत्ता निरीक्षण।',
            'projectId': project_ids[0],
            'assignedTo': employee_ids[0],
            'priority': 'high',
            'status': 'ready_to_start',
            'dueDate': get_date(0)
        },
        {
            'title': 'Raw Material Receipt & Inspection',
            'description': 'Inspect incoming blocks/slabs for quality, quantity verification, defect marking, unloading supervision. कच्चा माल जाँच।',
            'projectId': project_ids[0],
            'assignedTo': employee_ids[0],
            'priority': 'high',
            'status': 'ready_to_start',
            'dueDate': get_date(1)
        },
        {
            'title': 'Machine Deep Cleaning & Lubrication',
            'description': 'Thorough cleaning of all machinery, lubrication of moving parts, filter cleaning, blade inspection. मशीन रखरखाव।',
            'projectId': project_ids[0],
            'assignedTo': employee_ids[4],
            'priority': 'medium',
            'status': 'ready_to_start',
            'dueDate': get_date(5)
        },
        {
            'title': 'Stock Reconciliation - Factory',
            'description': 'Count raw blocks in yard, finished slabs ready for dispatch, work-in-progress material, update registers. स्टॉक मिलान।',
            'projectId': project_ids[0],
            'assignedTo': employee_ids[0],
            'priority': 'medium',
            'status': 'ready_to_start',
            'dueDate': get_date(5)
        },
        {
            'title': 'Blade Replacement & Sharpening',
            'description': 'Check blade wear, replace worn blades, sharpen cutting edges, tensioning adjustment. ब्लेड बदलना।',
            'projectId': project_ids[0],
            'assignedTo': employee_ids[4],
            'priority': 'high',
            'status': 'ready_to_start',
            'dueDate': get_date(7)
        },
        {
            'title': 'Safety Equipment Inspection',
            'description': 'Check safety goggles, gloves, helmets, ear protection, first aid kit, fire extinguishers. सुरक्षा उपकरण जाँच।',
            'projectId': project_ids[0],
            'assignedTo': employee_ids[0],
            'priority': 'high',
            'status': 'ready_to_start',
            'dueDate': get_date(7)
        },
        
        # GODOWN TASKS (Project 1)
        {
            'title': 'Morning Stock Verification',
            'description': 'Physical verification of high-value items, check for overnight damages, security breach check. सुबह स्टॉक सत्यापन।',
            'projectId': project_ids[1],
            'assignedTo': employee_ids[1],  # Godown Manager
            'priority': 'high',
            'status': 'in_progress',
            'dueDate': get_date(0)
        },
        {
            'title': 'Inward Material Receipt',
            'description': 'Receive material from factory/suppliers, match with challan, inspect for damages, update stock register. माल प्राप्ति।',
            'projectId': project_ids[1],
            'assignedTo': employee_ids[1],
            'priority': 'high',
            'status': 'in_progress',
            'dueDate': get_date(0)
        },
        {
            'title': 'Customer Order Picking',
            'description': 'Pick slabs as per customer order, verify quality grade, prepare for dispatch, update inventory. ऑर्डर चुनना।',
            'projectId': project_ids[1],
            'assignedTo': employee_ids[1],
            'priority': 'high',
            'status': 'pending_verification',
            'dueDate': get_date(0)
        },
        {
            'title': 'Loading & Dispatch - Jaipur Delivery',
            'description': 'Load material on truck safely, secure with straps/padding, prepare delivery challan, vehicle documentation. लोडिंग और भेजना।',
            'projectId': project_ids[1],
            'assignedTo': employee_ids[1],
            'priority': 'high',
            'status': 'ready_to_start',
            'dueDate': get_date(1)
        },
        {
            'title': 'Material Stacking & Arrangement',
            'description': 'Proper stacking of slabs in A-frame racks, segregate by variety/size, maintain aisle space. माल सजावट।',
            'projectId': project_ids[1],
            'assignedTo': employee_ids[1],
            'priority': 'medium',
            'status': 'ready_to_start',
            'dueDate': get_date(1)
        },
        {
            'title': 'Cycle Stock Count',
            'description': 'Physical count of 20-30% of inventory, variance analysis, update system records. चक्रीय स्टॉक गणना।',
            'projectId': project_ids[1],
            'assignedTo': employee_ids[1],
            'priority': 'high',
            'status': 'ready_to_start',
            'dueDate': get_date(6)
        },
        {
            'title': 'Slow-Moving Stock Identification',
            'description': 'Identify items in godown for >60 days, report to management for clearance sale decisions. धीमी स्टॉक पहचान।',
            'projectId': project_ids[1],
            'assignedTo': employee_ids[1],
            'priority': 'medium',
            'status': 'ready_to_start',
            'dueDate': get_date(7)
        },
        {
            'title': 'Godown Equipment Maintenance',
            'description': 'Forklift servicing, crane wire rope check, A-frame rack stability check, tool inventory. उपकरण रखरखाव।',
            'projectId': project_ids[1],
            'assignedTo': employee_ids[1],
            'priority': 'high',
            'status': 'ready_to_start',
            'dueDate': get_date(7)
        },
        
        # SHOWROOM TASKS (Project 2)
        {
            'title': 'Showroom Opening Checklist',
            'description': 'Open shutters, lights/AC on, display cleaning, cash float preparation, system boot-up. शोरूम खोलना।',
            'projectId': project_ids[2],
            'assignedTo': employee_ids[2],  # Showroom Manager
            'priority': 'high',
            'status': 'completed',
            'dueDate': get_date(-1)
        },
        {
            'title': 'Customer Walk-in - Mehta Residence Project',
            'description': 'Greet customers, understand requirements, show samples, explain varieties, create quotation. ग्राहक संभालना।',
            'projectId': project_ids[2],
            'assignedTo': employee_ids[5],  # Sales Executive
            'priority': 'high',
            'status': 'in_progress',
            'dueDate': get_date(0)
        },
        {
            'title': 'Site Visit - Vaishali Nagar Villa',
            'description': 'Visit customer site for measurement, assessment, material selection on-site, template taking. साइट विज़िट।',
            'projectId': project_ids[2],
            'assignedTo': employee_ids[5],
            'priority': 'high',
            'status': 'in_progress',
            'dueDate': get_date(0)
        },
        {
            'title': 'Quotation Preparation - Hotel Taj Palace',
            'description': 'Prepare detailed quotations with measurements, rates, installation charges; follow-up calls. कोटेशन तैयारी।',
            'projectId': project_ids[2],
            'assignedTo': employee_ids[5],
            'priority': 'high',
            'status': 'pending_verification',
            'dueDate': get_date(1)
        },
        {
            'title': 'Order Booking - Sharma Kitchen Project',
            'description': 'Confirm orders, collect advance payment (30-50%), issue receipt, inform godown for material. ऑर्डर बुकिंग।',
            'projectId': project_ids[2],
            'assignedTo': employee_ids[2],
            'priority': 'high',
            'status': 'ready_to_start',
            'dueDate': get_date(1)
        },
        {
            'title': 'Sample Request Processing',
            'description': 'Prepare sample pieces (6"x6" or 12"x12") for customers, pack properly, arrange courier/delivery. नमूना तैयार करना।',
            'projectId': project_ids[2],
            'assignedTo': employee_ids[5],
            'priority': 'medium',
            'status': 'ready_to_start',
            'dueDate': get_date(2)
        },
        {
            'title': 'Customer Complaint - Singh Residence',
            'description': 'Handle customer complaint regarding installation quality, coordinate resolution with installation team. शिकायत निपटान।',
            'projectId': project_ids[2],
            'assignedTo': employee_ids[2],
            'priority': 'high',
            'status': 'in_progress',
            'dueDate': get_date(1)
        },
        {
            'title': 'Daily Sales Reporting',
            'description': 'Compile daily sales data, payment collections, pending payments, send report to management. बिक्री रिपोर्ट।',
            'projectId': project_ids[2],
            'assignedTo': employee_ids[2],
            'priority': 'medium',
            'status': 'ready_to_start',
            'dueDate': get_date(0)
        },
        {
            'title': 'Display Rearrangement',
            'description': 'Rotate sample displays, highlight new arrivals, clean sample boards, update price tags. प्रदर्शन पुनर्व्यवस्था।',
            'projectId': project_ids[2],
            'assignedTo': employee_ids[5],
            'priority': 'medium',
            'status': 'ready_to_start',
            'dueDate': get_date(7)
        },
        {
            'title': 'Lead Follow-up & Conversion Review',
            'description': 'Review all pending quotations, make follow-up calls, strategize for conversion, update CRM. लीड अनुवर्ती।',
            'projectId': project_ids[2],
            'assignedTo': employee_ids[2],
            'priority': 'high',
            'status': 'ready_to_start',
            'dueDate': get_date(7)
        },
        {
            'title': 'New Sample Addition - Latest Varieties',
            'description': 'Visit factory/godown, select new varieties, prepare display samples, label and arrange. नया नमूना जोड़ना।',
            'projectId': project_ids[2],
            'assignedTo': employee_ids[2],
            'priority': 'medium',
            'status': 'ready_to_start',
            'dueDate': get_date(14)
        },
        
        # INSTALLATION TASKS (Project 3)
        {
            'title': 'Site Measurement - Gupta Residence Kitchen',
            'description': 'Measure installation area, assess substrate condition, note obstacles/cuts, prepare cutting list. साइट माप।',
            'projectId': project_ids[3],
            'assignedTo': employee_ids[3],  # Installation Supervisor
            'priority': 'high',
            'status': 'in_progress',
            'dueDate': get_date(0)
        },
        {
            'title': 'Material Loading - Vaishali Project',
            'description': 'Load required slabs/materials from godown, secure properly, transport to site safely. माल लोड करना।',
            'projectId': project_ids[3],
            'assignedTo': employee_ids[6],  # Stone Mason
            'priority': 'high',
            'status': 'ready_to_start',
            'dueDate': get_date(1)
        },
        {
            'title': 'Stone Installation - Mehta Kitchen Counter',
            'description': 'Lay marble/granite slabs, apply adhesive, ensure level alignment, grout joints, cleanup. पत्थर स्थापना।',
            'projectId': project_ids[3],
            'assignedTo': employee_ids[6],
            'priority': 'high',
            'status': 'in_progress',
            'dueDate': get_date(1)
        },
        {
            'title': 'On-site Cutting - Bathroom Vanity',
            'description': 'Final cuts for fitting around obstacles, sink cutouts, edge adjustments using portable tools. साइट पर काटना।',
            'projectId': project_ids[3],
            'assignedTo': employee_ids[6],
            'priority': 'high',
            'status': 'in_progress',
            'dueDate': get_date(1)
        },
        {
            'title': 'Final Polishing - Mehta Project',
            'description': 'Polish installed surface, buff to shine, remove installation marks, joint line polishing. अंतिम पॉलिशिंग।',
            'projectId': project_ids[3],
            'assignedTo': employee_ids[6],
            'priority': 'high',
            'status': 'pending_verification',
            'dueDate': get_date(2)
        },
        {
            'title': 'Customer Final Inspection - Mehta Handover',
            'description': 'Show completed work to customer, explain care instructions, obtain completion sign-off. ग्राहक निरीक्षण।',
            'projectId': project_ids[3],
            'assignedTo': employee_ids[3],
            'priority': 'high',
            'status': 'pending_verification',
            'dueDate': get_date(2)
        },
        {
            'title': 'Site Cleanup - Gupta Residence',
            'description': 'Clean site thoroughly, remove waste material, return unused slabs to godown, tool collection. साइट सफाई।',
            'projectId': project_ids[3],
            'assignedTo': employee_ids[6],
            'priority': 'medium',
            'status': 'ready_to_start',
            'dueDate': get_date(2)
        },
        {
            'title': 'Installation Report Submission',
            'description': 'Submit daily work report, material used, issues faced, customer feedback, payment collection. रिपोर्ट जमा।',
            'projectId': project_ids[3],
            'assignedTo': employee_ids[3],
            'priority': 'medium',
            'status': 'ready_to_start',
            'dueDate': get_date(0)
        },
        {
            'title': 'Tool & Equipment Maintenance',
            'description': 'Check all installation tools, sharpen cutting discs, lubricate machines, replace worn items. उपकरण रखरखाव।',
            'projectId': project_ids[3],
            'assignedTo': employee_ids[6],
            'priority': 'high',
            'status': 'ready_to_start',
            'dueDate': get_date(7)
        },
        {
            'title': 'Site Survey - Sharma Building Flooring',
            'description': 'New project measurement, material requirement calculation, installation timeline planning. साइट सर्वेक्षण।',
            'projectId': project_ids[3],
            'assignedTo': employee_ids[3],
            'priority': 'high',
            'status': 'ready_to_start',
            'dueDate': get_date(3)
        },
        {
            'title': 'Pending Site Follow-up',
            'description': 'Visit sites with pending work, assess delays, coordinate material availability, reschedule. लंबित साइट अनुवर्ती।',
            'projectId': project_ids[3],
            'assignedTo': employee_ids[3],
            'priority': 'medium',
            'status': 'ready_to_start',
            'dueDate': get_date(6)
        },
        
        # ADDITIONAL CROSS-FUNCTIONAL TASKS
        {
            'title': 'Weekly Team Coordination Meeting',
            'description': 'Review weekly progress across all branches, discuss pending orders, material availability, upcoming projects. टीम बैठक।',
            'projectId': project_ids[2],
            'assignedTo': employee_ids[2],
            'priority': 'high',
            'status': 'ready_to_start',
            'dueDate': get_date(7)
        },
        {
            'title': 'Urgent Order - Hotel Rajputana Lobby',
            'description': 'Rush order for 200 sq ft Makrana White marble, priority production and installation within 5 days. तत्काल ऑर्डर।',
            'projectId': project_ids[0],
            'assignedTo': employee_ids[0],
            'priority': 'high',
            'status': 'in_progress',
            'dueDate': get_date(5)
        },
        {
            'title': 'Quality Issue Investigation - Batch #4532',
            'description': 'Investigate reported surface defects in recent batch, coordinate with factory and customer. गुणवत्ता जाँच।',
            'projectId': project_ids[0],
            'assignedTo': employee_ids[0],
            'priority': 'high',
            'status': 'in_progress',
            'dueDate': get_date(2)
        },
        {
            'title': 'Payment Collection - Pending Invoices',
            'description': 'Follow up with 5 customers for pending payments, coordinate with accounts department. भुगतान संग्रह।',
            'projectId': project_ids[2],
            'assignedTo': employee_ids[2],
            'priority': 'high',
            'status': 'ready_to_start',
            'dueDate': get_date(3)
        },
        {
            'title': 'New Material Sourcing - Green Marble',
            'description': 'Source new supplier for Udaipur green marble, negotiate rates, arrange sample inspection. नई सामग्री खरीद।',
            'projectId': project_ids[1],
            'assignedTo': employee_ids[1],
            'priority': 'medium',
            'status': 'ready_to_start',
            'dueDate': get_date(10)
        },
        {
            'title': 'Staff Training - Safety Procedures',
            'description': 'Conduct safety training for all team members, equipment handling, emergency response procedures. प्रशिक्षण।',
            'projectId': project_ids[0],
            'assignedTo': employee_ids[0],
            'priority': 'high',
            'status': 'ready_to_start',
            'dueDate': get_date(14)
        }
    ]
    
    created_count = 0
    failed_count = 0
    
    for task_data in tasks_data:
        result = tasks.create_task(task_data)
        if result['success']:
            created_count += 1
            status_emoji = {
                'completed': '✅',
                'in_progress': '🔄',
                'pending_verification': '⏳',
                'ready_to_start': '📋'
            }.get(task_data['status'], '📝')
            print(f"   {status_emoji} {task_data['title'][:50]}...")
        else:
            failed_count += 1
            print(f"   ❌ Failed: {task_data['title'][:50]} - {result.get('error', 'Unknown error')}")
    
    print(f"\n✅ Created {created_count} tasks")
    if failed_count > 0:
        print(f"❌ Failed {failed_count} tasks")
    print()

def main():
    """Main function to populate demo data"""
    print("=" * 70)
    print("🏗️  MARBLE & GRANITE BUSINESS - DEMO DATA POPULATION")
    print("📍 Rajasthan, India - 4 Branches")
    print("=" * 70)
    print()
    
    try:
        # Initialize database
        print("🔧 Initializing database...")
        db.init_database()
        print("✅ Database initialized\n")
        
        # Create employees
        employee_ids = create_employees()
        if len(employee_ids) != 7:
            print("⚠️  Warning: Expected 7 employees, but created", len(employee_ids))
            print()
        
        # Create projects
        project_ids = create_projects(employee_ids)
        if len(project_ids) != 4:
            print("⚠️  Warning: Expected 4 projects, but created", len(project_ids))
            print()
        
        # Create tasks
        create_tasks(employee_ids, project_ids)
        
        print("=" * 70)
        print("🎉 DEMO DATA POPULATED SUCCESSFULLY!")
        print("=" * 70)
        print()
        print("📊 Summary:")
        print(f"   👥 Employees: 7 team members across all branches")
        print(f"   📁 Projects: 4 branches (Factory, Godown, Showroom, Installation)")
        print(f"   📝 Tasks: 45+ realistic recurring tasks")
        print()
        print("🌐 You can now:")
        print("   1. Start your Flask backend: python app.py")
        print("   2. Start your React frontend: npm test")
        print("   3. View the populated dashboard")
        print("   4. Demo the WhatsApp task management workflow")
        print()
        print("💡 Task statuses include:")
        print("   ✅ Completed (past tasks)")
        print("   🔄 In Progress (active work)")
        print("   ⏳ Pending Verification (awaiting approval)")
        print("   📋 Ready to Start (upcoming tasks)")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())

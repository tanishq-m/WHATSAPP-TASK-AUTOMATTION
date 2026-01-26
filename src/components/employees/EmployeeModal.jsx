/**
 * EmployeeModal Component
 * Modal form for creating and editing employees
 * Follows the same pattern as CreateProjectModal.jsx
 */

import { useState, useEffect } from 'react';
import { validateEmployee } from '../../utils/validators';
import { useApp } from '../../context/useApp';
import Modal from '../common/Modal';
import Input from '../common/Input';
import Button from '../common/Button';
import Select from '../common/Select';

const ROLE_OPTIONS = [
  { value: 'Developer', label: 'Developer' },
  { value: 'Designer', label: 'Designer' },
  { value: 'Tester', label: 'Tester' },
  { value: 'Manager', label: 'Manager' },
  { value: 'Other', label: 'Other' }
];

const EmployeeModal = ({ isOpen, onClose, employee = null }) => {
  const { addEmployee, updateEmployee, setModalOpen } = useApp();
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    role: ''
  });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Pre-fill form when editing employee
  useEffect(() => {
    if (isOpen && employee) {
      setFormData({
        name: employee.name || '',
        phone: employee.phone || '',
        role: employee.role || ''
      });
    } else if (isOpen && !employee) {
      // Clear form for new employee
      setFormData({
        name: '',
        phone: '',
        role: ''
      });
    }
    setErrors({});
  }, [isOpen, employee]);

  // Handle modal open/close for auto-refresh pause
  useEffect(() => {
    setModalOpen(isOpen);
    return () => setModalOpen(false);
  }, [isOpen, setModalOpen]);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));

    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate form
    const { isValid, errors: validationErrors } = validateEmployee(formData);
    
    if (!isValid) {
      setErrors(validationErrors);
      return;
    }

    setIsSubmitting(true);
    
    try {
      if (employee) {
        // Update existing employee
        await updateEmployee(employee.id, formData);
      } else {
        // Create new employee
        await addEmployee(formData);
      }
      
      // Close modal on success
      onClose();
    } catch (error) {
      // Error is handled by context and shown as toast
      console.error('Error saving employee:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      setFormData({
        name: '',
        phone: '',
        role: ''
      });
      setErrors({});
      onClose();
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={employee ? 'Edit Employee' : 'Add Employee'}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Employee Name */}
        <Input
          label="Employee Name"
          value={formData.name}
          onChange={(e) => handleInputChange('name', e.target.value)}
          placeholder="Enter employee name"
          error={errors.name}
          required
          disabled={isSubmitting}
        />

        {/* Phone Number */}
        <Input
          label="Phone Number"
          type="tel"
          value={formData.phone}
          onChange={(e) => handleInputChange('phone', e.target.value)}
          placeholder="+919876543210"
          error={errors.phone}
          required
          disabled={isSubmitting}
          helperText="Include country code (e.g., +91 for India)"
        />

        {/* Role */}
        <Select
          label="Role"
          value={formData.role}
          onChange={(e) => handleInputChange('role', e.target.value)}
          options={ROLE_OPTIONS}
          placeholder="Select role"
          error={errors.role}
          required
          disabled={isSubmitting}
        />

        {/* Submit Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 pt-4">
          <Button
            type="button"
            variant="secondary"
            onClick={handleClose}
            disabled={isSubmitting}
            className="w-full sm:w-auto order-2 sm:order-1"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={isSubmitting}
            isLoading={isSubmitting}
            className="w-full sm:flex-1 order-1 sm:order-2"
          >
            {isSubmitting 
              ? (employee ? 'Updating...' : 'Creating...') 
              : (employee ? 'Update Employee' : 'Create Employee')
            }
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default EmployeeModal;
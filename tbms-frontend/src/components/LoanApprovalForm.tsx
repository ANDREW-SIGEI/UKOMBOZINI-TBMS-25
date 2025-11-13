import { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { loansApi } from '../utils/api';
import type { Loan } from '../types';
import { toast } from 'react-toastify';

interface LoanApprovalFormProps {
  loan: Loan;
  onClose: () => void;
  onSuccess: () => void;
}

const LoanApprovalForm = ({ loan, onClose, onSuccess }: LoanApprovalFormProps) => {
  const [formData, setFormData] = useState({
    approval_date: new Date().toISOString().split('T')[0],
    approval_notes: '',
  });

  const approveMutation = useMutation({
    mutationFn: (data: typeof formData) =>
      loansApi.updateLoan(loan.id, { ...data, status: 'approved' }),
    onSuccess: () => {
      toast.success('Loan approved successfully');
      onSuccess();
    },
    onError: () => {
      toast.error('Failed to approve loan');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    approveMutation.mutate(formData);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const isLoading = approveMutation.isPending;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Approve Loan Application</h3>

          <div className="mb-4 p-4 bg-gray-50 rounded-md">
            <h4 className="text-sm font-medium text-gray-900 mb-2">Loan Details</h4>
            <div className="text-sm text-gray-600 space-y-1">
              <p><strong>Loan Number:</strong> {loan.loan_number}</p>
              <p><strong>Member:</strong> {loan.member_name}</p>
              <p><strong>Amount:</strong> KES {loan.principal_amount?.toLocaleString()}</p>
              <p><strong>Type:</strong> {loan.loan_type}</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Approval Date
              </label>
              <input
                type="date"
                name="approval_date"
                value={formData.approval_date}
                onChange={handleChange}
                required
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Approval Notes
              </label>
              <textarea
                name="approval_notes"
                value={formData.approval_notes}
                onChange={handleChange}
                rows={3}
                placeholder="Optional notes about the approval..."
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className="bg-green-600 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
              >
                {isLoading ? 'Approving...' : 'Approve Loan'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default LoanApprovalForm;

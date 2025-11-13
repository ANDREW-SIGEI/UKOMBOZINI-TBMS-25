import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { loansApi } from '../utils/api';
import { toast } from 'react-toastify';
import { loanSchema, type LoanFormData } from '../utils/validationSchemas';
import type { Loan, Member, Group } from '../types';

interface LoanFormProps {
  loan?: Loan | null;
  members: Member[];
  groups: Group[];
  onClose: () => void;
  onSuccess: () => void;
}

const LoanForm = ({ loan, members, groups, onClose, onSuccess }: LoanFormProps) => {
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<LoanFormData>({
    resolver: zodResolver(loanSchema),
    defaultValues: {
      loan_type: 'short_term',
      principal_amount: 0,
      interest_rate: 0,
      short_term_months: 12,
      long_term_months: 0,
      application_date: new Date().toISOString().split('T')[0],
    },
  });

  const loanType = watch('loan_type');
  const principalAmount = watch('principal_amount');
  const interestRate = watch('interest_rate');
  const shortTermMonths = watch('short_term_months');
  const longTermMonths = watch('long_term_months');

  useEffect(() => {
    if (loan) {
      setValue('member', loan.member || 0);
      setValue('group', loan.group || undefined);
      setValue('loan_type', loan.loan_type as 'short_term' | 'long_term' | 'top_up' | 'project');
      setValue('principal_amount', loan.principal_amount);
      setValue('interest_rate', loan.interest_rate);
      setValue('short_term_months', loan.short_term_months || 0);
      setValue('long_term_months', loan.long_term_months || 0);
      setValue('application_date', loan.application_date);
    }
  }, [loan, setValue]);

  const createMutation = useMutation({
    mutationFn: (data: LoanFormData) => loansApi.createLoan(data),
    onSuccess: () => {
      toast.success('Loan application submitted successfully');
      onSuccess();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to submit loan application');
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: LoanFormData) => loansApi.updateLoan(loan!.id, data),
    onSuccess: () => {
      toast.success('Loan updated successfully');
      onSuccess();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to update loan');
    },
  });

  const onSubmit = (data: LoanFormData) => {
    if (loan) {
      updateMutation.mutate(data);
    } else {
      createMutation.mutate(data);
    }
  };

  const isLoading = createMutation.isPending || updateMutation.isPending;

  const calculateTotalRepayment = () => {
    const principal = principalAmount || 0;
    const rate = (interestRate || 0) / 100;
    const months = loanType === 'short_term' ? (shortTermMonths || 0) : (longTermMonths || 0);
    const totalInterest = principal * rate * (months / 12);
    return principal + totalInterest;
  };

  const calculateMonthlyPayment = () => {
    const total = calculateTotalRepayment();
    const months = loanType === 'short_term' ? (shortTermMonths || 0) : (longTermMonths || 0);
    return months > 0 ? total / months : 0;
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white max-h-[90vh] overflow-y-auto">
        <div className="mt-3">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            {loan ? 'Edit Loan Application' : 'New Loan Application'}
          </h3>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Basic Information */}
              <div className="space-y-4">
                <h4 className="text-md font-medium text-gray-900">Basic Information</h4>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Member
                  </label>
                  <select
                    {...register('member', { valueAsNumber: true })}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    <option value="">Select Member</option>
                    {members.map((member) => (
                      <option key={member.id} value={member.id}>
                        {member.full_name} ({member.member_number})
                      </option>
                    ))}
                  </select>
                  {errors.member && (
                    <p className="mt-1 text-sm text-red-600">{errors.member.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Group (Optional)
                  </label>
                  <select
                    {...register('group', { valueAsNumber: true })}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    <option value="">Select Group</option>
                    {groups.map((group) => (
                      <option key={group.id} value={group.id}>
                        {group.name}
                      </option>
                    ))}
                  </select>
                  {errors.group && (
                    <p className="mt-1 text-sm text-red-600">{errors.group.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Loan Type
                  </label>
                  <select
                    {...register('loan_type')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    <option value="short_term">Short Term</option>
                    <option value="long_term">Long Term</option>
                    <option value="top_up">Top Up</option>
                    <option value="project">Project</option>
                  </select>
                  {errors.loan_type && (
                    <p className="mt-1 text-sm text-red-600">{errors.loan_type.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Principal Amount (KES)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    {...register('principal_amount', { valueAsNumber: true })}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.principal_amount && (
                    <p className="mt-1 text-sm text-red-600">{errors.principal_amount.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Interest Rate (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    {...register('interest_rate', { valueAsNumber: true })}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.interest_rate && (
                    <p className="mt-1 text-sm text-red-600">{errors.interest_rate.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Short Term Months
                  </label>
                  <input
                    type="number"
                    {...register('short_term_months', { valueAsNumber: true })}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.short_term_months && (
                    <p className="mt-1 text-sm text-red-600">{errors.short_term_months.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Long Term Months
                  </label>
                  <input
                    type="number"
                    {...register('long_term_months', { valueAsNumber: true })}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.long_term_months && (
                    <p className="mt-1 text-sm text-red-600">{errors.long_term_months.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Application Date
                  </label>
                  <input
                    type="date"
                    {...register('application_date')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.application_date && (
                    <p className="mt-1 text-sm text-red-600">{errors.application_date.message}</p>
                  )}
                </div>
              </div>

              {/* Additional Information */}
              <div className="space-y-4">
                <h4 className="text-md font-medium text-gray-900">Additional Information</h4>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Purpose
                  </label>
                  <textarea
                    {...register('purpose')}
                    rows={3}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.purpose && (
                    <p className="mt-1 text-sm text-red-600">{errors.purpose.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Collateral Details
                  </label>
                  <textarea
                    {...register('collateral_details')}
                    rows={2}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.collateral_details && (
                    <p className="mt-1 text-sm text-red-600">{errors.collateral_details.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Guarantor Name
                  </label>
                  <input
                    type="text"
                    {...register('guarantor_name')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.guarantor_name && (
                    <p className="mt-1 text-sm text-red-600">{errors.guarantor_name.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Guarantor Phone
                  </label>
                  <input
                    type="tel"
                    {...register('guarantor_phone')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.guarantor_phone && (
                    <p className="mt-1 text-sm text-red-600">{errors.guarantor_phone.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Guarantor ID Number
                  </label>
                  <input
                    type="text"
                    {...register('guarantor_id_number')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.guarantor_id_number && (
                    <p className="mt-1 text-sm text-red-600">{errors.guarantor_id_number.message}</p>
                  )}
                </div>

                {/* Loan Summary */}
                <div className="bg-gray-50 p-4 rounded-md">
                  <h5 className="text-sm font-medium text-gray-900 mb-2">Loan Summary</h5>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span>Total Repayment:</span>
                      <span className="font-medium">KES {calculateTotalRepayment().toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Monthly Payment:</span>
                      <span className="font-medium">KES {calculateMonthlyPayment().toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Interest Amount:</span>
                      <span className="font-medium">
                        KES {(calculateTotalRepayment() - (principalAmount || 0)).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Form Actions */}
            <div className="flex justify-end space-x-3 pt-6 border-t">
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
                className="bg-indigo-600 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
              >
                {isLoading ? 'Submitting...' : (loan ? 'Update Application' : 'Submit Application')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default LoanForm;

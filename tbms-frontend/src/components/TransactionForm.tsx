import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { transactionsApi } from '../utils/api';
import { toast } from 'react-toastify';
import { transactionSchema, type TransactionFormData } from '../utils/validationSchemas';
import type { Group } from '../types';

interface TransactionFormProps {
  transactionType: 'cash_in' | 'cash_out';
  groups: Group[];
  onClose: () => void;
  onSuccess: () => void;
}

const TransactionForm = ({ transactionType, groups, onClose, onSuccess }: TransactionFormProps) => {
  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<TransactionFormData>({
    resolver: zodResolver(transactionSchema),
    defaultValues: {
      amount: 0,
      description: '',
      transaction_date: new Date().toISOString().split('T')[0],
      receipt_number: '',
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: TransactionFormData) =>
      transactionType === 'cash_in'
        ? transactionsApi.createCashIn(data)
        : transactionsApi.createCashOut(data),
    onSuccess: () => {
      toast.success('Transaction recorded successfully');
      onSuccess();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to record transaction');
    },
  });

  const onSubmit = (data: TransactionFormData) => {
    createMutation.mutate(data);
  };

  const isLoading = createMutation.isPending;

  const generateReceiptNumber = () => {
    const date = new Date();
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
    const type = transactionType === 'cash_in' ? 'CI' : 'CO';
    return `${type}${year}${month}${day}${random}`;
  };



  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            {transactionType === 'cash_in' ? 'Cash In Transaction' : 'Cash Out Transaction'}
          </h3>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Group
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
                Amount (KES)
              </label>
              <input
                type="number"
                step="0.01"
                {...register('amount', { valueAsNumber: true })}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
              {errors.amount && (
                <p className="mt-1 text-sm text-red-600">{errors.amount.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Description
              </label>
              <textarea
                {...register('description')}
                rows={3}
                placeholder="Enter transaction description..."
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
              {errors.description && (
                <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Transaction Date
              </label>
              <input
                type="date"
                {...register('transaction_date')}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
              {errors.transaction_date && (
                <p className="mt-1 text-sm text-red-600">{errors.transaction_date.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Receipt Number
              </label>
              <div className="flex space-x-2">
                <input
                  type="text"
                  {...register('receipt_number')}
                  placeholder="Enter or generate receipt number"
                  className="mt-1 block flex-1 border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
                <button
                  type="button"
                  onClick={() => setValue('receipt_number', generateReceiptNumber())}
                  className="mt-1 px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  Generate
                </button>
              </div>
              {errors.receipt_number && (
                <p className="mt-1 text-sm text-red-600">{errors.receipt_number.message}</p>
              )}
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
                className={`py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                  transactionType === 'cash_in'
                    ? 'bg-green-600 hover:bg-green-700 focus:ring-green-500'
                    : 'bg-red-600 hover:bg-red-700 focus:ring-red-500'
                } disabled:opacity-50`}
              >
                {isLoading ? 'Recording...' : `Record ${transactionType === 'cash_in' ? 'Cash In' : 'Cash Out'}`}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default TransactionForm;

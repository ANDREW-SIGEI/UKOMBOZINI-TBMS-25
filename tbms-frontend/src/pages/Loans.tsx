import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { loansApi, membersApi, groupsApi } from '../utils/api';
import type { Loan, Member, Group } from '../types';
import Layout from '../components/Layout';
import LoanForm from '../components/LoanForm';
import LoanApprovalForm from '../components/LoanApprovalForm';
import LoanDisbursementForm from '../components/LoanDisbursementForm';
import { toast } from 'react-toastify';

const Loans = () => {
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isApprovalOpen, setIsApprovalOpen] = useState(false);
  const [isDisbursementOpen, setIsDisbursementOpen] = useState(false);
  const [selectedLoan, setSelectedLoan] = useState<Loan | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);

  const queryClient = useQueryClient();

  const { data: loansResponse, isLoading } = useQuery({
    queryKey: ['loans', currentPage, searchTerm, statusFilter],
    queryFn: () => loansApi.getLoans({
      page: currentPage,
      page_size: pageSize,
      search: searchTerm || undefined,
      status: statusFilter || undefined,
    }),
    select: (data) => data.data,
  });

  const { data: members } = useQuery({
    queryKey: ['members'],
    queryFn: () => membersApi.getMembers(),
    select: (data) => data.data.results,
  });

  const { data: groups } = useQuery({
    queryKey: ['groups'],
    queryFn: () => groupsApi.getGroups(),
    select: (data) => data.data.results,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => loansApi.updateLoan(id, { status: 'cancelled' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['loans'] });
      toast.success('Loan cancelled successfully');
    },
    onError: () => {
      toast.error('Failed to cancel loan');
    },
  });

  const handleEdit = (loan: Loan) => {
    setSelectedLoan(loan);
    setIsFormOpen(true);
  };

  const handleApprove = (loan: Loan) => {
    setSelectedLoan(loan);
    setIsApprovalOpen(true);
  };

  const handleDisburse = (loan: Loan) => {
    setSelectedLoan(loan);
    setIsDisbursementOpen(true);
  };

  const handleCancel = (id: number) => {
    if (window.confirm('Are you sure you want to cancel this loan?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleFormClose = () => {
    setIsFormOpen(false);
    setIsApprovalOpen(false);
    setIsDisbursementOpen(false);
    setSelectedLoan(null);
  };

  const handleFormSuccess = () => {
    queryClient.invalidateQueries({ queryKey: ['loans'] });
    handleFormClose();
  };

  const loans = loansResponse?.results || [];
  const totalPages = Math.ceil((loansResponse?.count || 0) / pageSize);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'approved': return 'bg-blue-100 text-blue-800';
      case 'disbursed': return 'bg-green-100 text-green-800';
      case 'active': return 'bg-indigo-100 text-indigo-800';
      case 'completed': return 'bg-purple-100 text-purple-800';
      case 'defaulted': return 'bg-red-100 text-red-800';
      case 'cancelled': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold text-gray-900">Loans</h1>
            <button
              onClick={() => setIsFormOpen(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
            >
              Apply for Loan
            </button>
          </div>

          {/* Filters */}
          <div className="mb-6 flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search loans..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 w-full"
              />
            </div>
            <div className="sm:w-48">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 w-full"
              >
                <option value="">All Statuses</option>
                <option value="pending">Pending</option>
                <option value="approved">Approved</option>
                <option value="disbursed">Disbursed</option>
                <option value="active">Active</option>
                <option value="completed">Completed</option>
                <option value="defaulted">Defaulted</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
          </div>

          {/* Loans Table */}
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Loan Number
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Member
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Amount
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Due Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {isLoading ? (
                    <tr>
                      <td colSpan={7} className="px-6 py-4 text-center">
                        Loading...
                      </td>
                    </tr>
                  ) : loans.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-6 py-4 text-center text-gray-500">
                        No loans found
                      </td>
                    </tr>
                  ) : (
                    loans.map((loan: Loan) => (
                      <tr key={loan.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {loan.loan_number}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {loan.member_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          KES {loan.principal_amount?.toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 capitalize">
                          {loan.loan_type?.replace('_', ' ')}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(loan.status)}`}>
                            {loan.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {loan.due_date ? new Date(loan.due_date).toLocaleDateString() : 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                          {loan.status === 'pending' && (
                            <button
                              onClick={() => handleApprove(loan)}
                              className="text-green-600 hover:text-green-900"
                            >
                              Approve
                            </button>
                          )}
                          {loan.status === 'approved' && (
                            <button
                              onClick={() => handleDisburse(loan)}
                              className="text-blue-600 hover:text-blue-900"
                            >
                              Disburse
                            </button>
                          )}
                          {loan.status !== 'cancelled' && loan.status !== 'completed' && loan.status !== 'defaulted' && (
                            <button
                              onClick={() => handleCancel(loan.id)}
                              className="text-red-600 hover:text-red-900"
                            >
                              Cancel
                            </button>
                          )}
                          {loan.status === 'active' && (
                            <button
                              onClick={() => handleEdit(loan)}
                              className="text-blue-600 hover:text-blue-900"
                            >
                              View Details
                            </button>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 bg-white border-t border-gray-200 sm:px-6 mt-4">
              <div className="flex-1 flex justify-between sm:hidden">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                  className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  Next
                </button>
              </div>
              <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm text-gray-700">
                    Showing page <span className="font-medium">{currentPage}</span> of{' '}
                    <span className="font-medium">{totalPages}</span>
                  </p>
                </div>
                <div>
                  <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                    <button
                      onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                      disabled={currentPage === 1}
                      className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                      disabled={currentPage === totalPages}
                      className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                    >
                      Next
                    </button>
                  </nav>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Forms */}
      {isFormOpen && (
        <LoanForm
          loan={selectedLoan}
          members={members || []}
          groups={groups || []}
          onClose={handleFormClose}
          onSuccess={handleFormSuccess}
        />
      )}

      {isApprovalOpen && selectedLoan && (
        <LoanApprovalForm
          loan={selectedLoan}
          onClose={handleFormClose}
          onSuccess={handleFormSuccess}
        />
      )}

      {isDisbursementOpen && selectedLoan && (
        <LoanDisbursementForm
          loan={selectedLoan}
          onClose={handleFormClose}
          onSuccess={handleFormSuccess}
        />
      )}
    </Layout>
  );
};

export default Loans;

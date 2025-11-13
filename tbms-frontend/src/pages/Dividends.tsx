import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { dividendsApi } from '../utils/api';
import type { DividendPeriod, MemberDividend } from '../types';
import { toast } from 'react-toastify';

const Dividends = () => {
  const [selectedPeriod, setSelectedPeriod] = useState<number | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const queryClient = useQueryClient();

  // Fetch dividend periods
  const { data: periods, isLoading: periodsLoading } = useQuery({
    queryKey: ['dividend-periods'],
    queryFn: () => dividendsApi.getDividendPeriods(),
  });

  // Fetch member dividends for selected period
  const { data: memberDividends, isLoading: dividendsLoading } = useQuery({
    queryKey: ['member-dividends', selectedPeriod],
    queryFn: () => selectedPeriod ? dividendsApi.getMemberDividends(selectedPeriod).then(res => res.data) : Promise.resolve([]),
    enabled: !!selectedPeriod,
  });

  // Calculate dividends mutation
  const calculateMutation = useMutation({
    mutationFn: (periodId: number) => dividendsApi.calculateDividends(periodId),
    onSuccess: () => {
      toast.success('Dividends calculated successfully');
      queryClient.invalidateQueries({ queryKey: ['dividend-periods'] });
      queryClient.invalidateQueries({ queryKey: ['member-dividends', selectedPeriod] });
    },
    onError: () => {
      toast.error('Failed to calculate dividends');
    },
  });

  // Toggle visibility mutations
  const toggleFieldOfficerVisibilityMutation = useMutation({
    mutationFn: ({ id, visible }: { id: number; visible: boolean }) =>
      dividendsApi.toggleFieldOfficerVisibility(id, visible),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['member-dividends', selectedPeriod] });
    },
  });

  const toggleMemberVisibilityMutation = useMutation({
    mutationFn: ({ id, visible }: { id: number; visible: boolean }) =>
      dividendsApi.toggleMemberVisibility(id, visible),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['member-dividends', selectedPeriod] });
    },
  });

  const filteredDividends = (memberDividends || []).filter((dividend: any) =>
    dividend.member_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleCalculateDividends = (periodId: number) => {
    calculateMutation.mutate(periodId);
  };

  const handleToggleFieldOfficerVisibility = (dividendId: number, currentVisibility: boolean) => {
    toggleFieldOfficerVisibilityMutation.mutate({ id: dividendId, visible: !currentVisibility });
  };

  const handleToggleMemberVisibility = (dividendId: number, currentVisibility: boolean) => {
    toggleMemberVisibilityMutation.mutate({ id: dividendId, visible: !currentVisibility });
  };

  if (periodsLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-gray-900">Dividend Management</h1>
          <p className="mt-2 text-sm text-gray-700">
            Calculate and manage dividend distributions for groups and members.
          </p>
        </div>
      </div>

      {/* Dividend Periods */}
      <div className="mt-8">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Dividend Periods</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {periods?.data?.map((period: DividendPeriod) => (
            <div
              key={period.id}
              className={`relative block w-full rounded-lg border p-4 cursor-pointer transition-colors ${
                selectedPeriod === period.id
                  ? 'border-indigo-500 bg-indigo-50'
                  : 'border-gray-300 bg-white hover:border-gray-400'
              }`}
              onClick={() => setSelectedPeriod(period.id)}
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-gray-900">{period.year}</h3>
                  <p className="text-sm text-gray-500">
                    {period.is_current_december ? 'December Period' : 'Annual Period'}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">
                    KES {period.total_dividend_pool?.toLocaleString() || '0'}
                  </p>
                  <p className="text-xs text-gray-500">Dividend Pool</p>
                </div>
              </div>

              <div className="mt-2 flex items-center justify-between">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  period.can_calculate
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {period.can_calculate ? 'Ready to Calculate' : 'Calculated'}
                </span>

                {period.can_calculate && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCalculateDividends(period.id);
                    }}
                    disabled={calculateMutation.isPending}
                    className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                  >
                    {calculateMutation.isPending ? 'Calculating...' : 'Calculate'}
                  </button>
                )}
              </div>

              {period.calculation_date && (
                <p className="mt-2 text-xs text-gray-500">
                  Calculated on {new Date(period.calculation_date).toLocaleDateString()}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Member Dividends */}
      {selectedPeriod && (
        <div className="mt-8">
          <div className="sm:flex sm:items-center">
            <div className="sm:flex-auto">
              <h2 className="text-lg font-medium text-gray-900">Member Dividends</h2>
              <p className="mt-2 text-sm text-gray-700">
                Manage dividend visibility and view distributions for the selected period.
              </p>
            </div>
            <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
              <div className="flex items-center">
                <input
                  type="text"
                  placeholder="Search members..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
              </div>
            </div>
          </div>

          {dividendsLoading ? (
            <div className="flex justify-center items-center h-32 mt-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            </div>
          ) : (
            <div className="mt-4 flex flex-col">
              <div className="-my-2 -mx-4 overflow-x-auto sm:-mx-6 lg:-mx-8">
                <div className="inline-block min-w-full py-2 align-middle md:px-6 lg:px-8">
                  <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
                    <table className="min-w-full divide-y divide-gray-300">
                      <thead className="bg-gray-50">
                        <tr>
                          <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6">
                            Member Name
                          </th>
                          <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                            Amount (KES)
                          </th>
                          <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                            Field Officer
                          </th>
                          <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                            Member
                          </th>
                          <th scope="col" className="relative py-3.5 pl-3 pr-4 sm:pr-6">
                            <span className="sr-only">Actions</span>
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200 bg-white">
                        {filteredDividends.map((dividend: any) => (
                          <tr key={dividend.id}>
                            <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-6">
                              {dividend.member_name}
                            </td>
                            <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                              {dividend.amount.toLocaleString()}
                            </td>
                            <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                dividend.is_visible_to_field_officer
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-gray-100 text-gray-800'
                              }`}>
                                {dividend.is_visible_to_field_officer ? 'Visible' : 'Hidden'}
                              </span>
                            </td>
                            <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                dividend.is_visible_to_member
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-gray-100 text-gray-800'
                              }`}>
                                {dividend.is_visible_to_member ? 'Visible' : 'Hidden'}
                              </span>
                            </td>
                            <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                              <div className="flex space-x-2">
                                <button
                                  onClick={() => handleToggleFieldOfficerVisibility(dividend.id, dividend.is_visible_to_field_officer)}
                                  className="text-indigo-600 hover:text-indigo-900"
                                >
                                  {dividend.is_visible_to_field_officer ? 'Hide FO' : 'Show FO'}
                                </button>
                                <button
                                  onClick={() => handleToggleMemberVisibility(dividend.id, dividend.is_visible_to_member)}
                                  className="text-indigo-600 hover:text-indigo-900"
                                >
                                  {dividend.is_visible_to_member ? 'Hide Member' : 'Show Member'}
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Dividends;

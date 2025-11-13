import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '../utils/api';
import Layout from '../components/Layout';
import DashboardChart from '../components/DashboardChart';
import CalendarView from '../components/CalendarView';
import ActivityFeed from '../components/ActivityFeed';

const Dashboard = () => {
  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ['dashboard-overview'],
    queryFn: () => dashboardApi.getOverview(),
    select: (data) => data.data,
  });

  const { data: loanOverview, isLoading: loanLoading } = useQuery({
    queryKey: ['dashboard-loan-overview'],
    queryFn: () => dashboardApi.getLoanOverview(),
    select: (data) => data.data,
  });

  const { data: savingsOverview, isLoading: savingsLoading } = useQuery({
    queryKey: ['dashboard-savings-overview'],
    queryFn: () => dashboardApi.getSavingsOverview(),
    select: (data) => data.data,
  });

  // Mock data for charts and calendar - replace with real API calls
  const loanChartData = [
    { name: 'Jan', loans: 120000 },
    { name: 'Feb', loans: 150000 },
    { name: 'Mar', loans: 180000 },
    { name: 'Apr', loans: 200000 },
    { name: 'May', loans: 220000 },
    { name: 'Jun', loans: 250000 },
  ];

  const savingsChartData = [
    { name: 'Jan', savings: 80000 },
    { name: 'Feb', savings: 95000 },
    { name: 'Mar', savings: 110000 },
    { name: 'Apr', savings: 125000 },
    { name: 'May', savings: 140000 },
    { name: 'Jun', savings: 160000 },
  ];

  const loanStatusData = [
    { name: 'Active', value: 65 },
    { name: 'Pending', value: 20 },
    { name: 'Overdue', value: 15 },
  ];

  const mockMeetings = [
    { id: '1', title: 'Monthly General Meeting', date: '2024-01-15', time: '10:00 AM', description: 'Monthly member meeting' },
    { id: '2', title: 'Loan Committee Review', date: '2024-01-18', time: '2:00 PM', description: 'Review pending loan applications' },
    { id: '3', title: 'Savings Collection', date: '2024-01-20', time: '9:00 AM', description: 'Monthly savings collection' },
  ];

  const mockActivities = [
    { id: '1', type: 'member_created', title: 'New Member Added', description: 'John Doe joined the cooperative', timestamp: new Date().toISOString(), user: 'Admin' },
    { id: '2', type: 'loan_approved', title: 'Loan Approved', description: 'Loan of KES 50,000 approved for Jane Smith', timestamp: new Date(Date.now() - 3600000).toISOString(), user: 'Loan Officer' },
    { id: '3', type: 'payment_received', title: 'Payment Received', description: 'Monthly savings payment received from Group A', timestamp: new Date(Date.now() - 7200000).toISOString(), user: 'Treasurer' },
    { id: '4', type: 'meeting_scheduled', title: 'Meeting Scheduled', description: 'Annual General Meeting scheduled for next month', timestamp: new Date(Date.now() - 10800000).toISOString(), user: 'Secretary' },
  ];

  const isLoading = overviewLoading || loanLoading || savingsLoading;

  if (isLoading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-lg">Loading dashboard...</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Dashboard</h1>

          {/* Overview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-blue-500 rounded-md flex items-center justify-center">
                      <span className="text-white text-sm font-bold">👥</span>
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Total Members
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {overview?.total_members || 0}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
                      <span className="text-white text-sm font-bold">🏢</span>
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Total Groups
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {overview?.total_groups || 0}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-yellow-500 rounded-md flex items-center justify-center">
                      <span className="text-white text-sm font-bold">💰</span>
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Total Loans
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        KES {overview?.total_loans?.toLocaleString() || 0}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-purple-500 rounded-md flex items-center justify-center">
                      <span className="text-white text-sm font-bold">💸</span>
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Total Savings
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        KES {overview?.total_savings?.toLocaleString() || 0}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Charts Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <DashboardChart
              data={loanChartData}
              type="line"
              title="Loan Trends (Last 6 Months)"
              dataKey="loans"
              color="#8884d8"
            />
            <DashboardChart
              data={savingsChartData}
              type="bar"
              title="Savings Growth (Last 6 Months)"
              dataKey="savings"
              color="#82ca9d"
            />
          </div>

          {/* Loan Status Pie Chart */}
          <div className="mb-8">
            <DashboardChart
              data={loanStatusData}
              type="pie"
              title="Loan Status Distribution"
              dataKey="value"
            />
          </div>

          {/* Calendar and Activity Feed */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <CalendarView meetings={mockMeetings} />
            <ActivityFeed activities={mockActivities} />
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Dashboard;

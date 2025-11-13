import { formatDistanceToNow } from 'date-fns';

interface Activity {
  id: string;
  type: 'member_created' | 'loan_approved' | 'payment_received' | 'meeting_scheduled';
  title: string;
  description: string;
  timestamp: string;
  user?: string;
}

interface ActivityFeedProps {
  activities: Activity[];
}

const ActivityFeed = ({ activities }: ActivityFeedProps) => {
  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'member_created':
        return '👤';
      case 'loan_approved':
        return '💰';
      case 'payment_received':
        return '💳';
      case 'meeting_scheduled':
        return '📅';
      default:
        return '📝';
    }
  };

  const getActivityColor = (type: string) => {
    switch (type) {
      case 'member_created':
        return 'bg-blue-100 text-blue-800';
      case 'loan_approved':
        return 'bg-green-100 text-green-800';
      case 'payment_received':
        return 'bg-purple-100 text-purple-800';
      case 'meeting_scheduled':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h3>
      <div className="space-y-4 max-h-96 overflow-y-auto">
        {activities.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">📭</div>
            <p>No recent activity</p>
          </div>
        ) : (
          activities.map((activity) => (
            <div key={activity.id} className="flex items-start space-x-3">
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm ${getActivityColor(activity.type)}`}>
                {getActivityIcon(activity.type)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-gray-900">
                    {activity.title}
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}
                  </p>
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  {activity.description}
                </p>
                {activity.user && (
                  <p className="text-xs text-gray-500 mt-1">
                    by {activity.user}
                  </p>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ActivityFeed;

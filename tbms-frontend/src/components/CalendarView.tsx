import { useState } from 'react';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isSameDay, addMonths, subMonths } from 'date-fns';

interface Meeting {
  id: string;
  title: string;
  date: string;
  time: string;
  description?: string;
}

interface CalendarViewProps {
  meetings: Meeting[];
}

const CalendarView = ({ meetings }: CalendarViewProps) => {
  const [currentDate, setCurrentDate] = useState(new Date());

  const monthStart = startOfMonth(currentDate);
  const monthEnd = endOfMonth(currentDate);
  const calendarDays = eachDayOfInterval({ start: monthStart, end: monthEnd });

  const getMeetingsForDate = (date: Date) => {
    return meetings.filter(meeting => isSameDay(new Date(meeting.date), date));
  };

  const nextMonth = () => {
    setCurrentDate(addMonths(currentDate, 1));
  };

  const prevMonth = () => {
    setCurrentDate(subMonths(currentDate, 1));
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-medium text-gray-900">Meeting Calendar</h3>
        <div className="flex items-center space-x-2">
          <button
            onClick={prevMonth}
            className="p-2 hover:bg-gray-100 rounded-md"
          >
            ‹
          </button>
          <span className="text-lg font-medium">
            {format(currentDate, 'MMMM yyyy')}
          </span>
          <button
            onClick={nextMonth}
            className="p-2 hover:bg-gray-100 rounded-md"
          >
            ›
          </button>
        </div>
      </div>

      <div className="grid grid-cols-7 gap-1">
        {/* Day headers */}
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
          <div key={day} className="p-2 text-center text-sm font-medium text-gray-500">
            {day}
          </div>
        ))}

        {/* Calendar days */}
        {calendarDays.map(day => {
          const dayMeetings = getMeetingsForDate(day);
          const isCurrentMonth = isSameMonth(day, currentDate);

          return (
            <div
              key={day.toISOString()}
              className={`min-h-[80px] p-2 border border-gray-200 ${
                !isCurrentMonth ? 'bg-gray-50 text-gray-400' : 'bg-white'
              }`}
            >
              <div className="text-sm font-medium mb-1">
                {format(day, 'd')}
              </div>
              <div className="space-y-1">
                {dayMeetings.slice(0, 2).map(meeting => (
                  <div
                    key={meeting.id}
                    className="text-xs bg-blue-100 text-blue-800 px-1 py-0.5 rounded truncate"
                    title={`${meeting.title} - ${meeting.time}`}
                  >
                    {meeting.title}
                  </div>
                ))}
                {dayMeetings.length > 2 && (
                  <div className="text-xs text-gray-500">
                    +{dayMeetings.length - 2} more
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Upcoming meetings list */}
      <div className="mt-6">
        <h4 className="text-md font-medium text-gray-900 mb-3">Upcoming Meetings</h4>
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {meetings
            .filter(meeting => new Date(meeting.date) >= new Date())
            .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
            .slice(0, 5)
            .map(meeting => (
              <div key={meeting.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                <div>
                  <div className="font-medium text-sm">{meeting.title}</div>
                  <div className="text-xs text-gray-500">
                    {format(new Date(meeting.date), 'MMM d, yyyy')} at {meeting.time}
                  </div>
                </div>
              </div>
            ))}
          {meetings.filter(meeting => new Date(meeting.date) >= new Date()).length === 0 && (
            <div className="text-sm text-gray-500 text-center py-4">
              No upcoming meetings
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CalendarView;

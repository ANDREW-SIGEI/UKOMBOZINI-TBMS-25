import { useState } from 'react';

interface WorkflowStep {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'completed' | 'rejected' | 'current';
  completedAt?: string;
  completedBy?: string;
  notes?: string;
}

interface ApprovalWorkflowProps {
  steps: WorkflowStep[];
  currentStep?: string;
}

const ApprovalWorkflow = ({ steps, currentStep }: ApprovalWorkflowProps) => {
  const [expandedStep, setExpandedStep] = useState<string | null>(null);

  const getStatusIcon = (status: WorkflowStep['status']) => {
    switch (status) {
      case 'completed':
        return <span className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center text-white text-sm">✓</span>;
      case 'rejected':
        return <span className="w-6 h-6 rounded-full bg-red-500 flex items-center justify-center text-white text-sm">✗</span>;
      case 'current':
        return <span className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center text-white text-sm animate-pulse">○</span>;
      default:
        return <span className="w-6 h-6 rounded-full bg-gray-400 flex items-center justify-center text-white text-sm">○</span>;
    }
  };

  const getStatusColor = (status: WorkflowStep['status']) => {
    switch (status) {
      case 'completed':
        return 'border-green-500 bg-green-50';
      case 'rejected':
        return 'border-red-500 bg-red-50';
      case 'current':
        return 'border-blue-500 bg-blue-50';
      default:
        return 'border-gray-300 bg-gray-50';
    }
  };

  const getConnectorColor = (status: WorkflowStep['status']) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500';
      case 'rejected':
        return 'bg-red-500';
      case 'current':
        return 'bg-blue-500';
      default:
        return 'bg-gray-300';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-6">Approval Workflow</h3>

      <div className="space-y-4">
        {steps.map((step, index) => (
          <div key={step.id} className="relative">
            {/* Connector line */}
            {index < steps.length - 1 && (
              <div
                className={`absolute left-6 top-12 w-0.5 h-8 ${getConnectorColor(step.status)}`}
              />
            )}

            {/* Step card */}
            <div
              className={`flex items-start space-x-4 p-4 rounded-lg border-2 transition-colors cursor-pointer ${getStatusColor(step.status)}`}
              onClick={() => setExpandedStep(expandedStep === step.id ? null : step.id)}
            >
              <div className="flex-shrink-0">
                {getStatusIcon(step.status)}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-medium text-gray-900">
                    {step.title}
                  </h4>
                  <span
                    className={`w-4 h-4 text-gray-400 transform transition-transform inline-block ${
                      expandedStep === step.id ? 'rotate-90' : ''
                    }`}
                  >
                    ▶
                  </span>
                </div>

                <p className="text-sm text-gray-600 mt-1">
                  {step.description}
                </p>

                {step.status === 'completed' && step.completedAt && (
                  <p className="text-xs text-gray-500 mt-2">
                    Completed on {new Date(step.completedAt).toLocaleDateString()}
                    {step.completedBy && ` by ${step.completedBy}`}
                  </p>
                )}

                {step.status === 'rejected' && step.notes && (
                  <p className="text-xs text-red-600 mt-2">
                    {step.notes}
                  </p>
                )}
              </div>
            </div>

            {/* Expanded details */}
            {expandedStep === step.id && (
              <div className="ml-12 mt-2 p-4 bg-gray-50 rounded-lg">
                <div className="space-y-2">
                  <div className="text-sm">
                    <span className="font-medium text-gray-700">Status:</span>
                    <span className={`ml-2 px-2 py-1 text-xs font-medium rounded-full ${
                      step.status === 'completed' ? 'bg-green-100 text-green-800' :
                      step.status === 'rejected' ? 'bg-red-100 text-red-800' :
                      step.status === 'current' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {step.status.charAt(0).toUpperCase() + step.status.slice(1)}
                    </span>
                  </div>

                  {step.completedAt && (
                    <div className="text-sm">
                      <span className="font-medium text-gray-700">Completed:</span>
                      <span className="ml-2 text-gray-600">
                        {new Date(step.completedAt).toLocaleString()}
                      </span>
                    </div>
                  )}

                  {step.completedBy && (
                    <div className="text-sm">
                      <span className="font-medium text-gray-700">By:</span>
                      <span className="ml-2 text-gray-600">{step.completedBy}</span>
                    </div>
                  )}

                  {step.notes && (
                    <div className="text-sm">
                      <span className="font-medium text-gray-700">Notes:</span>
                      <p className="ml-2 text-gray-600 mt-1">{step.notes}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Progress summary */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">
            Progress: {steps.filter(s => s.status === 'completed').length} of {steps.length} steps completed
          </span>
          <span className="font-medium text-gray-900">
            {Math.round((steps.filter(s => s.status === 'completed').length / steps.length) * 100)}%
          </span>
        </div>
        <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{
              width: `${(steps.filter(s => s.status === 'completed').length / steps.length) * 100}%`
            }}
          />
        </div>
      </div>
    </div>
  );
};

export default ApprovalWorkflow;

import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { membersApi, groupsApi } from '../utils/api';
import { toast } from 'react-toastify';
import { memberSchema, type MemberFormData } from '../utils/validationSchemas';
import type { Member } from '../types';
import DocumentUpload from './DocumentUpload';
import CameraCapture from './CameraCapture';
import SignaturePad from './SignaturePad';
import ApprovalWorkflow from './ApprovalWorkflow';

interface MemberFormProps {
  member?: Member | null;
  onClose: () => void;
  onSuccess: () => void;
}

const MemberForm = ({ member, onClose, onSuccess }: MemberFormProps) => {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'basic' | 'verification' | 'workflow'>('basic');
  const [idDocument, setIdDocument] = useState<File | null>(null);
  const [idDocumentPreview, setIdDocumentPreview] = useState<string>('');
  const [capturedImage, setCapturedImage] = useState<string>('');
  const [signature, setSignature] = useState<string>('');

  const { data: groups } = useQuery({
    queryKey: ['groups'],
    queryFn: () => groupsApi.getGroups(),
    select: (data) => data.data.results,
  });

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<MemberFormData>({
    resolver: zodResolver(memberSchema),
  });

  useEffect(() => {
    if (member) {
      setValue('member_number', member.member_number);
      setValue('user', member.user);
      setValue('group', member.group);
      setValue('first_name', member.first_name);
      setValue('last_name', member.last_name);
      setValue('id_number', member.id_number);
      setValue('phone_number', member.phone_number);
      setValue('email', member.email);
      setValue('date_of_birth', member.date_of_birth);
      setValue('gender', member.gender);
      setValue('marital_status', member.marital_status);
      setValue('education_level', member.education_level);
      setValue('occupation', member.occupation);
      setValue('employer', member.employer || '');
      setValue('monthly_income', member.monthly_income);
      setValue('address', member.address);
      setValue('city', member.city);
      setValue('county', member.county);
      setValue('postal_code', member.postal_code || '');

      // Set verification data
      if (member.id_document_preview) setIdDocumentPreview(member.id_document_preview);
      if (member.signature_url) setSignature(member.signature_url);
    }
  }, [member, setValue]);

  const createMutation = useMutation({
    mutationFn: (data: MemberFormData) => membersApi.createMember(data),
    onSuccess: () => {
      toast.success('Member created successfully');
      queryClient.invalidateQueries({ queryKey: ['members'] });
      onSuccess();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to create member');
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: MemberFormData) => membersApi.updateMember(member!.id, data),
    onSuccess: () => {
      toast.success('Member updated successfully');
      queryClient.invalidateQueries({ queryKey: ['members'] });
      onSuccess();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to update member');
    },
  });

  const onSubmit = (data: MemberFormData) => {
    // Prepare form data with verification documents
    const formData = {
      ...data,
      id_document: idDocument,
      id_document_preview: idDocumentPreview,
      signature_url: signature,
      verification_status: member?.verification_status || 'pending'
    };

    if (member) {
      updateMutation.mutate(formData);
    } else {
      createMutation.mutate(formData);
    }
  };

  const isLoading = createMutation.isPending || updateMutation.isPending;

  // Mock workflow steps for demonstration
  const workflowSteps = [
    {
      id: 'document_upload',
      title: 'Document Upload',
      description: 'Upload ID document and capture photo',
      status: (idDocumentPreview || capturedImage) ? 'completed' : 'pending',
      completedAt: idDocumentPreview ? new Date().toISOString() : undefined,
      completedBy: 'Field Officer',
    },
    {
      id: 'signature_capture',
      title: 'Signature Capture',
      description: 'Capture member signature',
      status: signature ? 'completed' : 'pending',
      completedAt: signature ? new Date().toISOString() : undefined,
      completedBy: 'Field Officer',
    },
    {
      id: 'verification_review',
      title: 'Verification Review',
      description: 'Review and verify member information',
      status: member?.verification_status === 'verified' ? 'completed' : 'current',
      completedAt: member?.verified_at,
      completedBy: member?.verified_by?.toString(),
    },
  ];

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-6xl shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            {member ? 'Edit Member' : 'Add New Member'}
          </h3>

          {/* Tab Navigation */}
          <div className="border-b border-gray-200 mb-6">
            <nav className="-mb-px flex space-x-8">
              {[
                { id: 'basic', label: 'Basic Information' },
                { id: 'verification', label: 'Verification' },
                { id: 'workflow', label: 'Approval Workflow' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {activeTab === 'basic' && (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Basic Information */}
              <div className="space-y-4">
                <h4 className="text-md font-medium text-gray-900">Basic Information</h4>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Member Number
                  </label>
                  <input
                    type="text"
                    {...register('member_number')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.member_number && (
                    <p className="mt-1 text-sm text-red-600">{errors.member_number.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    First Name
                  </label>
                  <input
                    type="text"
                    {...register('first_name')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.first_name && (
                    <p className="mt-1 text-sm text-red-600">{errors.first_name.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Last Name
                  </label>
                  <input
                    type="text"
                    {...register('last_name')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.last_name && (
                    <p className="mt-1 text-sm text-red-600">{errors.last_name.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    ID Number
                  </label>
                  <input
                    type="text"
                    {...register('id_number')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.id_number && (
                    <p className="mt-1 text-sm text-red-600">{errors.id_number.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Phone Number
                  </label>
                  <input
                    type="tel"
                    {...register('phone_number')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.phone_number && (
                    <p className="mt-1 text-sm text-red-600">{errors.phone_number.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Email
                  </label>
                  <input
                    type="email"
                    {...register('email')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.email && (
                    <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Date of Birth
                  </label>
                  <input
                    type="date"
                    {...register('date_of_birth')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.date_of_birth && (
                    <p className="mt-1 text-sm text-red-600">{errors.date_of_birth.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Gender
                  </label>
                  <select
                    {...register('gender')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    <option value="">Select Gender</option>
                    <option value="M">Male</option>
                    <option value="F">Female</option>
                  </select>
                  {errors.gender && (
                    <p className="mt-1 text-sm text-red-600">{errors.gender.message}</p>
                  )}
                </div>
              </div>

              {/* Additional Information */}
              <div className="space-y-4">
                <h4 className="text-md font-medium text-gray-900">Additional Information</h4>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Group
                  </label>
                  <select
                    {...register('group')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    <option value="">Select Group</option>
                    {groups?.map((group) => (
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
                    Marital Status
                  </label>
                  <select
                    {...register('marital_status')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    <option value="">Select Status</option>
                    <option value="single">Single</option>
                    <option value="married">Married</option>
                    <option value="divorced">Divorced</option>
                    <option value="widowed">Widowed</option>
                  </select>
                  {errors.marital_status && (
                    <p className="mt-1 text-sm text-red-600">{errors.marital_status.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Education Level
                  </label>
                  <select
                    {...register('education_level')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    <option value="">Select Education</option>
                    <option value="primary">Primary</option>
                    <option value="secondary">Secondary</option>
                    <option value="tertiary">Tertiary</option>
                    <option value="university">University</option>
                  </select>
                  {errors.education_level && (
                    <p className="mt-1 text-sm text-red-600">{errors.education_level.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Occupation
                  </label>
                  <input
                    type="text"
                    {...register('occupation')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.occupation && (
                    <p className="mt-1 text-sm text-red-600">{errors.occupation.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Employer
                  </label>
                  <input
                    type="text"
                    {...register('employer')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.employer && (
                    <p className="mt-1 text-sm text-red-600">{errors.employer.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Monthly Income (KES)
                  </label>
                  <input
                    type="number"
                    {...register('monthly_income')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.monthly_income && (
                    <p className="mt-1 text-sm text-red-600">{errors.monthly_income.message}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Address Information */}
            <div className="space-y-4">
              <h4 className="text-md font-medium text-gray-900">Address Information</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Address
                  </label>
                  <input
                    type="text"
                    {...register('address')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.address && (
                    <p className="mt-1 text-sm text-red-600">{errors.address.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    City
                  </label>
                  <input
                    type="text"
                    {...register('city')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.city && (
                    <p className="mt-1 text-sm text-red-600">{errors.city.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    County
                  </label>
                  <input
                    type="text"
                    {...register('county')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.county && (
                    <p className="mt-1 text-sm text-red-600">{errors.county.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Postal Code
                  </label>
                  <input
                    type="text"
                    {...register('postal_code')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.postal_code && (
                    <p className="mt-1 text-sm text-red-600">{errors.postal_code.message}</p>
                  )}
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
                {isLoading ? 'Saving...' : (member ? 'Update Member' : 'Create Member')}
              </button>
            </div>
          </form>
          )}

          {activeTab === 'verification' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <DocumentUpload
                  onFileSelect={(file, preview) => {
                    setIdDocument(file);
                    setIdDocumentPreview(preview);
                  }}
                  label="ID Document Upload"
                  currentPreview={idDocumentPreview}
                />

                <CameraCapture
                  onCapture={setCapturedImage}
                  label="Live Photo Capture"
                  currentImage={capturedImage}
                />
              </div>

              <SignaturePad
                onSignature={setSignature}
                label="Member Signature"
                currentSignature={signature}
              />

              <div className="flex justify-end space-x-3 pt-6 border-t">
                <button
                  type="button"
                  onClick={onClose}
                  className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('workflow')}
                  className="bg-indigo-600 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-indigo-700"
                >
                  Review Workflow
                </button>
              </div>
            </div>
          )}

          {activeTab === 'workflow' && (
            <div className="space-y-6">
              <ApprovalWorkflow steps={workflowSteps} />

              <div className="flex justify-end space-x-3 pt-6 border-t">
                <button
                  type="button"
                  onClick={() => setActiveTab('verification')}
                  className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Back to Verification
                </button>
                <button
                  type="button"
                  onClick={onClose}
                  className="bg-indigo-600 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-indigo-700"
                >
                  Complete Verification
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MemberForm;

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { groupsApi } from '../utils/api';
import { toast } from 'react-toastify';
import { groupSchema, type GroupFormData } from '../utils/validationSchemas';
import type { Group } from '../types';

interface GroupFormProps {
  group?: Group | null;
  onClose: () => void;
  onSuccess: () => void;
}

const GroupForm = ({ group, onClose, onSuccess }: GroupFormProps) => {
  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<GroupFormData>({
    resolver: zodResolver(groupSchema),
  });

  useEffect(() => {
    if (group) {
      setValue('name', group.name);
      setValue('registration_number', group.registration_number);
      setValue('description', group.description);
      setValue('county', group.county);
      setValue('constituency', group.constituency);
      setValue('ward', group.ward);
      setValue('location', group.location);
      setValue('village', group.village);
      setValue('chairperson_name', group.chairperson_name);
      setValue('chairperson_phone', group.chairperson_phone);
      setValue('chairperson_email', group.chairperson_email);
      setValue('secretary_name', group.secretary_name);
      setValue('treasurer_name', group.treasurer_name);
      setValue('formation_date', group.formation_date);
      setValue('registration_date', group.registration_date);
      setValue('initial_capital', group.initial_capital);
    }
  }, [group, setValue]);

  const createMutation = useMutation({
    mutationFn: (data: GroupFormData) => groupsApi.createGroup(data),
    onSuccess: () => {
      toast.success('Group created successfully');
      onSuccess();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to create group');
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: GroupFormData) => groupsApi.updateGroup(group!.id, data),
    onSuccess: () => {
      toast.success('Group updated successfully');
      onSuccess();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to update group');
    },
  });

  const onSubmit = (data: GroupFormData) => {
    if (group) {
      updateMutation.mutate(data);
    } else {
      createMutation.mutate(data);
    }
  };

  const isLoading = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white max-h-[90vh] overflow-y-auto">
        <div className="mt-3">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            {group ? 'Edit Group' : 'Add New Group'}
          </h3>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Basic Information */}
              <div className="space-y-4">
                <h4 className="text-md font-medium text-gray-900">Basic Information</h4>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Group Name
                  </label>
                  <input
                    type="text"
                    {...register('name')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.name && (
                    <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Registration Number
                  </label>
                  <input
                    type="text"
                    {...register('registration_number')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.registration_number && (
                    <p className="mt-1 text-sm text-red-600">{errors.registration_number.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Description
                  </label>
                  <textarea
                    {...register('description')}
                    rows={3}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.description && (
                    <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Formation Date
                  </label>
                  <input
                    type="date"
                    {...register('formation_date')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.formation_date && (
                    <p className="mt-1 text-sm text-red-600">{errors.formation_date.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Registration Date
                  </label>
                  <input
                    type="date"
                    {...register('registration_date')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.registration_date && (
                    <p className="mt-1 text-sm text-red-600">{errors.registration_date.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Initial Capital (KES)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    {...register('initial_capital', { valueAsNumber: true })}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.initial_capital && (
                    <p className="mt-1 text-sm text-red-600">{errors.initial_capital.message}</p>
                  )}
                </div>
              </div>

              {/* Location Information */}
              <div className="space-y-4">
                <h4 className="text-md font-medium text-gray-900">Location Information</h4>

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
                    Constituency
                  </label>
                  <input
                    type="text"
                    {...register('constituency')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.constituency && (
                    <p className="mt-1 text-sm text-red-600">{errors.constituency.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Ward
                  </label>
                  <input
                    type="text"
                    {...register('ward')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.ward && (
                    <p className="mt-1 text-sm text-red-600">{errors.ward.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Location
                  </label>
                  <input
                    type="text"
                    {...register('location')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.location && (
                    <p className="mt-1 text-sm text-red-600">{errors.location.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Village
                  </label>
                  <input
                    type="text"
                    {...register('village')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.village && (
                    <p className="mt-1 text-sm text-red-600">{errors.village.message}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Leadership Information */}
            <div className="space-y-4">
              <h4 className="text-md font-medium text-gray-900">Leadership Information</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Chairperson Name
                  </label>
                  <input
                    type="text"
                    {...register('chairperson_name')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.chairperson_name && (
                    <p className="mt-1 text-sm text-red-600">{errors.chairperson_name.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Chairperson Phone
                  </label>
                  <input
                    type="tel"
                    {...register('chairperson_phone')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.chairperson_phone && (
                    <p className="mt-1 text-sm text-red-600">{errors.chairperson_phone.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Chairperson Email
                  </label>
                  <input
                    type="email"
                    {...register('chairperson_email')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.chairperson_email && (
                    <p className="mt-1 text-sm text-red-600">{errors.chairperson_email.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Secretary Name
                  </label>
                  <input
                    type="text"
                    {...register('secretary_name')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.secretary_name && (
                    <p className="mt-1 text-sm text-red-600">{errors.secretary_name.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Treasurer Name
                  </label>
                  <input
                    type="text"
                    {...register('treasurer_name')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {errors.treasurer_name && (
                    <p className="mt-1 text-sm text-red-600">{errors.treasurer_name.message}</p>
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
                {isLoading ? 'Saving...' : (group ? 'Update Group' : 'Create Group')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default GroupForm;

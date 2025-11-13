import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { authApi } from '../utils/api';
import type { User, LoginForm, RegisterForm } from '../types';

export const useAuth = () => {
  const queryClient = useQueryClient();

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: (credentials: LoginForm) => authApi.login(credentials),
    onSuccess: (data) => {
      const { access, refresh } = data.data;
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      queryClient.invalidateQueries({ queryKey: ['profile'] });
    },
  });

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: (userData: RegisterForm) => authApi.register(userData),
    onSuccess: () => {
      // Optionally redirect to login or auto-login
    },
  });

  // Logout mutation
  const logoutMutation = useMutation({
    mutationFn: () => authApi.logout(),
    onSuccess: () => {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      queryClient.clear();
    },
  });

  // Profile query
  const profileQuery = useQuery({
    queryKey: ['profile'],
    queryFn: () => authApi.getProfile(),
    enabled: !!localStorage.getItem('access_token'),
    select: (data) => data.data as User,
  });

  // Check if user is authenticated
  const isAuthenticated = !!localStorage.getItem('access_token') && !profileQuery.isError;

  return {
    login: loginMutation.mutate,
    register: registerMutation.mutate,
    logout: logoutMutation.mutate,
    profile: profileQuery.data,
    isAuthenticated,
    isLoading: profileQuery.isLoading || loginMutation.isPending,
    loginError: loginMutation.error,
    registerError: registerMutation.error,
    logoutError: logoutMutation.error,
  };
};

// API Response Types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// User Types
export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
  is_active: boolean;
  date_joined: string;
  last_login: string | null;
  profile: UserProfile;
}

export interface UserProfile {
  id: number;
  user: number;
  phone_number: string;
  location: string;
  role: string;
  department: string;
  employee_id: string;
}

// Member Types
export interface Member {
  id: number;
  member_number: string;
  user: number;
  group: number;
  first_name: string;
  last_name: string;
  id_number: string;
  phone_number: string;
  email: string;
  date_of_birth: string;
  gender: 'M' | 'F';
  marital_status: string;
  education_level: string;
  occupation: string;
  employer: string;
  monthly_income: number;
  address: string;
  city: string;
  county: string;
  postal_code: string;
  date_joined: string;
  membership_status: string;
  membership_type: string;
  total_savings: number;
  total_loans_taken: number;
  total_loans_repaid: number;
  credit_score: number;
  risk_category: string;
  full_name: string;
  age: number;
  // Verification fields
  id_document_url?: string;
  id_document_preview?: string;
  signature_url?: string;
  verification_status: 'pending' | 'verified' | 'rejected';
  verified_at?: string;
  verified_by?: number;
}

// Group Types
export interface Group {
  id: number;
  name: string;
  registration_number: string;
  description: string;
  county: string;
  constituency: string;
  ward: string;
  location: string;
  village: string;
  chairperson_name: string;
  chairperson_phone: string;
  chairperson_email: string;
  secretary_name: string;
  treasurer_name: string;
  formation_date: string;
  registration_date: string;
  status: string;
  initial_capital: number;
  total_members: number;
  total_savings: number;
  total_loans: number;
  current_balance: number;
}

// Loan Types
export interface Loan {
  id: number;
  loan_number: string;
  loan_type: 'short_term' | 'long_term' | 'top_up' | 'project';
  group: number;
  group_name: string;
  member: number;
  member_name: string;
  principal_amount: number;
  interest_rate: number;
  total_repayable: number;
  total_paid: number;
  current_balance: number;
  application_date: string;
  approval_date: string | null;
  disbursement_date: string | null;
  due_date: string;
  short_term_months: number;
  long_term_months: number;
  status: 'active' | 'completed' | 'defaulted' | 'pending' | 'approved' | 'disbursed';
  monthly_repayment: number;
  repayment_schedule: Date[];
  member_signatures: string[]; // URLs to signed documents
}

// Transaction Types
export interface Transaction {
  id: number;
  group: number;
  transaction_type: string;
  amount: number;
  description: string;
  transaction_date: string;
  receipt_number: string;
  created_by: number;
  created_at: string;
}

// Dividend Types
export interface DividendPeriod {
  id: number;
  year: number;
  is_current_december: boolean;
  can_calculate: boolean;
  calculation_date: string | null;
  net_profit: number;
  total_dividend_pool: number;
  reserve_amount: number;
  development_amount: number;
}

export interface MemberDividend {
  id: number;
  member: number;
  member_name: string;
  dividend_period: number;
  period_year: number;
  amount: number;
  is_visible_to_field_officer: boolean;
  is_visible_to_member: boolean;
}

// Form Types
export interface LoginForm {
  username: string;
  password: string;
}

export interface RegisterForm {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
  first_name: string;
  last_name: string;
}

// API Error Types
export interface ApiError {
  message: string;
  errors?: Record<string, string[]>;
  status: number;
}

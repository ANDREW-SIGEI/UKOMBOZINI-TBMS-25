import { z } from 'zod';

// Auth Schemas
export const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
});

export const registerSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  password_confirm: z.string(),
  first_name: z.string().min(1, 'First name is required'),
  last_name: z.string().min(1, 'Last name is required'),
}).refine((data) => data.password === data.password_confirm, {
  message: "Passwords don't match",
  path: ["password_confirm"],
});

// Member Schemas
export const memberSchema = z.object({
  member_number: z.string().min(1, 'Member number is required'),
  user: z.number().optional(),
  group: z.number().min(1, 'Group is required'),
  first_name: z.string().min(1, 'First name is required'),
  last_name: z.string().min(1, 'Last name is required'),
  id_number: z.string().min(1, 'ID number is required'),
  phone_number: z.string().min(10, 'Phone number must be at least 10 digits'),
  email: z.string().email('Invalid email address'),
  date_of_birth: z.string().min(1, 'Date of birth is required'),
  gender: z.enum(['M', 'F'], { required_error: 'Gender is required' }),
  marital_status: z.string().min(1, 'Marital status is required'),
  education_level: z.string().min(1, 'Education level is required'),
  occupation: z.string().min(1, 'Occupation is required'),
  employer: z.string().optional(),
  monthly_income: z.number().min(0, 'Monthly income must be positive'),
  address: z.string().min(1, 'Address is required'),
  city: z.string().min(1, 'City is required'),
  county: z.string().min(1, 'County is required'),
  postal_code: z.string().optional(),
});

// Group Schemas
export const groupSchema = z.object({
  name: z.string().min(1, 'Group name is required'),
  registration_number: z.string().min(1, 'Registration number is required'),
  description: z.string().optional(),
  county: z.string().min(1, 'County is required'),
  constituency: z.string().min(1, 'Constituency is required'),
  ward: z.string().min(1, 'Ward is required'),
  location: z.string().min(1, 'Location is required'),
  village: z.string().min(1, 'Village is required'),
  chairperson_name: z.string().min(1, 'Chairperson name is required'),
  chairperson_phone: z.string().min(10, 'Chairperson phone must be at least 10 digits'),
  chairperson_email: z.string().email('Invalid chairperson email'),
  secretary_name: z.string().min(1, 'Secretary name is required'),
  treasurer_name: z.string().min(1, 'Treasurer name is required'),
  formation_date: z.string().min(1, 'Formation date is required'),
  registration_date: z.string().min(1, 'Registration date is required'),
  initial_capital: z.number().min(0, 'Initial capital must be positive'),
});

// Loan Schemas
export const loanSchema = z.object({
  loan_type: z.enum(['short_term', 'long_term', 'top_up', 'project'], {
    required_error: 'Loan type is required'
  }),
  group: z.number().min(1, 'Group is required'),
  member: z.number().min(1, 'Member is required'),
  principal_amount: z.number().min(1, 'Principal amount must be greater than 0'),
  interest_rate: z.number().min(0, 'Interest rate must be positive'),
  application_date: z.string().min(1, 'Application date is required'),
  short_term_months: z.number().optional(),
  long_term_months: z.number().optional(),
  purpose: z.string().optional(),
  collateral_details: z.string().optional(),
  guarantor_name: z.string().optional(),
  guarantor_phone: z.string().optional(),
  guarantor_id_number: z.string().optional(),
}).refine((data) => {
  if (data.loan_type === 'short_term' && (!data.short_term_months || data.short_term_months <= 0)) {
    return false;
  }
  if (data.loan_type === 'long_term' && (!data.long_term_months || data.long_term_months <= 0)) {
    return false;
  }
  return true;
}, {
  message: "Please specify the number of months for the selected loan type",
  path: ["short_term_months"],
});

// Transaction Schemas
export const transactionSchema = z.object({
  group: z.number().min(1, 'Group is required'),
  amount: z.number().min(0.01, 'Amount must be greater than 0'),
  description: z.string().min(1, 'Description is required'),
  transaction_date: z.string().min(1, 'Transaction date is required'),
  receipt_number: z.string().min(1, 'Receipt number is required'),
});

// Type exports
export type LoginFormData = z.infer<typeof loginSchema>;
export type RegisterFormData = z.infer<typeof registerSchema>;
export type MemberFormData = z.infer<typeof memberSchema>;
export type GroupFormData = z.infer<typeof groupSchema>;
export type LoanFormData = z.infer<typeof loanSchema>;
export type TransactionFormData = z.infer<typeof transactionSchema>;

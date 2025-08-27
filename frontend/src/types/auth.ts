export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  subscription_tier: 'free' | 'pro' | 'enterprise';
  questions_used_this_month: number;
  questions_used_current_cycle: number;  // Add this line
  is_verified: boolean;
  cycle_reset_time: string | null;  // ← ADD THIS LINE
  
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface Consultation {
  id: string;
  question: string;
  answer: string;
  category?: string;
  processing_time_ms: number;
  timestamp: string;
  user_questions_remaining: number;
}

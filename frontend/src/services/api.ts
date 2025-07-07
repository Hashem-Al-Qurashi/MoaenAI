import axios from 'axios';
import type { 
  User, 
  LoginRequest, 
  RegisterRequest, 
  AuthResponse, 
  Consultation 
} from '../types/auth';

const API_BASE_URL = 'http://moaen-ai-alb-505825922.eu-central-1.elb.amazonaws.com';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

const getToken = (): string | null => {
  return localStorage.getItem('access_token');
};

const setToken = (token: string): void => {
  localStorage.setItem('access_token', token);
};

const removeToken = (): void => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

api.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      removeToken();
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

// In frontend/src/services/api.ts - Replace the entire authAPI object
export const authAPI = {
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await api.post('/api/auth/login', credentials);
    
    const { access_token, refresh_token, expires_in } = response.data;
    setToken(access_token);
    localStorage.setItem('refresh_token', refresh_token);
    
    return response.data;
  },

  async register(userData: RegisterRequest): Promise<User> {
    const response = await api.post('/api/auth/register', userData);
    return response.data;
  },

  async getCurrentUser(): Promise<User> {
  const response = await api.get('/api/chat/status');
  return {
    id: response.data.user_id || response.data.id,
    email: response.data.email,
    full_name: response.data.full_name,
    is_active: response.data.is_active,
    subscription_tier: response.data.subscription_tier,
    questions_used_this_month: response.data.questions_used_this_month,
    questions_used_current_cycle: response.data.questions_used_current_cycle || 0,
    cycle_reset_time: response.data.cycle_reset_time || null,
    is_verified: response.data.is_verified
  };
},

  logout(): void {
    removeToken();
    window.location.href = '/';
  }
};

// Add this to your API interceptors for automatic token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/api/auth/refresh`, {
            refresh_token: refreshToken
          });
          
          const { access_token } = response.data;
          setToken(access_token);
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          
          return api(originalRequest);
        }
      } catch (refreshError) {
        removeToken();
        window.location.href = '/';
      }
    }
    
    if (error.response?.status === 401) {
      removeToken();
      window.location.href = '/';
    }
    
    return Promise.reject(error);
  }
);

export const legalAPI = {
  async askQuestion(question: string, conversationHistory: any[] = []): Promise<Consultation> {
  const formData = new FormData();
  formData.append('query', question);
  
  // Add conversation history for context (if any)
  if (conversationHistory.length > 0) {
    formData.append('context', JSON.stringify(conversationHistory));
  }

  const response = await api.post('/api/ask', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  
  return response.data;
},

  // 🔧 NEW: Get updated user stats after asking question
  async askQuestionWithUserUpdate(question: string): Promise<{consultation: Consultation, updatedUser?: any}> {
    const consultation = await this.askQuestion(question);
    
    // If the response includes updated user data, return it
    if ((consultation as any).updated_user) {
      return {
        consultation,
        updatedUser: (consultation as any).updated_user
      };
    }
    
    // Otherwise, fetch current user stats separately
    try {
      const userStats = await chatAPI.getUserStats();
      return {
        consultation,
        updatedUser: userStats
      };
    } catch (error) {
      console.warn('Failed to fetch updated user stats:', error);
      return { consultation };
    }
  },

  async exportDocx(question: string, answer: string): Promise<void> {
    const response = await api.get('/export/docx', {
      params: { question, answer },
      responseType: 'blob'
    });

    const blob = new Blob([response.data]);
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `legal-response-${Date.now()}.docx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  }
};
export const chatAPI = {
async sendMessage(message: string, conversationId?: string, sessionId?: string): Promise<any> {
  const formData = new FormData();
  formData.append('message', message);
  if (conversationId) {
    formData.append('conversation_id', conversationId);
  }
  if (sessionId) {
    formData.append('session_id', sessionId);
  }

  const response = await api.post('/api/chat/message', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  
  return response.data;
},

  async getConversations(): Promise<any> {
    const response = await api.get('/api/chat/conversations');
    return response.data;
  },

  async getConversationMessages(conversationId: string): Promise<any> {
    const response = await api.get(`/api/chat/conversations/${conversationId}/messages`);
    return response.data;
  },

  async updateConversationTitle(conversationId: string, title: string): Promise<any> {
    const formData = new FormData();
    formData.append('new_title', title);

    const response = await api.put(`/api/chat/conversations/${conversationId}/title`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    
    
    return response.data;
  },

  
  async archiveConversation(conversationId: string): Promise<any> {
    const response = await api.delete(`/api/chat/conversations/${conversationId}`);
    return response.data;
  },

  async getUserStats(): Promise<any> {
  const response = await api.get('/api/chat/status');
  return response.data;
}

  
};

export { getToken, removeToken };
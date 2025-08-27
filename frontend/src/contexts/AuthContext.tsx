import React, { createContext, useContext, useState, useEffect, useMemo, useCallback, type ReactNode } from 'react';
import { authAPI, chatAPI } from '../services/api';
import type { User } from '../types/auth';




interface CooldownInfo {
  questionsUsed: number;
  maxQuestions: number;
  isInCooldown: boolean;
  resetTime: Date | null;
  timeUntilReset: number; // minutes
  canAskQuestion: boolean;
  resetTimeFormatted: string | null; // "4:15 PM"
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isGuest: boolean;
  cooldownInfo: CooldownInfo;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  updateUserData: (userData: Partial<User>) => void;
  refreshUserData: () => Promise<void>;
  incrementQuestionUsage: () => void;
  canSendMessage: () => boolean;
  resetCooldownForTesting: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isGuest, setIsGuest] = useState(true);
  const [cooldownInfo, setCooldownInfo] = useState<CooldownInfo>({
    questionsUsed: 0,
    maxQuestions: 5, // Will be updated based on user type
    isInCooldown: false,
    resetTime: null,
    timeUntilReset: 0,
    canAskQuestion: true,
    resetTimeFormatted: null
  });

  // Real-time countdown timer
  useEffect(() => {
    if (cooldownInfo.isInCooldown && cooldownInfo.resetTime) {
      const interval = setInterval(() => {
        const now = new Date();
        const timeLeft = cooldownInfo.resetTime!.getTime() - now.getTime();
        
        if (timeLeft <= 0) {
          // Cooldown expired - reset
          setCooldownInfo(prev => ({
            ...prev,
            questionsUsed: 0,
            isInCooldown: false,
            resetTime: null,
            timeUntilReset: 0,
            canAskQuestion: true,
            resetTimeFormatted: null
          }));
        } else {
          // Update countdown
          const minutesLeft = Math.ceil(timeLeft / (60 * 1000));
          const resetTimeFormatted = cooldownInfo.resetTime!.toLocaleTimeString('en-US', { 
            hour: 'numeric', 
            minute: '2-digit', 
            hour12: true 
          });
          
          setCooldownInfo(prev => ({
            ...prev,
            timeUntilReset: minutesLeft,
            resetTimeFormatted
          }));
        }
      }, 1000); // Update every second for real-time

      return () => clearInterval(interval);
    }
  }, [cooldownInfo.isInCooldown, cooldownInfo.resetTime]);

  // Update max questions when user type changes
  useEffect(() => {
    const maxQuestions = isGuest ? 5 : 20;
    setCooldownInfo(prev => ({
      ...prev,
      maxQuestions
    }));
  }, [isGuest, user?.subscription_tier]);

  // Sync with user's backend cooldown state
  useEffect(() => {
    if (user && user.cycle_reset_time && user.questions_used_current_cycle !== undefined) {
      const resetTime = new Date(user.cycle_reset_time);
      const now = new Date();
      const maxQuestions = 20;
      const isInCooldown = user.questions_used_current_cycle >= maxQuestions && resetTime > now;
      
      setCooldownInfo(prev => ({
        ...prev,
        questionsUsed: user.questions_used_current_cycle,
        maxQuestions,
        isInCooldown,
        resetTime: isInCooldown ? resetTime : null,
        canAskQuestion: !isInCooldown,
        resetTimeFormatted: isInCooldown ? resetTime.toLocaleTimeString('en-US', { 
          hour: 'numeric', 
          minute: '2-digit', 
          hour12: true 
        }) : null
      }));
    }
  }, [user?.cycle_reset_time, user?.questions_used_current_cycle]);

  const checkAuth = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (token) {
        const currentUser = await authAPI.getCurrentUser();
        setUser(currentUser);
        setIsGuest(false);
      } else {
        setIsGuest(true);
      }
    } catch (error) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setIsGuest(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = useCallback(async (email: string, password: string) => {
    console.log('🔑 Starting login process...');
    await authAPI.login({ email, password });
    console.log('✅ API login successful, getting user data...');
    
    const currentUser = await authAPI.getCurrentUser();
    console.log('👤 User data received:', currentUser.email);
    
    setUser(currentUser);
    setIsGuest(false);
    
    console.log('🎯 Auth state updated, login complete');
    await new Promise(resolve => setTimeout(resolve, 100));
  }, []);

  const register = useCallback(async (email: string, password: string, fullName: string) => {
    console.log('📝 Starting registration process...');
    await authAPI.register({ email, password, full_name: fullName });
    console.log('✅ Registration API successful, logging in...');
    
    await login(email, password);
    console.log('🎯 Registration and login complete');
    await new Promise(resolve => setTimeout(resolve, 100));
  }, [login]);

  const logout = () => {
    authAPI.logout();
    setUser(null);
    setIsGuest(true);
    // Reset cooldown for guests
    setCooldownInfo({
      questionsUsed: 0,
      maxQuestions: 5,
      isInCooldown: false,
      resetTime: null,
      timeUntilReset: 0,
      canAskQuestion: true,
      resetTimeFormatted: null
    });
  };

  const updateUserData = useCallback((userData: Partial<User>) => {
    if (user) {
      console.log('🔄 Updating user data:', userData);
      setUser(prevUser => {
        const hasChanged = Object.keys(userData).some(
          key => prevUser![key as keyof User] !== userData[key as keyof User]
        );
        
        if (hasChanged) {
          const updatedUser = { ...prevUser!, ...userData };
          console.log('🔍 Updated user cooldown data:', {
            questions_used_current_cycle: updatedUser.questions_used_current_cycle,
            cycle_reset_time: updatedUser.cycle_reset_time
          });
          return updatedUser;
        }
        return prevUser!;
      });
    }
  }, [user]);

  const refreshUserData = useCallback(async () => {
    if (!isGuest) {
      try {
        console.log('🔄 Refreshing user data from backend...');
        const userStats = await chatAPI.getUserStats();
        if (userStats && !userStats.error) {
          console.log('✅ User data refreshed:', userStats);
          setUser(prevUser => ({
            ...prevUser!,
            questions_used_current_cycle: userStats.questions_used_current_cycle,
            cycle_reset_time: userStats.cycle_reset_time,
            subscription_tier: userStats.subscription_tier,
            is_active: userStats.is_active,
            is_verified: userStats.is_verified
          }));
        }
      } catch (error) {
        console.warn('⚠️ Failed to refresh user data:', error);
      }
    }
  }, [isGuest]);

  const incrementQuestionUsage = useCallback(() => {
    setCooldownInfo(prev => {
      const newUsed = prev.questionsUsed + 1;
      const maxQuestions = isGuest ? 5 : 20;
      
      if (newUsed >= maxQuestions) {
        const resetTime = new Date(Date.now() + 90 * 60 * 1000); // 1.5 hours
        const resetTimeFormatted = resetTime.toLocaleTimeString('en-US', { 
          hour: 'numeric', 
          minute: '2-digit', 
          hour12: true 
        });
        
        return {
          questionsUsed: newUsed,
          maxQuestions,
          isInCooldown: true,
          resetTime,
          timeUntilReset: 90,
          canAskQuestion: false,
          resetTimeFormatted
        };
      }
      
      return { 
        ...prev, 
        questionsUsed: newUsed, 
        maxQuestions,
        canAskQuestion: true
      };
    });
  }, [isGuest]);

  const canSendMessage = useCallback((): boolean => {
    return cooldownInfo.canAskQuestion;
  }, [cooldownInfo.canAskQuestion]);

  const resetCooldownForTesting = useCallback(() => {
    setCooldownInfo({
      questionsUsed: 0,
      maxQuestions: isGuest ? 5 : 20,
      isInCooldown: false,
      resetTime: null,
      timeUntilReset: 0,
      canAskQuestion: true,
      resetTimeFormatted: null
    });
  }, [isGuest]);

  const value = useMemo(() => ({
    user,
    loading,
    isGuest,
    cooldownInfo,
    login,
    register,
    logout,
    isAuthenticated: !!user,
    updateUserData,
    refreshUserData,
    incrementQuestionUsage,
    canSendMessage,
    resetCooldownForTesting
  }), [
    user,
    loading,
    isGuest,
    cooldownInfo,
    login,
    register,
    updateUserData,
    refreshUserData,
    incrementQuestionUsage,
    canSendMessage,
    resetCooldownForTesting
  ]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};


// New component: frontend/src/components/chat/ChatHistory.tsx
// Chat history sidebar with conversation switching

import React, { useState, useEffect } from 'react';
import { chatAPI } from '../../services/api';

interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  last_message_preview: string | null;
  message_count: number;
}

interface ChatHistoryProps {
  currentConversationId: string | null | undefined;  // ← FIXED
  onConversationSelect: (conversationId: string) => void;
  onNewConversation: () => void;
  isVisible: boolean;
  onToggleVisibility: () => void;
}

const ChatHistory: React.FC<ChatHistoryProps> = ({
  currentConversationId,
  onConversationSelect,
  onNewConversation,
  isVisible,
  onToggleVisibility
}) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load conversations when component mounts or becomes visible
  useEffect(() => {
    if (isVisible) {
      loadConversations();
    }
  }, [isVisible]);

  const loadConversations = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await chatAPI.getConversations();
      setConversations(response.conversations || []);
    } catch (err: any) {
      setError('فشل في تحميل المحادثات');
      console.error('Failed to load conversations:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return 'اليوم';
    if (diffDays === 2) return 'أمس';
    if (diffDays <= 7) return `منذ ${diffDays} أيام`;
    return date.toLocaleDateString('ar-SA');
  };

  const truncateTitle = (title: string, maxLength: number = 40) => {
    return title.length > maxLength ? title.substring(0, maxLength) + '...' : title;
  };

  if (!isVisible) {
    return (
      <button
        onClick={onToggleVisibility}
        style={{
          position: 'fixed',
          top: '100px',
          right: '20px',
          background: 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)',
          color: 'white',
          border: 'none',
          borderRadius: '50%',
          width: '50px',
          height: '50px',
          cursor: 'pointer',
          boxShadow: '0 4px 12px rgba(76, 175, 80, 0.3)',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '20px'
        }}
        title="عرض المحادثات السابقة"
      >
        💬
      </button>
    );
  }

  return (
    <>
      {/* Overlay */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.5)',
          zIndex: 999
        }}
        onClick={onToggleVisibility}
      />
      
      {/* Sidebar */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          right: 0,
          height: '100vh',
          width: '350px',
          background: 'white',
          boxShadow: '-4px 0 20px rgba(0, 0, 0, 0.1)',
          zIndex: 1000,
          display: 'flex',
          flexDirection: 'column',
          fontFamily: "'Noto Sans Arabic', sans-serif"
        }}
      >
        {/* Header */}
        <div
          style={{
            background: 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)',
            color: 'white',
            padding: '20px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <h2 style={{ margin: 0, fontSize: '18px', fontWeight: '600' }}>
            📚 المحادثات السابقة
          </h2>
          <button
            onClick={onToggleVisibility}
            style={{
              background: 'rgba(255, 255, 255, 0.2)',
              border: 'none',
              color: 'white',
              borderRadius: '50%',
              width: '30px',
              height: '30px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            ✕
          </button>
        </div>

        {/* New Conversation Button */}
        <div style={{ padding: '15px', borderBottom: '1px solid #e5e7eb' }}>
          <button
            onClick={() => {
              onNewConversation();
              onToggleVisibility();
            }}
            style={{
              width: '100%',
              background: 'linear-gradient(135deg, #2196F3 0%, #1976D2 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              padding: '12px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px'
            }}
          >
            ➕ محادثة جديدة
          </button>
        </div>

        {/* Conversations List */}
        <div style={{ flex: 1, overflow: 'auto', padding: '10px' }}>
          {loading && (
            <div style={{ textAlign: 'center', padding: '20px', color: '#666' }}>
              <div style={{ 
                width: '20px', 
                height: '20px', 
                border: '2px solid #4CAF50',
                borderTop: '2px solid transparent',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite',
                margin: '0 auto 10px'
              }} />
              جاري التحميل...
            </div>
          )}

          {error && (
            <div style={{
              background: '#fee2e2',
              color: '#dc2626',
              padding: '12px',
              borderRadius: '8px',
              textAlign: 'center',
              margin: '10px 0'
            }}>
              {error}
              <button
                onClick={loadConversations}
                style={{
                  display: 'block',
                  margin: '8px auto 0',
                  background: '#dc2626',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  padding: '4px 8px',
                  cursor: 'pointer',
                  fontSize: '12px'
                }}
              >
                إعادة المحاولة
              </button>
            </div>
          )}

          {!loading && !error && conversations.length === 0 && (
            <div style={{
              textAlign: 'center',
              padding: '40px 20px',
              color: '#6b7280'
            }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>💭</div>
              <h3 style={{ margin: '0 0 8px 0', fontSize: '16px' }}>لا توجد محادثات سابقة</h3>
              <p style={{ margin: 0, fontSize: '14px' }}>ابدأ محادثة جديدة لتظهر هنا</p>
            </div>
          )}

          {!loading && !error && conversations.map((conversation) => (
            <div
              key={conversation.id}
              onClick={() => {
                onConversationSelect(conversation.id);
                onToggleVisibility();
              }}
              style={{
                background: currentConversationId === conversation.id 
                  ? 'linear-gradient(135deg, #e8f5e8 0%, #d4edda 100%)' 
                  : '#f8f9fa',
                border: currentConversationId === conversation.id 
                  ? '2px solid #4CAF50' 
                  : '1px solid #e5e7eb',
                borderRadius: '8px',
                padding: '12px',
                margin: '8px 0',
                cursor: 'pointer',
                transition: 'all 0.2s ease-in-out'
              }}
              onMouseEnter={(e) => {
                if (currentConversationId !== conversation.id) {
                  e.currentTarget.style.background = '#f3f4f6';
                  e.currentTarget.style.transform = 'translateX(-2px)';
                }
              }}
              onMouseLeave={(e) => {
                if (currentConversationId !== conversation.id) {
                  e.currentTarget.style.background = '#f8f9fa';
                  e.currentTarget.style.transform = 'translateX(0)';
                }
              }}
            >
              <div style={{
                fontWeight: '600',
                fontSize: '14px',
                color: '#1f2937',
                marginBottom: '4px',
                lineHeight: '1.3'
              }}>
                {truncateTitle(conversation.title)}
              </div>
              
              {conversation.last_message_preview && (
                <div style={{
                  fontSize: '12px',
                  color: '#6b7280',
                  marginBottom: '6px',
                  lineHeight: '1.3'
                }}>
                  {truncateTitle(conversation.last_message_preview, 60)}
                </div>
              )}
              
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                fontSize: '11px',
                color: '#9ca3af'
              }}>
                <span>{formatDate(conversation.updated_at)}</span>
                <span>{conversation.message_count} رسالة</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Add CSS animation for spinner */}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </>
  );
};

export default ChatHistory;
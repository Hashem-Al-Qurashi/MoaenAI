import React, { useState } from 'react';
import { chatAPI } from '../services/api';

export const DirectChatGPT: React.FC = () => {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<any[]>([]);
  const [showComparison, setShowComparison] = useState(false);
  const [regularResponse, setRegularResponse] = useState('');

  const handleSendMessage = async () => {
    if (!message.trim()) return;

    setLoading(true);
    setResponse('');
    setRegularResponse('');
    
    try {
      // Get direct ChatGPT response
      const directResult = await chatAPI.sendDirectChatGPT(message, history);
      setResponse(directResult.response);
      
      // Update history
      const newHistory = [...history, 
        { role: 'user', content: message },
        { role: 'assistant', content: directResult.response }
      ];
      setHistory(newHistory);

      // If comparison mode is on, also get regular response
      if (showComparison) {
        const regularResult = await chatAPI.sendMessage(
          message, 
          undefined, 
          `test_session_${Date.now()}`
        );
        setRegularResponse(regularResult.ai_message?.content || '');
      }
      
      setMessage('');
    } catch (error) {
      console.error('Error:', error);
      setResponse('Error occurred while fetching response');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h2>Direct ChatGPT Interface</h2>
      <p style={{ color: '#666', marginBottom: '20px' }}>
        This uses the raw ChatGPT API directly without any system prompts or modifications
      </p>
      
      <div style={{ marginBottom: '20px' }}>
        <label>
          <input
            type="checkbox"
            checked={showComparison}
            onChange={(e) => setShowComparison(e.target.checked)}
          />
          Show comparison with regular endpoint
        </label>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Enter your message here..."
          style={{ 
            width: '100%', 
            height: '100px', 
            padding: '10px',
            fontSize: '16px',
            borderRadius: '4px',
            border: '1px solid #ccc'
          }}
        />
        <button 
          onClick={handleSendMessage} 
          disabled={loading}
          style={{
            marginTop: '10px',
            padding: '10px 20px',
            fontSize: '16px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.6 : 1
          }}
        >
          {loading ? 'Loading...' : 'Send to Direct ChatGPT'}
        </button>
      </div>

      <div style={{ display: showComparison ? 'flex' : 'block', gap: '20px' }}>
        <div style={{ flex: 1 }}>
          <h3>Direct ChatGPT Response (Raw):</h3>
          <div style={{ 
            backgroundColor: '#f5f5f5', 
            padding: '15px', 
            borderRadius: '4px',
            minHeight: '200px',
            whiteSpace: 'pre-wrap',
            direction: 'rtl',
            textAlign: 'right'
          }}>
            {response || 'No response yet...'}
          </div>
        </div>

        {showComparison && (
          <div style={{ flex: 1 }}>
            <h3>Regular Endpoint Response:</h3>
            <div style={{ 
              backgroundColor: '#f0f8ff', 
              padding: '15px', 
              borderRadius: '4px',
              minHeight: '200px',
              whiteSpace: 'pre-wrap',
              direction: 'rtl',
              textAlign: 'right'
            }}>
              {regularResponse || 'No response yet...'}
            </div>
          </div>
        )}
      </div>

      <div style={{ marginTop: '20px' }}>
        <button 
          onClick={() => {
            setHistory([]);
            setResponse('');
            setRegularResponse('');
          }}
          style={{
            padding: '8px 16px',
            fontSize: '14px',
            backgroundColor: '#dc3545',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Clear History
        </button>
      </div>

      {history.length > 0 && (
        <div style={{ marginTop: '20px' }}>
          <h4>Conversation History:</h4>
          <div style={{ 
            backgroundColor: '#fafafa', 
            padding: '10px', 
            borderRadius: '4px',
            maxHeight: '200px',
            overflow: 'auto'
          }}>
            {history.map((msg, index) => (
              <div key={index} style={{ marginBottom: '10px' }}>
                <strong>{msg.role === 'user' ? 'You' : 'ChatGPT'}:</strong> {msg.content.slice(0, 100)}...
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
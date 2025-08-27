from openai import AsyncOpenAI
from fastapi import FastAPI, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import os
from dotenv import load_dotenv
import json

load_dotenv()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

@app.post('/api/chat/message')
async def pure_chatgpt(request: Request, message: str = Form(...), session_id: str = Form(None)):
    print(f'🔥 Pure ChatGPT call: {message}')
    
    # Check if streaming is requested
    accept_header = request.headers.get('accept', '')
    is_streaming = 'text/event-stream' in accept_header
    
    response = await client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[{'role': 'user', 'content': message}],
        temperature=1.0
    )
    content = response.choices[0].message.content
    print(f'🔥 Pure ChatGPT response: {content}')
    
    if is_streaming:
        # Return streaming response
        async def generate():
            # Send metadata first
            metadata = {
                'type': 'metadata',
                'id': 'pure_response',
                'conversation_id': session_id
            }
            yield f"data: {json.dumps(metadata)}\n\n"
            
            # Send content in chunks
            words = content.split()
            for i, word in enumerate(words):
                chunk_data = {
                    'type': 'chunk',
                    'content': word + (' ' if i < len(words) - 1 else '')
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"
            
            # Send completion
            complete_data = {
                'type': 'complete',
                'answer': {
                    'id': 'pure_response',
                    'content': content,
                    'timestamp': '2024-01-01T00:00:00Z',
                    'processing_time_ms': 1000
                },
                'conversation_id': session_id
            }
            yield f"data: {json.dumps(complete_data)}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(generate(), media_type='text/event-stream')
    else:
        # Return JSON response
        return {
            'ai_message': {
                'content': content,
                'id': 'pure_chatgpt_response',
                'timestamp': '2024-01-01T00:00:00Z',
                'processing_time_ms': 1000
            },
            'conversation_id': session_id,
            'user_questions_remaining': 999
        }

if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8001)
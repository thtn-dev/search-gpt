import { Thread, Message } from '@/schemas/chat-schema';
import { 
  ApiMessage, 
  CreateMessageRequest, 
  CreateMessageResponse 
} from './types';

const API_BASE_URL = 'http://localhost:8000';

export const apiRequest = async (url: string, options: RequestInit = {}) => {
  const response = await fetch(API_BASE_URL + url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  return response;
};

export const createThreadAsync = async (): Promise<{ thread_id: string }> => {
  const response = await fetch(`${API_BASE_URL}/v1/threads`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      last_message_at: new Date().toISOString()
    })
  });
  
  if (!response.ok) {
    throw new Error(`Failed to create thread: ${response.status}`);
  }
  
  const data = await response.json();
  return { thread_id: data.thread_id };
};

export const fetchThreads = async (): Promise<Thread[]> => {
  const response = await apiRequest('/v1/threads');
  return response.json();
};

export const fetchMessages = async (threadId: string): Promise<Message[]> => {
  const response = await apiRequest(`/v1/threads/${threadId}/messages`);
  const apiMessages: ApiMessage[] = await response.json();

  return apiMessages.map((apiMsg) => ({
    id: apiMsg.id,
    role: apiMsg.role as 'user' | 'assistant',
    content: apiMsg.content.map((item) => item.text).join(''),
    createdAt: new Date(apiMsg.created_at),
    threadId: threadId,
    parentId: apiMsg.parent_id
  }));
};

export const createMessage = async (
  threadId: string,
  messageRequest: CreateMessageRequest
): Promise<CreateMessageResponse> => {
  const response = await apiRequest(`/v1/threads/${threadId}/messages`, {
    method: 'POST',
    body: JSON.stringify(messageRequest)
  });
  
  return response.json();
};

export const streamChatResponse = async (
  messages: Array<{ role: string; content: Array<{ type: string; text: string }> }>,
  assistantMessageId: string
): Promise<ReadableStreamDefaultReader<Uint8Array>> => {
  const chatRequest = {
    messages,
    tools: {},
    unstable_assistantMessageId: assistantMessageId,
    runConfig: {}
  };

  const chatResponse = await fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(chatRequest)
  });

  if (!chatResponse.ok) {
    throw new Error(`Chat API error! status: ${chatResponse.status}`);
  }

  const reader = chatResponse.body?.getReader();
  if (!reader) {
    throw new Error('No response body reader available');
  }

  return reader;
};

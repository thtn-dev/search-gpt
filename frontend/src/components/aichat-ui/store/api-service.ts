'use client';

import { Thread, Message } from '@/schemas/chat-schema';
import { getSession } from 'next-auth/react';
import {
  CreateMessageRequest,
  CreateMessageResponse,
  MessageRequestBase
} from './types';

type ThreadResponse = {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
};

type MessageResponse = {
  message_id: string;
  thread_id: string;
  content: string;
  role: 'user' | 'assistant';
  created_at: string;
  updated_at: string;
};

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

export const createThreadAsync = async (
  title: string
): Promise<{ thread_id: string }> => {
  const session = await getSession();
  console.log(session);
  const response = await fetch(`${API_BASE_URL}/v1/threads`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${session?.user?.accessToken}`
    },
    body: JSON.stringify({
      title
    })
  });

  if (!response.ok) {
    throw new Error(`Failed to create thread: ${response.status}`);
  }

  const data = await response.json();
  return { thread_id: data.thread_id };
};

export const fetchThreads = async (): Promise<Thread[]> => {
  const session = await getSession();
  const response = await apiRequest('/v1/threads', {
    headers: {
      Authorization: `Bearer ${session?.user?.accessToken}`
    }
  });
  const data = (await response.json()) as ThreadResponse[];
  return data.map((thread) => ({
    id: thread.id,
    title: thread.title,
    createdAt: new Date(thread.created_at),
    updatedAt: new Date(thread.updated_at)
  }));
};

export const fetchMessages = async (threadId: string): Promise<Message[]> => {
  const session = await getSession();
  const response = await apiRequest(`/v1/threads/${threadId}/messages`, {
    headers: {
      Authorization: `Bearer ${session?.user?.accessToken}`
    }
  });
  const apiMessages: MessageResponse[] = await response.json();

  return apiMessages.map((msg) => ({
    messageId: msg.message_id,
    threadId: msg.thread_id,
    content: msg.content,
    role: msg.role,
    createdAt: new Date(msg.created_at)
  }));
};

export const createMessage = async (
  threadId: string,
  messageRequest: CreateMessageRequest
): Promise<CreateMessageResponse> => {
  const session = await getSession();
  const response = await apiRequest(`/v1/threads/${threadId}/messages`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${session?.user?.accessToken}`
    },
    body: JSON.stringify(messageRequest)
  });
  return response.json();
};

export const getThreadById = async (
  threadId: string
): Promise<Thread | null> => {
  const session = await getSession();
  const response = await apiRequest(`/v1/threads/${threadId}`, {
    headers: {
      Authorization: `Bearer ${session?.user?.accessToken}`
    }
  });
  if (!response.ok) {
    if (response.status === 404) {
      return null; // Thread not found
    }
    throw new Error(`Failed to fetch thread: ${response.status}`);
  }
  const data = (await response.json()) as ThreadResponse;
  return {
    id: data.id,
    title: data.title,
    createdAt: new Date(data.created_at),
    updatedAt: new Date(data.updated_at)
  };
};

export const streamChatResponse = async (
  messageContent: MessageRequestBase,
  history: Array<[string, string]>
): Promise<ReadableStreamDefaultReader<Uint8Array>> => {
  const chatRequest = {
    history,
    system_instructions: 'You are a helpful assistant.',
    message: messageContent
  };
  const session = await getSession();

  const chatResponse = await fetch(API_BASE_URL + '/v1/stream2', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${session?.user?.accessToken}`
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

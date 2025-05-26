'use client';

import React, { ReactNode, useContext, useReducer, createContext } from 'react';
import { Message, Thread } from '@/schemas/chat-schema';

/* eslint-disable @typescript-eslint/no-explicit-any */

type ApiContentItem = {
  type: string;
  text: string;
};

type ApiContent = {
  role: string;
  content: ApiContentItem[];
  metadata: {
    custom?: Record<string, any>;
    unstable_annotations?: any[];
    unstable_data?: any[];
    steps?: Array<{
      state?: string;
      messageId?: string;
      finishReason?: string;
      isContinued?: boolean;
      usage?: {
        promptTokens?: number;
        completionTokens?: number;
      };
    }>;
  };
};

type CreateMessageRequest = {
  parent_id?: string;
  format: string;
  content: ApiContent;
};

type CreateMessageResponse = {
  message_id: string;
};

type ApiMessage = {
  id: string;
  role: string;
  content: ApiContentItem[];
  created_at: string;
  parent_id?: string;
  metadata?: any;
};

export type ChatState = {
  threads: Thread[];
  messages: Message[];
  currentThreadId: string | null;
  isLoading: boolean;
  error: string | null;
  isLoadingMessages: boolean;
  isLoadingThreads?: boolean;
};

export type ChatAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_LOADING_THREADS'; payload: boolean }
  | { type: 'SET_LOADING_MESSAGES'; payload: boolean }
  | { type: 'CREATE_THREAD'; payload: { id: string; title: string } }
  | { type: 'SET_CURRENT_THREAD'; payload: string }
  | { type: 'SET_THREADS'; payload: Thread[] }
  | { type: 'ADD_MESSAGE'; payload: Message }
  | {
      type: 'UPDATE_MESSAGE';
      payload: { id: string; content: string; isStreaming?: boolean };
    }
  | { type: 'SET_MESSAGES'; payload: Message[] }
  | { type: 'DELETE_THREAD'; payload: string }
  | {
      type: 'UPDATE_THREAD_TITLE';
      payload: { threadId: string; title: string };
    }
  | { type: 'CLEAR_MESSAGES'; payload: string };

const initialState: ChatState = {
  threads: [],
  messages: [],
  currentThreadId: null,
  isLoading: false,
  error: null,
  isLoadingMessages: false
};

function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_LOADING_THREADS':
      return { ...state, isLoadingThreads: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };

    case 'SET_LOADING_MESSAGES':
      return { ...state, isLoadingMessages: action.payload };

    case 'CREATE_THREAD':
      const newThread: Thread = {
        id: action.payload.id,
        title: action.payload.title,
        createdAt: new Date(),
        updatedAt: new Date()
      };
      return {
        ...state,
        threads: [newThread, ...state.threads],
        currentThreadId: action.payload.id
      };

    case 'SET_CURRENT_THREAD':
      return { ...state, currentThreadId: action.payload };

    case 'SET_THREADS':
      return { ...state, threads: action.payload };

    case 'ADD_MESSAGE':
      return {
        ...state,
        messages: [...state.messages, action.payload],
        threads: state.threads.map((thread) =>
          thread.id === action.payload.threadId
            ? { ...thread, updatedAt: new Date() }
            : thread
        )
      };

    case 'UPDATE_MESSAGE':
      return {
        ...state,
        messages: state.messages.map((message) =>
          message.id === action.payload.id
            ? {
                ...message,
                content: action.payload.content,
                isStreaming: action.payload.isStreaming
              }
            : message
        )
      };

    case 'SET_MESSAGES':
      return { ...state, messages: action.payload };

    case 'DELETE_THREAD':
      const updatedThreads = state.threads.filter(
        (thread) => thread.id !== action.payload
      );
      return {
        ...state,
        threads: updatedThreads,
        messages: state.messages.filter(
          (message) => message.threadId !== action.payload
        ),
        currentThreadId:
          state.currentThreadId === action.payload
            ? updatedThreads.length > 0
              ? updatedThreads[0].id
              : null
            : state.currentThreadId
      };

    case 'UPDATE_THREAD_TITLE':
      return {
        ...state,
        threads: state.threads.map((thread) =>
          thread.id === action.payload.threadId
            ? { ...thread, title: action.payload.title, updatedAt: new Date() }
            : thread
        )
      };

    case 'CLEAR_MESSAGES':
      return {
        ...state,
        messages: state.messages.filter(
          (message) => message.threadId !== action.payload
        ),
        threads: state.threads.map((thread) =>
          thread.id === action.payload
            ? { ...thread, updatedAt: new Date() }
            : thread
        )
      };

    default:
      return state;
  }
}

export type ChatContextType = {
  state: ChatState;
  dispatch: React.Dispatch<ChatAction>;
  // Helper functions
  createThread: (title?: string) => Promise<string>;
  loadThreads: () => Promise<void>;
  sendMessage: (
    content: string,
    files: File[],
    threadId?: string
  ) => Promise<void>;
  loadMessages: (threadId: string) => Promise<void>;
  deleteThread: (threadId: string) => void;
  updateThreadTitle: (threadId: string, title: string) => void;
  getCurrentThread: () => Thread | null;
  getCurrentMessages: () => Message[];
  clearMessages: (threadId: string) => void;
  switchThread: (threadId: string) => Promise<void>;
};

const ChatContext = createContext<ChatContextType | undefined>(undefined);

const handleCreateThreadAsync = async (): Promise<{
  thread_id: string;
}> => {
  const endpoint = 'http://localhost:8000/v1/threads';
  const response = await fetch(endpoint, {
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

const apiRequest = async (url: string, options: RequestInit = {}) => {
  const response = await fetch('http://localhost:8000' + url, {
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

export function ChatProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(chatReducer, initialState);

  const createThread = React.useCallback(
    async (title?: string): Promise<string> => {
      const threadTitle = title || `Chat ${new Date().toLocaleString()}`;
      dispatch({ type: 'SET_LOADING', payload: true });

      // Create thread in backend
      try {
        const data = await handleCreateThreadAsync();
        dispatch({
          type: 'CREATE_THREAD',
          payload: { id: data.thread_id, title: threadTitle }
        });

        return data.thread_id;
      } catch (error) {
        console.error('Create thread error:', error);
        dispatch({
          type: 'SET_ERROR',
          payload:
            error instanceof Error ? error.message : 'Failed to create thread'
        });
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
      return '';
    },
    []
  );

  const loadThreads = React.useCallback(async (): Promise<void> => {
    dispatch({ type: 'SET_LOADING_THREADS', payload: true });

    try {
      const response = await apiRequest('/v1/threads');
      const threads: Thread[] = await response.json();
      dispatch({ type: 'SET_THREADS', payload: threads });
    } catch (error) {
      console.error('Load threads error:', error);
      dispatch({
        type: 'SET_ERROR',
        payload:
          error instanceof Error ? error.message : 'Failed to load threads'
      });
    } finally {
      dispatch({ type: 'SET_LOADING_THREADS', payload: false });
    }
  }, []);

  const loadMessages = React.useCallback(
    async (threadId: string): Promise<void> => {
      dispatch({ type: 'SET_LOADING_MESSAGES', payload: true });

      try {
        const response = await apiRequest(`/v1/threads/${threadId}/messages`);
        const apiMessages: ApiMessage[] = await response.json();

        // Convert API messages to internal format
        const messages: Message[] = apiMessages.map((apiMsg) => ({
          id: apiMsg.id,
          role: apiMsg.role as 'user' | 'assistant',
          content: apiMsg.content.map((item) => item.text).join(''),
          createdAt: new Date(apiMsg.created_at),
          threadId: threadId,
          parentId: apiMsg.parent_id
        }));

        // Filter out messages from other threads and add new ones
        const otherThreadMessages = state.messages.filter(
          (msg) => msg.threadId !== threadId
        );
        dispatch({
          type: 'SET_MESSAGES',
          payload: [...otherThreadMessages, ...messages]
        });
      } catch (error) {
        console.error('Load messages error:', error);
        dispatch({
          type: 'SET_ERROR',
          payload:
            error instanceof Error ? error.message : 'Failed to load messages'
        });
      } finally {
        dispatch({ type: 'SET_LOADING_MESSAGES', payload: false });
      }
    },
    [state.messages]
  );

  const switchThread = async (threadId: string): Promise<void> => {
    dispatch({ type: 'SET_CURRENT_THREAD', payload: threadId });
    await loadMessages(threadId);
  };

  const sendMessage = React.useCallback(
    async (
      content: string,
      files: File[] = [],
      threadId?: string
    ): Promise<void> => {
      const targetThreadId = threadId || state.currentThreadId;
      console.log('files', files);
      if (!targetThreadId) {
        throw new Error('No active thread');
      }
      const fakeParentId_UUID = '00000000-0000-0000-0000-000000000000';
      try {
        const userMessageRequest: CreateMessageRequest = {
          parent_id: fakeParentId_UUID,
          format: 'markdown',
          content: {
            role: 'user',
            content: [
              {
                type: 'text',
                text: content
              }
            ],
            metadata: {
              custom: {}
            }
          }
        };

        const userResponse = await apiRequest(
          `/v1/threads/${targetThreadId}/messages`,
          {
            method: 'POST',
            body: JSON.stringify(userMessageRequest)
          }
        );

        const userResult: CreateMessageResponse = await userResponse.json();

        const userMessage: Message = {
          id: userResult.message_id,
          role: 'user',
          content,
          createdAt: new Date(),
          threadId: targetThreadId,
          parentId: fakeParentId_UUID
        };

        dispatch({ type: 'ADD_MESSAGE', payload: userMessage });

        const assistantMessageId = `temp-assistant-${Date.now()}`;
        const assistantMessage: Message = {
          id: assistantMessageId,
          role: 'assistant',
          content: '',
          createdAt: new Date(),
          threadId: targetThreadId,
          parentId: userResult.message_id,
          isStreaming: true
        };

        dispatch({ type: 'ADD_MESSAGE', payload: assistantMessage });

        const threadMessages = state.messages
          .filter((msg) => msg.threadId === targetThreadId)
          .concat([userMessage]);

        const apiMessages = threadMessages.map((msg) => ({
          role: msg.role,
          content: [
            {
              type: 'text',
              text: msg.content
            }
          ]
        }));

        const chatRequest = {
          messages: apiMessages,
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

        const decoder = new TextDecoder();
        let streamingContent = '';

        // Process streaming response
        while (true) {
          const { done, value } = await reader.read();

          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.trim() === '') continue;

            if (line.startsWith('0:"')) {
              const match = line.match(/^0:"(.*)"/);
              if (match) {
                const textContent = match[1]
                  .replace(/\\n/g, '\n')
                  .replace(/\\"/g, '"')
                  .replace(/\\\\/g, '\\');

                streamingContent += textContent;

                dispatch({
                  type: 'UPDATE_MESSAGE',
                  payload: {
                    id: assistantMessageId,
                    content: streamingContent,
                    isStreaming: true
                  }
                });
              }
            } else if (line.startsWith('e:') || line.startsWith('d:')) {
              break;
            }
          }
        }

        // Save final assistant message to backend
        const assistantMessageRequest: CreateMessageRequest = {
          parent_id: userResult.message_id,
          format: 'markdown',
          content: {
            role: 'assistant',
            content: [
              {
                type: 'text',
                text: streamingContent.trim()
              }
            ],
            metadata: {
              unstable_annotations: [],
              unstable_data: [],
              steps: [
                {
                  state: 'finished',
                  finishReason: 'stop',
                  isContinued: false,
                  usage: {}
                }
              ],
              custom: {}
            }
          }
        };

        const assistantResponse = await apiRequest(
          `/v1/threads/${targetThreadId}/messages`,
          {
            method: 'POST',
            body: JSON.stringify(assistantMessageRequest)
          }
        );
        const assistantResult: CreateMessageResponse =
          await assistantResponse.json();

        // dispatch({
        //   type: 'SET_MESSAGES',
        //   payload: state.messages.map((msg) =>
        //     msg.id === assistantMessageId
        //       ? {
        //           ...msg,
        //           id: assistantResult.message_id,
        //           content: streamingContent.trim(),
        //           isStreaming: false
        //         }
        //       : msg
        //   )
        // });
      } catch (error) {
        console.error('Send message error:', error);
        dispatch({
          type: 'SET_ERROR',
          payload:
            error instanceof Error ? error.message : 'Unknown error occurred'
        });
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    },
    [state.currentThreadId, state.messages]
  );

  const deleteThread = (threadId: string) => {
    dispatch({ type: 'DELETE_THREAD', payload: threadId });
  };

  const updateThreadTitle = (threadId: string, title: string) => {
    dispatch({ type: 'UPDATE_THREAD_TITLE', payload: { threadId, title } });
  };

  const getCurrentThread = (): Thread | null => {
    if (!state.currentThreadId) return null;
    return (
      state.threads.find((thread) => thread.id === state.currentThreadId) ||
      null
    );
  };

  const getCurrentMessages = (): Message[] => {
    if (!state.currentThreadId) return [];
    return state.messages.filter(
      (message) => message.threadId === state.currentThreadId
    );
  };

  const clearMessages = (threadId: string) => {
    dispatch({ type: 'CLEAR_MESSAGES', payload: threadId });
  };

  const contextValue: ChatContextType = {
    state,
    dispatch,
    createThread,
    sendMessage,
    loadMessages,
    deleteThread,
    loadThreads,
    updateThreadTitle,
    getCurrentThread,
    getCurrentMessages,
    clearMessages,
    switchThread
  };

  return (
    <ChatContext.Provider value={contextValue}>{children}</ChatContext.Provider>
  );
}

export function useChatContext(): ChatContextType {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChatContext must be used within a ChatProvider');
  }
  return context;
}

// Hook để sử dụng thread hiện tại
export function useCurrentThread(): Thread | null {
  const { getCurrentThread } = useChatContext();
  return getCurrentThread();
}

// Hook để lấy messages của thread hiện tại
export function useCurrentMessages(): Message[] {
  const { getCurrentMessages } = useChatContext();
  return getCurrentMessages();
}

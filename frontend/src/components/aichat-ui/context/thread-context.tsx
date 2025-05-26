'use client';

import React, { ReactNode, useContext, useReducer, createContext } from 'react';
import { Message, Thread } from '@/schemas/chat-schema';

export type ChatState = {
  threads: Thread[];
  messages: Message[];
  currentThreadId: string | null;
  isLoading: boolean;
  error: string | null;
  isLoadingMessages: boolean;
};

export type ChatAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
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
  createThread: (title?: string) => string;
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

export function ChatProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(chatReducer, initialState);

  const createThread = React.useCallback((title?: string): string => {
    const id = `thread-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const threadTitle = title || `Chat ${new Date().toLocaleString()}`;

    dispatch({
      type: 'CREATE_THREAD',
      payload: { id, title: threadTitle }
    });

    return id;
  }, []);

  const loadMessages = async (threadId: string): Promise<void> => {
    dispatch({ type: 'SET_LOADING_MESSAGES', payload: true });

    try {
      // Call API to load messages for specific thread
      const response = await fetch(`/api/threads/${threadId}/messages`);
      if (!response.ok) {
        throw new Error(`Failed to load messages: ${response.status}`);
      }

      const messages: Message[] = await response.json();

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
  };

  const switchThread = async (threadId: string): Promise<void> => {
    dispatch({ type: 'SET_CURRENT_THREAD', payload: threadId });
    await loadMessages(threadId);
  };

  const sendMessage = async (
    content: string,
    files: File[] = [],
    threadId?: string
  ): Promise<void> => {
    const targetThreadId = threadId || state.currentThreadId;
    console.log('files', files);
    if (!targetThreadId) {
      throw new Error('No active thread');
    }

    // Generate message IDs
    const userMessageId = `msg-user-${Date.now()}`;
    const assistantMessageId = `msg-assistant-${Date.now() + 1}`;

    // Add user message immediately
    const userMessage: Message = {
      id: userMessageId,
      role: 'user',
      content,
      createdAt: new Date(),
      threadId: targetThreadId
    };

    dispatch({ type: 'ADD_MESSAGE', payload: userMessage });
    dispatch({ type: 'SET_LOADING', payload: true });

    // Add empty assistant message for streaming
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      createdAt: new Date(),
      threadId: targetThreadId
    };

    dispatch({ type: 'ADD_MESSAGE', payload: assistantMessage });

    try {
      // Get current thread messages for context
      const threadMessages = state.messages.filter(
        (msg) => msg.threadId === targetThreadId
      );

      // Format messages for API (exclude the streaming assistant message)
      const apiMessages = [...threadMessages, userMessage].map((msg) => ({
        role: msg.role,
        content: [
          {
            type: 'text',
            text: msg.content
          }
        ]
      }));

      const requestBody = {
        messages: apiMessages,
        tools: {},
        unstable_assistantMessageId: assistantMessageId,
        runConfig: {}
      };

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body reader available');
      }

      const decoder = new TextDecoder();
      let streamingContent = '';

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.trim() === '') continue;

          // Parse streaming data
          if (line.startsWith('0:"')) {
            const match = line.match(/^0:"(.*)"/);
            if (match) {
              const textContent = match[1]
                .replace(/\\n/g, '\n')
                .replace(/\\"/g, '"')
                .replace(/\\\\/g, '\\');

              streamingContent += textContent;

              // Update assistant message content
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
            // End of stream
            break;
          }
        }
      }

      // Mark message as complete
      dispatch({
        type: 'UPDATE_MESSAGE',
        payload: {
          id: assistantMessageId,
          content: streamingContent.trim(),
          isStreaming: false
        }
      });
    } catch (error) {
      console.error('Send message error:', error);
      dispatch({
        type: 'SET_ERROR',
        payload:
          error instanceof Error ? error.message : 'Unknown error occurred'
      });

      // Remove the failed assistant message
      dispatch({
        type: 'SET_MESSAGES',
        payload: state.messages.filter((msg) => msg.id !== assistantMessageId)
      });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

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

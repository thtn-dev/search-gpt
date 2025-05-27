'use client';

import React, { ReactNode, useReducer, createContext, useCallback } from 'react';
import { Message, Thread } from '@/schemas/chat-schema';
import { ChatContextType, CreateMessageRequest } from './types';
import { chatReducer, initialState } from './chat-reducer';
import { 
  createThreadAsync, 
  fetchThreads, 
  fetchMessages, 
  createMessage,
  streamChatResponse 
} from './api-service';
import { processStreamingResponse } from './streaming-service';

export const ChatContext = createContext<ChatContextType | undefined>(undefined);

const FAKE_PARENT_ID = '00000000-0000-0000-0000-000000000000';

export function ChatProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(chatReducer, initialState);

  const createThread = useCallback(async (title?: string): Promise<string> => {
    const threadTitle = title || `Chat ${new Date().toLocaleString()}`;
    dispatch({ type: 'SET_LOADING', payload: true });

    try {
      const data = await createThreadAsync();
      dispatch({
        type: 'CREATE_THREAD',
        payload: { id: data.thread_id, title: threadTitle }
      });
      return data.thread_id;
    } catch (error) {
      console.error('Create thread error:', error);
      dispatch({
        type: 'SET_ERROR',
        payload: error instanceof Error ? error.message : 'Failed to create thread'
      });
      return '';
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, []);

  const loadThreads = useCallback(async (): Promise<void> => {
    dispatch({ type: 'SET_LOADING_THREADS', payload: true });

    try {
      const threads = await fetchThreads();
      dispatch({ type: 'SET_THREADS', payload: threads });
    } catch (error) {
      console.error('Load threads error:', error);
      dispatch({
        type: 'SET_ERROR',
        payload: error instanceof Error ? error.message : 'Failed to load threads'
      });
    } finally {
      dispatch({ type: 'SET_LOADING_THREADS', payload: false });
    }
  }, []);

  const loadMessages = useCallback(async (threadId: string): Promise<void> => {
    dispatch({ type: 'SET_LOADING_MESSAGES', payload: true });

    try {
      const messages = await fetchMessages(threadId);
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
        payload: error instanceof Error ? error.message : 'Failed to load messages'
      });
    } finally {
      dispatch({ type: 'SET_LOADING_MESSAGES', payload: false });
    }
  }, [state.messages]);

  const switchThread = useCallback(async (threadId: string): Promise<void> => {
    dispatch({ type: 'SET_CURRENT_THREAD', payload: threadId });
    await loadMessages(threadId);
  }, [loadMessages]);

  const sendMessage = useCallback(async (
    content: string,
    files: File[] = [],
    threadId?: string
  ): Promise<void> => {
    const targetThreadId = threadId || state.currentThreadId;
    console.log('files', files);
    
    if (!targetThreadId) {
      throw new Error('No active thread');
    }

    try {
      // Create user message
      const userMessageRequest: CreateMessageRequest = {
        parent_id: FAKE_PARENT_ID,
        format: 'markdown',
        content: {
          role: 'user',
          content: [{ type: 'text', text: content }],
          metadata: { custom: {} }
        }
      };

      const userResult = await createMessage(targetThreadId, userMessageRequest);
      const userMessage: Message = {
        id: userResult.message_id,
        role: 'user',
        content,
        createdAt: new Date(),
        threadId: targetThreadId,
        parentId: FAKE_PARENT_ID
      };

      dispatch({ type: 'ADD_MESSAGE', payload: userMessage });

      // Create temporary assistant message
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

      // Prepare messages for chat API
      const threadMessages = state.messages
        .filter((msg) => msg.threadId === targetThreadId)
        .concat([userMessage]);

      const apiMessages = threadMessages.map((msg) => ({
        role: msg.role,
        content: [{ type: 'text', text: msg.content }]
      }));

      // Stream chat response
      const reader = await streamChatResponse(apiMessages, assistantMessageId);
      
      const finalContent = await processStreamingResponse(reader, (streamingContent) => {
        dispatch({
          type: 'UPDATE_MESSAGE',
          payload: {
            id: assistantMessageId,
            content: streamingContent,
            isStreaming: true
          }
        });
      });

      // Save final assistant message to backend
      const assistantMessageRequest: CreateMessageRequest = {
        parent_id: userResult.message_id,
        format: 'markdown',
        content: {
          role: 'assistant',
          content: [{ type: 'text', text: finalContent }],
          metadata: {
            unstable_annotations: [],
            unstable_data: [],
            steps: [{
              state: 'finished',
              finishReason: 'stop',
              isContinued: false,
              usage: {}
            }],
            custom: {}
          }
        }
      };

      await createMessage(targetThreadId, assistantMessageRequest);

      // Update message to final state
      dispatch({
        type: 'UPDATE_MESSAGE',
        payload: {
          id: assistantMessageId,
          content: finalContent,
          isStreaming: false
        }
      });

    } catch (error) {
      console.error('Send message error:', error);
      dispatch({
        type: 'SET_ERROR',
        payload: error instanceof Error ? error.message : 'Unknown error occurred'
      });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [state.currentThreadId, state.messages]);

  const deleteThread = useCallback((threadId: string) => {
    dispatch({ type: 'DELETE_THREAD', payload: threadId });
  }, []);

  const updateThreadTitle = useCallback((threadId: string, title: string) => {
    dispatch({ type: 'UPDATE_THREAD_TITLE', payload: { threadId, title } });
  }, []);

  const getCurrentThread = useCallback((): Thread | null => {
    if (!state.currentThreadId) return null;
    return state.threads.find((thread) => thread.id === state.currentThreadId) || null;
  }, [state.currentThreadId, state.threads]);

  const getCurrentMessages = useCallback((): Message[] => {
    if (!state.currentThreadId) return [];
    return state.messages.filter((message) => message.threadId === state.currentThreadId);
  }, [state.currentThreadId, state.messages]);

  const clearMessages = useCallback((threadId: string) => {
    dispatch({ type: 'CLEAR_MESSAGES', payload: threadId });
  }, []);

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
    <ChatContext.Provider value={contextValue}>
      {children}
    </ChatContext.Provider>
  );
}

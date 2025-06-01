'use client';

import React, {
  ReactNode,
  useReducer,
  createContext,
  useCallback
} from 'react';
import { Message, Thread } from '@/schemas/chat-schema';
import crypto from 'crypto';
import {
  createThreadAsync,
  fetchThreads,
  fetchMessages,
  createMessage,
  streamChatResponse
} from './api-service';
import { chatReducer, initialState } from './chat-reducer';
import { processStreamingResponse } from './streaming-service';
import { ChatContextType, CreateMessageRequest } from './types';

function genMessageId() {
  const timestamp = Date.now() * 1000; // microseconds (approximate)
  const hexPart = crypto.randomBytes(8).toString('hex');
  return `${timestamp.toString(16)}-${hexPart}`;
}

export const ChatContext = createContext<ChatContextType | undefined>(
  undefined
);

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
        payload:
          error instanceof Error ? error.message : 'Failed to create thread'
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
        payload:
          error instanceof Error ? error.message : 'Failed to load threads'
      });
    } finally {
      dispatch({ type: 'SET_LOADING_THREADS', payload: false });
    }
  }, []);

  const loadMessages = useCallback(async (threadId: string): Promise<void> => {
    dispatch({ type: 'SET_LOADING_MESSAGES', payload: true });

    try {
      const messages = await fetchMessages(threadId);

      dispatch({
        type: 'SET_MESSAGES',
        payload: messages
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
  }, []);

  const switchThread = useCallback(
    async (threadId: string): Promise<void> => {
      dispatch({ type: 'SET_CURRENT_THREAD', payload: threadId });
      await loadMessages(threadId);
    },
    [loadMessages]
  );

  const sendMessage = useCallback(
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

      try {
        // Create user message
        const userMessageRequest: CreateMessageRequest = {
          content,
          thread_id: targetThreadId,
          message_id: genMessageId(),
          role: 'user'
        };

        const userResult = await createMessage(
          targetThreadId,
          userMessageRequest
        );
        const userMessage: Message = {
          messageId: userResult.message_id,
          role: 'user',
          content,
          createdAt: new Date(),
          threadId: targetThreadId,
          parentId: FAKE_PARENT_ID
        };

        dispatch({ type: 'ADD_MESSAGE', payload: userMessage });

        // Create temporary assistant message
        const assistantMessageId = genMessageId();
        const assistantMessage: Message = {
          messageId: assistantMessageId,
          role: 'assistant',
          content: '',
          createdAt: new Date(),
          threadId: targetThreadId,
          parentId: userResult.message_id
        };

        dispatch({ type: 'ADD_MESSAGE', payload: assistantMessage });

        // Prepare messages for chat API
        const threadMessages = state.messages
          .filter((msg) => msg.threadId === targetThreadId)
          .concat([userMessage]);

        const history = threadMessages.map((msg) => [
          msg.role,
          msg.content
        ]) as Array<[string, string]>;

        // Stream chat response
        const reader = await streamChatResponse(
          {
            content: content,
            message_id: userResult.message_id,
            thread_id: targetThreadId
          },
          history
        );

        const finalContent = await processStreamingResponse(
          reader,
          (streamingContent) => {
            dispatch({
              type: 'UPDATE_MESSAGE',
              payload: {
                messageId: assistantMessageId,
                content: streamingContent,
                isStreaming: true
              }
            });
          },
          () => {},
          () => {},
          () => {},
          true
        );

        // Save final assistant message to backend
        const assistantMessageRequest: CreateMessageRequest = {
          message_id: assistantMessageId,
          thread_id: targetThreadId,
          content: finalContent.content,
          role: 'assistant'
        };

        await createMessage(targetThreadId, assistantMessageRequest);

        // Update message to final state
        dispatch({
          type: 'UPDATE_MESSAGE',
          payload: {
            messageId: assistantMessageId,
            content: finalContent.content,
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
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    },
    [state.currentThreadId, state.messages]
  );

  const deleteThread = useCallback((threadId: string) => {
    dispatch({ type: 'DELETE_THREAD', payload: threadId });
  }, []);

  const updateThreadTitle = useCallback((threadId: string, title: string) => {
    dispatch({ type: 'UPDATE_THREAD_TITLE', payload: { threadId, title } });
  }, []);

  const getCurrentThread = useCallback((): Thread | null => {
    if (!state.currentThreadId) return null;
    return (
      state.threads.find((thread) => thread.id === state.currentThreadId) ||
      null
    );
  }, [state.currentThreadId, state.threads]);

  const getCurrentMessages = useCallback((): Message[] => {
    if (!state.currentThreadId) return [];
    return state.messages.filter(
      (message) => message.threadId === state.currentThreadId
    );
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
    <ChatContext.Provider value={contextValue}>{children}</ChatContext.Provider>
  );
}

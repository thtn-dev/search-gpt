import { Message, Thread } from '@/schemas/chat-schema';
import crypto from 'crypto';
import { create } from 'zustand';
import { subscribeWithSelector, devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import {
  createThreadAsync,
  fetchThreads,
  fetchMessages,
  createMessage,
  streamChatResponse
} from './api-service';
import { processStreamingResponse } from './streaming-service';
import { CreateMessageRequest } from './types';

// Types
interface ChatState {
  // State
  threads: Thread[];
  messages: Message[];
  currentThreadId: string | null;
  currentThread: Thread | null;
  isLoading: boolean;
  error: string | null;
  isLoadingMessages: boolean;
  isLoadingThreads: boolean;

  // Actions
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setLoadingThreads: (loading: boolean) => void;
  setLoadingMessages: (loading: boolean) => void;

  // Thread actions
  createThread: (title?: string) => Promise<string>;
  loadThreads: () => Promise<void>;
  switchThread: (threadId: string) => Promise<void>;
  deleteThread: (threadId: string) => void;
  updateThreadTitle: (threadId: string, title: string) => void;

  // Message actions
  loadMessages: (threadId: string) => Promise<void>;
  sendMessage: (
    content: string,
    files?: File[],
    threadId?: string
  ) => Promise<void>;
  addMessage: (message: Message) => void;
  updateMessage: (
    messageId: string,
    content: string,
    isStreaming?: boolean
  ) => void;
  clearMessages: (threadId: string) => void;
}

// Helper functions
function genMessageId(): string {
  const timestamp = Date.now() * 1000;
  const hexPart = crypto.randomBytes(8).toString('hex');
  return `${timestamp.toString(16)}-${hexPart}`;
}

const FAKE_PARENT_ID = '00000000-0000-0000-0000-000000000000';

// Zustand store
export const useChatStore = create<ChatState>()(
  devtools(
    subscribeWithSelector(
      immer<ChatState>((set, get) => ({
        // Initial state
        threads: [],
        messages: [],
        currentThreadId: null,
        currentThread: null,
        isLoading: false,
        error: null,
        isLoadingMessages: false,
        isLoadingThreads: false,

        // Basic setters - đơn giản, dùng object spread
        setLoading: (loading) => set({ isLoading: loading }),
        setError: (error) => set({ error }),
        setLoadingThreads: (loading) => set({ isLoadingThreads: loading }),
        setLoadingMessages: (loading) => set({ isLoadingMessages: loading }),

        // Thread actions
        createThread: async (title?: string) => {
          const threadTitle = title || `Chat ${new Date().toLocaleString()}`;
          set({ isLoading: true });

          try {
            const data = await createThreadAsync();
            const newThread: Thread = {
              id: data.thread_id,
              title: threadTitle,
              createdAt: new Date(),
              updatedAt: new Date()
            };

            // Phức tạp - dùng Immer draft
            set((draft) => {
              draft.threads.unshift(newThread);
              draft.currentThreadId = data.thread_id;
              draft.currentThread = newThread;
              draft.isLoading = false;
            });

            return data.thread_id;
          } catch (error) {
            console.error('Create thread error:', error);
            const errorMessage =
              error instanceof Error
                ? error.message
                : 'Failed to create thread';
            // Đơn giản - dùng object spread
            set({ error: errorMessage, isLoading: false });
            return '';
          }
        },

        loadThreads: async () => {
          set({ isLoadingThreads: true });

          try {
            const threads = await fetchThreads();
            // Đơn giản - dùng object spread
            set({ threads, isLoadingThreads: false });
          } catch (error) {
            console.error('Load threads error:', error);
            const errorMessage =
              error instanceof Error ? error.message : 'Failed to load threads';
            set({ error: errorMessage, isLoadingThreads: false });
          }
        },

        switchThread: async (threadId: string) => {
          const currentThreadId = get().currentThreadId;
          if (currentThreadId === threadId) {
            console.log("no no no");
            return; // Không cần load lại nếu đã là thread hiện tại
          }
          console.log("select fuck");
          const threads = get().threads;
          const thread = threads.find((t) => t.id === threadId);
          if (!thread) {
            console.error(`Thread with ID ${threadId} not found`);
            return;
          }
          console.log("select fuck");

          set({ currentThreadId: threadId, currentThread: thread });

          await get().loadMessages(threadId);
        },

        deleteThread: (threadId: string) => {
          // Phức tạp - dùng Immer draft
          set((draft) => {
            draft.threads = draft.threads.filter(
              (thread) => thread.id !== threadId
            );
            draft.messages = draft.messages.filter(
              (message) => message.threadId !== threadId
            );

            if (draft.currentThreadId === threadId) {
              draft.currentThreadId =
                draft.threads.length > 0 ? draft.threads[0].id : null;
              draft.currentThread =
                draft.threads.length > 0 ? draft.threads[0] : null;
            }
          });
        },

        updateThreadTitle: (threadId: string, title: string) => {
          // Phức tạp - update nested object
          set((draft) => {
            const thread = draft.threads.find((t) => t.id === threadId);
            if (thread) {
              thread.title = title;
              thread.updatedAt = new Date();
            }
          });
        },

        // Message actions
        loadMessages: async (threadId: string) => {
          set({ isLoadingMessages: true });

          try {
            const messages = await fetchMessages(threadId);
            set({ messages, isLoadingMessages: false });
          } catch (error) {
            console.error('Load messages error:', error);
            const errorMessage =
              error instanceof Error
                ? error.message
                : 'Failed to load messages';
            set({ error: errorMessage, isLoadingMessages: false });
          }
        },

        sendMessage: async (
          content: string,
          files: File[] = [],
          threadId?: string
        ) => {
          const state = get();
          const targetThreadId = threadId || state.currentThreadId;
          console.log(files);
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

            get().addMessage(userMessage);

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

            get().addMessage(assistantMessage);

            // Get updated messages for streaming
            const currentState = get();
            const threadMessages = currentState.messages
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
                get().updateMessage(assistantMessageId, streamingContent, true);
              },
              () => {},
              () => {},
              () => {},
              true
            );

            // Save final assistant message
            const assistantMessageRequest: CreateMessageRequest = {
              message_id: assistantMessageId,
              thread_id: targetThreadId,
              content: finalContent.content,
              role: 'assistant'
            };

            await createMessage(targetThreadId, assistantMessageRequest);
            get().updateMessage(
              assistantMessageId,
              finalContent.content,
              false
            );
          } catch (error) {
            console.error('Send message error:', error);
            const errorMessage =
              error instanceof Error ? error.message : 'Unknown error occurred';
            set({ error: errorMessage, isLoading: false });
          } finally {
            set({ isLoading: false });
          }
        },

        addMessage: (message: Message) => {
          // Phức tạp - thêm message và update thread timestamp
          set((draft) => {
            draft.messages.push(message);

            const thread = draft.threads.find((t) => t.id === message.threadId);
            if (thread) {
              thread.updatedAt = new Date();
            }
          });
        },

        updateMessage: (
          messageId: string,
          content: string,
          isStreaming?: boolean
        ) => {
          // Phức tạp - tìm và update message
          set((draft) => {
            const message = draft.messages.find(
              (m) => m.messageId === messageId
            );
            if (message) {
              message.content = content;
              message.isStreaming = isStreaming;
            }
          });
        },

        clearMessages: (threadId: string) => {
          // Phức tạp - filter messages và update thread
          set((draft) => {
            draft.messages = draft.messages.filter(
              (message) => message.threadId !== threadId
            );

            const thread = draft.threads.find((t) => t.id === threadId);
            if (thread) {
              thread.updatedAt = new Date();
            }
          });
        },
      }))
    ),
    { name: 'ChatStore' }
  )
);

import { Message, Thread } from '@/schemas/chat-schema';

export type MessageRequestBase = {
  message_id?: string;
  thread_id?: string;
  content: string;
};

export type CreateMessageRequest = {
  role: 'user' | 'assistant';
} & MessageRequestBase;

export type CreateMessageResponse = {
  message_id: string;
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


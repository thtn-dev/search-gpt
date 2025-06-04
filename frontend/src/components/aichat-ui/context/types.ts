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
      payload: { messageId: string; content: string; isStreaming?: boolean };
    }
  | { type: 'SET_MESSAGES'; payload: Message[] }
  | { type: 'DELETE_THREAD'; payload: string }
  | {
      type: 'UPDATE_THREAD_TITLE';
      payload: { threadId: string; title: string };
    }
  | { type: 'CLEAR_MESSAGES'; payload: string };

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

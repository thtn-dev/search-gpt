import { Thread } from '@/schemas/chat-schema';
import { ChatState, ChatAction } from './types';

export const initialState: ChatState = {
  threads: [],
  messages: [],
  currentThreadId: null,
  isLoading: false,
  error: null,
  isLoadingMessages: false
};

export function chatReducer(state: ChatState, action: ChatAction): ChatState {
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
          message.messageId === action.payload.messageId
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

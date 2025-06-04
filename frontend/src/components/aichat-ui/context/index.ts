// Main exports
export { ChatProvider } from './thread-context';
export { useChatContext, useCurrentThread, useCurrentMessages } from './hooks';

// Type exports
export type {
  ChatState,
  ChatAction,
  ChatContextType,
  CreateMessageRequest,
  CreateMessageResponse
} from './types';

// Service exports (if needed externally)
export {
  createThreadAsync,
  fetchThreads,
  fetchMessages,
  createMessage,
  streamChatResponse
} from './api-service';

export { processStreamingResponse } from './streaming-service';

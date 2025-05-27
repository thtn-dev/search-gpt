// Main exports
export { ChatProvider } from './thread-context';
export { useChatContext, useCurrentThread, useCurrentMessages } from './hooks';

// Type exports
export type { 
  ChatState, 
  ChatAction, 
  ChatContextType,
  ApiContentItem,
  ApiContent,
  CreateMessageRequest,
  CreateMessageResponse,
  ApiMessage
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

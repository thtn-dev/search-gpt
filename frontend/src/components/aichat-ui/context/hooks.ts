import { useContext } from 'react';
import { Thread, Message } from '@/schemas/chat-schema';
import { ChatContext } from './thread-context';
import { ChatContextType } from './types';

export function useChatContext(): ChatContextType {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChatContext must be used within a ChatProvider');
  }
  return context;
}

export function useCurrentThread(): Thread | null {
  const { getCurrentThread } = useChatContext();
  return getCurrentThread();
}

export function useCurrentMessages(): Message[] {
  const { getCurrentMessages } = useChatContext();
  return getCurrentMessages();
}

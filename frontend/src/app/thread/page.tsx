import React from 'react';
import { ChatProvider } from '@/components/aichat-ui/context/thread-context';
import { ThreadRoot } from '@/components/aichat-ui/thread-root';

export default function ThreadPge() {
  return (
    <ChatProvider>
      <ThreadRoot />
    </ChatProvider>
  );
}

import React from 'react';
import { ChatProvider } from '@/components/aichat-ui/context';
import { ThreadRoot } from '@/components/aichat-ui/thread-root';

export default function ThreadByIdPage() {
  return (
    <ChatProvider>
      <ThreadRoot />
    </ChatProvider>
  );
}

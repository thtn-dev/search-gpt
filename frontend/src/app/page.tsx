'use client';

import { Thread } from '@/components/assistant-ui/thread';
import { ThreadList } from '@/components/assistant-ui/thread-list';
import { AssistantRuntimeProvider } from '@assistant-ui/react';
import { useChatRuntime } from '@assistant-ui/react-ai-sdk';

export default function Home() {
  // const runtime = useLocalRuntime(MyModelAdapter);
  const runtime = useChatRuntime({
    api: '/api/chat'
  });
  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <main className='h-dvh grid grid-cols-[200px_1fr] gap-x-2 px-4 py-4'>
        <ThreadList />
        <Thread />
      </main>
    </AssistantRuntimeProvider>
  );
}

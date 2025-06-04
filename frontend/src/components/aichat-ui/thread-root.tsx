'use client';

import * as React from 'react';
import { useParams } from 'next/navigation';
import { ScrollArea } from '../ui/scroll-area';
import { SidebarInset, SidebarProvider } from '../ui/sidebar';
import Chat from './chat';
import { useChatContext, useCurrentThread } from './context';
import EmptyChat from './empty-chat';
import { MessageInput } from './message-input';
import { AppSidebar } from './sidebar/app-sidebar';
import ThreadHeader from './thread-header';

export function ThreadRoot() {
  const params = useParams();
  const threadId = (params.id as string) || null;
  const { sendMessage, switchThread } = useChatContext();
  const thread = useCurrentThread();

  React.useEffect(() => {
    if (threadId) {
      switchThread(threadId);
    }
  }, [threadId, switchThread]);

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className='relative flex flex-col h-screen'>
        <ThreadHeader />
        {/* Main content area - flex-1 để chiếm hết không gian còn lại */}
        <div className='flex-1 overflow-hidden'>
          {thread ? (
            <ScrollArea className='h-full'>
              <section className='w-full max-w-4xl mx-auto p-5'>
                <Chat />
              </section>
              {/* MessageInput - cố định ở dưới cùng */}
              <div className='sticky bottom-0 pb-2 bg-background'>
                <div className='w-full max-w-4xl mx-auto px-5'>
                  <MessageInput
                    className='w-full'
                    onSendMessage={sendMessage}
                  />
                </div>
              </div>
            </ScrollArea>
          ) : (
            <EmptyChat />
          )}
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}

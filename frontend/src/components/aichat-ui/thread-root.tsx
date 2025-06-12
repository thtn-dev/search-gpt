'use client';

import * as React from 'react';
import { useParams } from 'next/navigation';
import { ScrollArea } from '../ui/scroll-area';
import { SidebarInset, SidebarProvider } from '../ui/sidebar';
import Chat from './chat';
import EmptyChat from './empty-chat';
import { MessageInput } from './message-input';
import { AppSidebar } from './sidebar/app-sidebar';
import { useChatStore } from './store/chat-store';
import ThreadHeader from './thread-header';

export function ThreadRoot() {
  const params = useParams();
  const threadId = (params.id as string) || null;
  const sendMessage = useChatStore((state) => state.sendMessage);
  const loadMessages = useChatStore((state) => state.loadMessages);
  const messages = useChatStore((state) => state.messages);
  const loadThreads = useChatStore((state) => state.loadThreads);
  const loadThreadById = useChatStore((state) => state.loadThreadById);

  React.useEffect(() => {
    loadThreads();
  }, [loadThreads]);

  React.useEffect(() => {
    if (threadId) {
      console.log('switching thread to:', threadId);
      Promise.allSettled([loadThreadById(threadId), loadMessages(threadId)]);
    }
  }, [threadId, loadMessages, loadThreadById]);

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className='relative flex flex-col h-screen'>
        <ThreadHeader />
        {/* Main content area - flex-1 để chiếm hết không gian còn lại */}
        <div className='flex-1 overflow-hidden'>
          {messages.length > 0 ? (
            <div className='overflow-auto h-full flex flex-col'>
              <ScrollArea className='flex-1'>
                <section className=' w-full max-w-4xl mx-auto p-5 '>
                  <Chat />
                </section>
              </ScrollArea>
              {/* MessageInput - cố định ở dưới cùng */}
              <div className='sticky bottom-0 pb-4 bg-background'>
                <div className='w-full max-w-4xl mx-auto px-5'>
                  <MessageInput
                    className='w-full'
                    onSendMessage={sendMessage}
                  />
                </div>
              </div>
            </div>
          ) : (
            <EmptyChat />
          )}
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}

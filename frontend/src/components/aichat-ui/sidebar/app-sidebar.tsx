'use client';

import * as React from 'react';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail
} from '@/components/ui/sidebar';
import { useChatStore } from '../store/chat-store';

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const threads = useChatStore(state => state.threads);
  const switchThread= useChatStore(state => state.switchThread);
  const changeUrlOnly = React.useCallback((tId: string) => {
    window.history.pushState({ threadId: tId }, '', `/threads/${tId}`);
  }, []);
  const handleClickSwitchThread = (threadId: string) => {
    changeUrlOnly(threadId);
    switchThread(threadId);
  };

  return (
    <Sidebar collapsible='icon' {...props}>
      <SidebarHeader>
        <div className='flex items-center justify-between'>
          <h1 className='text-lg font-semibold'>AI Chat</h1>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <div className='flex flex-col gap-2'>
          {threads.map((thread) => (
            <div key={thread.id} className='p-2 hover:bg-accent rounded-md'>
              <button
                onClick={() => handleClickSwitchThread(thread.id)}
                className='block text-sm'
              >
                {thread.title || 'Untitled Thread'}
              </button>
            </div>
          ))}
        </div>
      </SidebarContent>
      <SidebarFooter></SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}

'use client';

import * as React from 'react';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
  useSidebar
} from '@/components/ui/sidebar';
import { cn } from '@/lib/utils';
import { DiamondPlusIcon } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useChatStore } from '../store/chat-store';

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const router = useRouter();
  const { open } = useSidebar();
  const threads = useChatStore((state) => state.threads);
  const isLoadingThreads = useChatStore((state) => state.isLoadingThreads);
  const currentThreadId = useChatStore((state) => state.currentThreadId);
  const emptyThread = useChatStore((state) => state.emptyThread);

  const switchThread = useChatStore((state) => state.switchThread);

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
        <div className='flex items-center justify-center '>
          <h1 className='text-lg font-semibold italic text-pretty text-primary'>
            AI
          </h1>
        </div>
      </SidebarHeader>
      <SidebarContent className='pt-4 overflow-hidden'>
        <div className='flex items-center justify-center mb-2'>
          <Button
            size={open ? 'default' : 'icon'}
            variant={'outline'}
            className='rounded-full'
            onClick={() => {
              emptyThread();
              router.push('/');
            }}
          >
            <DiamondPlusIcon className='size-8' />
            {open ? 'New Thread' : <span className='sr-only'>New Thread</span>}
          </Button>
        </div>
        {isLoadingThreads ? (
          <div className='flex items-center justify-center h-full'>
            <span>Loading threads...</span>
          </div>
        ) : (
          <ScrollArea className='h-full w-full'>
            <ul
              className={cn(
                'flex flex-col gap-1 w-full',
                open ? 'h-full' : 'hidden',
                'overflow-x-hidden',
                'p-2'
              )}
            >
              {threads.map((thread) => (
                <li key={thread.id}>
                  <Button
                    variant={'ghost'}
                    className={cn(
                      'max-w-full w-full text-left justify-start px-2 rounded ',
                      currentThreadId === thread.id
                        ? 'bg-accent text-accent-foreground'
                        : 'hover:bg-accent hover:text-accent-foreground'
                    )}
                    onClick={() => handleClickSwitchThread(thread.id)}
                  >
                    <p>{thread.title || 'Untitled Thread'}</p>
                  </Button>
                </li>
              ))}
            </ul>
          </ScrollArea>
        )}
        <div className={cn('flex items-center mx-2', 'justify-center', 'mt-2')}>
          <Avatar className='size-8'>
            <AvatarFallback className='bg-primary text-primary-foreground'>
              U
            </AvatarFallback>
          </Avatar>
        </div>
      </SidebarContent>
      <SidebarFooter></SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}

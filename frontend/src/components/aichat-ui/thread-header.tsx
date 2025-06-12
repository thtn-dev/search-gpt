'use client';

import React from 'react';
import ThemeSwitcher from '../theme-switcher';
import { SidebarTrigger } from '../ui/sidebar';
import { useChatStore } from './store/chat-store';

export default function ThreadHeader() {
  const thread = useChatStore((state) => state.currentThread);
  return (
    <header className='flex h-12 sticky shrink-0 items-center gap-2 transition-[width,height] ease-linear shadow-sm'>
      <div className='flex items-center justify-between gap-2 px-4 w-full'>
        <SidebarTrigger className='-ml-1' />
        <div className='flex-1 flex items-center justify-center max-w-4xl gap-2'>
          {thread ? (
            <span className='text-sm font-semibold text-muted-foreground truncate'>
              {thread.title || 'New Thread'}
            </span>
          ) : (
            <span className='text-sm font-semibold text-muted-foreground'></span>
          )}
        </div>
        <ThemeSwitcher />
      </div>
    </header>
  );
}

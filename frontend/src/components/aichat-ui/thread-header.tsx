import React from 'react';
import ThemeSwitcher from '../theme-switcher';
import { Separator } from '../ui/separator';
import { SidebarTrigger } from '../ui/sidebar';
import { useCurrentThread } from './context/thread-context';

export default function ThreadHeader() {
  const thread = useCurrentThread();
  return (
    <header className='flex h-12 sticky shrink-0 items-center gap-2 transition-[width,height] ease-linear shadow-sm'>
      <div className='flex items-center justify-between gap-2 px-4 w-full'>
        <SidebarTrigger className='-ml-1' />
        <div className='flex-1 flex items-center gap-2'>
          <Separator orientation='vertical' className='mr-2 h-4' />
          {thread ? (
            <span className='text-sm font-semibold text-muted-foreground'>
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

'use client';

import React, { Fragment } from 'react';
import { AuroraText } from '../magicui/aurora-text';
import { useChatContext } from './context';
import { MessageInput } from './message-input';

export default function EmptyChat() {
  const { sendMessage, createThread, loadThreads } = useChatContext();

  React.useEffect(() => {
    loadThreads();
  }, [loadThreads]);

  const changeUrlOnly = React.useCallback((tId: string) => {
    window.history.pushState({ threadId: tId }, '', `/threads/${tId}`);
  }, []);

  const handleSendFirstMessage = React.useCallback(
    async (message: string, files: File[]) => {
      // Create a new thread if it doesn't exist
      const tId = await createThread('New Thread');
      if (!tId) {
        console.error('Failed to create thread');
        return;
      }

      // change the route to the new thread with out refreshing the page
      changeUrlOnly(tId);
      sendMessage(message, files, tId);
    },
    [changeUrlOnly, createThread, sendMessage]
  );

  return (
    <Fragment>
      <div className='flex flex-col items-center justify-center h-full p-4'>
        <h2 className='text-4xl font-bold mb-8'>
          Start a New{' '}
          <AuroraText colors={['#C96442', '#E07A4F', '#C96442', '#A74E33']}>
            Conversation...
          </AuroraText>
        </h2>
        <MessageInput
          className='w-full max-w-3xl'
          onSendMessage={handleSendFirstMessage}
        />
      </div>
    </Fragment>
  );
}

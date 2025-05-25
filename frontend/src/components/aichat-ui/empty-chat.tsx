import React, { Fragment } from 'react';
import { AuroraText } from '../magicui/aurora-text';
import { useChatContext } from './context/thread-context';
import { MessageInput } from './message-input';

export default function EmptyChat() {
  const { sendMessage, createThread } = useChatContext();

  const handleSendFirstMessage = (message: string, files: File[]) => {
    // Create a new thread if it doesn't exist
    const tId = createThread('New Thread');
    // Send an initial message
    sendMessage(message, files, tId);
  };

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

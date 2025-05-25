'use client';

import React, { Fragment } from 'react';
import { Message } from '@/schemas/chat-schema';
import { Avatar, AvatarFallback } from '../ui/avatar';
import { useChatContext, useCurrentMessages } from './context/thread-context';
import MessageBox from './message-box';

const UserMessageBox = ({
  message,
  messageIndex
}: {
  message?: Message;
  messageIndex?: number;
}) => {
  return (
    <Fragment key={messageIndex}>
      <div className='relative flex gap-2 items-start mb-4 animate-fadeIn rounded-lg bg-sidebar px-4 py-3 leading-normal break-words'>
        <Avatar className='size-6'>
          <AvatarFallback className='bg-primary text-primary-foreground'>
            U
          </AvatarFallback>
        </Avatar>
        <p>{message?.content}</p>
      </div>
    </Fragment>
  );
};

export default function Chat() {
  const { state } = useChatContext();
  const currrentMessages = useCurrentMessages();
  return (
    <Fragment>
      {currrentMessages.map((message, index) => (
        <Fragment key={message.id}>
          {message.role === 'user' ? (
            <UserMessageBox message={message} messageIndex={index} />
          ) : (
            <MessageBox
              messsage={message}
              messageIndex={index}
              loading={state.isLoading && index === currrentMessages.length - 1}
              isLastMessage={index === currrentMessages.length - 1}
            />
          )}
        </Fragment>
      ))}
    </Fragment>
  );
}

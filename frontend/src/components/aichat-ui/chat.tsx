'use client';

import React, { Fragment } from 'react';
import { Message } from '@/schemas/chat-schema';
import { Avatar, AvatarFallback } from '../ui/avatar';
import MessageBox from './message-box';
import { useChatStore } from './store/chat-store';

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
  const isLoading = useChatStore((state) => state.isLoading);
  const currrentMessages = useChatStore((state) => state.messages);
  console.log(currrentMessages);
  return (
    <Fragment>
      {currrentMessages.map((message, index) => (
        <Fragment key={message.messageId}>
          {message.role === 'user' ? (
            <UserMessageBox message={message} messageIndex={index} />
          ) : (
            <MessageBox
              messsage={message}
              messageIndex={index}
              loading={isLoading && index === currrentMessages.length - 1}
              isLastMessage={index === currrentMessages.length - 1}
            />
          )}
        </Fragment>
      ))}
    </Fragment>
  );
}

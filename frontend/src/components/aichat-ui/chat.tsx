'use client';

import React, { Fragment } from 'react';
import { Message } from '@/schemas/chat-schema';
import { LoaderPinwheel } from 'lucide-react';
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
          <AvatarFallback className='bg-accent text-primary font-semibold border'>
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
  const isLoadingMessages = useChatStore((state) => state.isLoadingMessages);
  const currrentMessages = useChatStore((state) => state.messages);
  console.log(isLoadingMessages);
  return (
    <Fragment>
      {isLoadingMessages ? (
        <div className='flex items-center justify-center  h-[70dvh] '>
          <LoaderPinwheel className='ease-in-out animate-spin opacity-80 size-40 text-primary' />
        </div>
      ) : (
        currrentMessages.map((message, index) => (
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
        ))
      )}
    </Fragment>
  );
}

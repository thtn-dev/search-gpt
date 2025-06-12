'use client';

import React, { Fragment } from 'react';
import { cn } from '@/lib/utils';
import { Message } from '@/schemas/chat-schema';
import Markdown, { MarkdownToJSX } from 'markdown-to-jsx';
import { darcula as theme } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import CodeBlock from './code-block';

const InlineCode = ({ children }: { children: React.ReactNode }) => (
  <code className='inline-code'>{children}</code>
);

const markdownOptions: MarkdownToJSX.Options = {
  overrides: {
    code: {
      component: InlineCode
    },
    pre: {
      component: ({
        children,
        ...props
      }: React.ComponentPropsWithoutRef<'pre'>) => {
        if (
          children &&
          React.isValidElement(children) &&
          typeof children === 'object'
        ) {
          const codeElement = children as React.ReactElement<{
            className?: string;
            children: React.ReactNode;
          }>;
          return (
            <CodeBlock theme={theme} className={codeElement.props.className}>
              {codeElement.props.children}
            </CodeBlock>
          );
        }
        return <pre {...props}>{children}</pre>;
      }
    }
  }
};

interface MessageBoxProps {
  messsage?: Message;
  messageIndex?: number;
  loading?: boolean;
  isLastMessage?: boolean;
}

export default function MessageBox({
  messsage,
  loading,
  isLastMessage,
  messageIndex
}: MessageBoxProps) {
  const [parsedMessage, setParsedMessage] = React.useState<string | undefined>(
    messsage?.content
  );

  React.useEffect(() => {
    if (messsage?.content) {
      setParsedMessage(messsage.content);
    }
  }, [messsage?.content]);

  return (
    <Fragment key={messageIndex}>
      <div className='relative mb-4 animate-fadeIn rounded-lg bg-card px-4 py-3 leading-normal'>
        {parsedMessage && (
          <>
            <Markdown
              className={cn(
                'prose prose-h1:mb-3 prose-h2:mb-2 prose-h2:mt-4 prose-h2:font-[800] prose-h3:mt-4 prose-h3:mb-1.5 prose-h3:font-[600] dark:prose-invert prose-p:leading-relaxed prose-pre:p-0 font-[400]',
                'max-w-none break-words'
              )}
              options={markdownOptions}
            >
              {parsedMessage}
            </Markdown>
            {isLastMessage && loading && (
              <span className='typing-indicator'>
                <span className='dot'></span>
                <span className='dot'></span>
                <span className='dot'></span>
              </span>
            )}
          </>
        )}
      </div>
    </Fragment>
  );
}

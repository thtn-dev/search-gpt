'use client';

import React, { Fragment } from 'react';
import { cn } from '@/lib/utils';
import { Message } from '@/schemas/chat-schema';
import Markdown, { MarkdownToJSX } from 'markdown-to-jsx';
import { darcula as theme } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import CodeBlock from './code-block';

interface Props extends React.PropsWithChildren {
  message: Message | null;
  isTyping?: boolean;
}


// Custom inline code component
const InlineCode = ({ children }: { children: React.ReactNode }) => (
  <code className='inline-code'>{children}</code>
);

export default function Chat({ message, isTyping = false }: Props) {
  const [parsedMessage, setParsedMessage] = React.useState<string | undefined>(
    message?.content
  );

  React.useEffect(() => {
    if (message) {
      setParsedMessage(message.content);
    }
  }, [message]);

  // Configure markdown options with custom code renderers
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

  return (
    <Fragment>
      <div className='chat-message'>
        {parsedMessage && (
          <>
            <Markdown
              className={cn(
                'prose prose-h1:mb-3 prose-h2:mb-2 prose-h2:mt-4 prose-h2:font-[800] prose-h3:mt-4 prose-h3:mb-1.5 prose-h3:font-[600] dark:prose-invert prose-p:leading-relaxed prose-pre:p-0 font-[400]',
                'max-w-none break-words text-black dark:text-white'
              )}
              options={markdownOptions}
            >
              {parsedMessage}
            </Markdown>
            {isTyping && (
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

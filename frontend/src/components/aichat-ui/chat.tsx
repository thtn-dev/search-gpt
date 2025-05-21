"use client";
import { Message } from "@/schemas/chat-schema";
import React from "react";
import Markdown, { MarkdownToJSX } from "markdown-to-jsx";
import SyntaxHighlighter from 'react-syntax-highlighter';
import { darcula as theme } from 'react-syntax-highlighter/dist/esm/styles/hljs';

interface Props extends React.PropsWithChildren {
  message: Message | null;
  isTyping?: boolean;
}

// Custom Code component for syntax highlighting
const CodeBlock = ({ className, children }: { className?: string; children: React.ReactNode }) => {
  // Extract language from className (format: "language-xxx")
  const match = /lang-(\w+)/.exec(className || '');
  const language = match ? match[1] : 'text';
  
  return (
    <div className="code-block-wrapper">
      <div className="code-block-header">
        {language && <span className="code-language-tag">{language}</span>}
      </div>
      <SyntaxHighlighter 
        language={language} 
        style={theme}
        showLineNumbers
        customStyle={{ margin: 0, borderRadius: '0 0 4px 4px' }}
      >
        {String(children).replace(/\n$/, '')}
      </SyntaxHighlighter>
    </div>
  );
};

// Custom inline code component
const InlineCode = ({ children }: { children: React.ReactNode }) => (
  <code className="inline-code">{children}</code>
);

export default function Chat({ message, isTyping = false }: Props) {
  const [parsedMessage, setParsedMessage] = React.useState<string | undefined>(message?.content);

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
        component: ({ children, ...props }: React.ComponentPropsWithoutRef<"pre">) => {
          if (children && React.isValidElement(children) && typeof children === 'object') {
            const codeElement = children as React.ReactElement<{ className?: string; children: React.ReactNode }>;
            return <CodeBlock className={codeElement.props.className}>{codeElement.props.children}</CodeBlock>;
          }
          return <pre {...props}>{children}</pre>;
        }
      }
    }
  };

  return (
    <div className="chat-message">
      {parsedMessage && (
        <>
          <Markdown options={markdownOptions}>{parsedMessage}</Markdown>
          {isTyping && (
            <span className="typing-indicator">
              <span className="dot"></span>
              <span className="dot"></span>
              <span className="dot"></span>
            </span>
          )}
        </>
      )}
    </div>
  );
}
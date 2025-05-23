"use client";
import * as React from "react";
import Chat from "./chat";
import { Message } from "@/schemas/chat-schema";
import { MessageInput } from "./message-input";
import { ScrollArea } from "../ui/scroll-area";
import { SidebarInset, SidebarProvider } from "../ui/sidebar";
import { AppSidebar } from "./sidebar/app-sidebar";
import ThreadHeader from "./thread-header";

interface Props {
  threadId?: string;
}

// Example message with code blocks for demonstration
const exampleMessage = `
# Sample Code Snippet
This is a sample code snippet in a markdown format. You can use \`code\` inline or create code blocks using triple backticks.
Here's a simple React component:

\`\`\`jsx
import React from 'react';

function HelloWorld() {
  return (
    <div className="greeting">
      <h1>React</h1>
      <p>Welcome to my React application!</p>
    </div>
  );
}
\`\`\`

And here's some CSS to style it:

\`\`\`css
.greeting {
  padding: 20px;
  border-radius: 8px;
  background-color: #f5f5f5;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  text-align: center;
}

h1 {
  color: #333;
  font-size: 24px;
}

p {
  color: #666;
  font-size: 16px;
}
\`\`\`

You can also use inline code like \`const x = 42;\` within your text.
`;

export function ThreadRoot({ threadId }: Props) {
  const [messages] = React.useState<Message[]>([]);
  const [currentMessage, setCurrentMessage] = React.useState<Message | null>(
    null
  );
  const [isTyping, setIsTyping] = React.useState<boolean>(false);

  // Stream the message character by character for better code block handling
  React.useEffect(() => {
    const streamMessage = async () => {
      setIsTyping(true);

      // Create the initial message
      setCurrentMessage({
        role: "assistant",
        content: "",
        createdAt: new Date(),
        threadId: threadId || "default-thread-id",
      });

      const messageToStream = exampleMessage; // Use the example message with code blocks
      let accumulatedContent = "";

      // Stream each character with a delay
      // This approach preserves formatting better than word-by-word for code blocks
      for (let i = 0; i < messageToStream.length; i++) {
        accumulatedContent += messageToStream[i];
        if (i % 10 === 0) {
          setCurrentMessage((prev) => {
            if (prev) {
              return {
                ...prev,
                content: accumulatedContent,
              };
            }
            return null;
          });

          // Slower delay for better readability
          // Adjust this value as needed - lower means faster typing
          await new Promise((resolve) => setTimeout(resolve, 40));
        }
      }

      // Finalize the message
      setIsTyping(false);

      // Add the complete message to the messages list when done streaming
      // setMessages((prev) => [
      //   ...prev,
      //   {
      //     role: "assistant",
      //     content: accumulatedContent,
      //     createdAt: new Date(),
      //     threadId: threadId || "default-thread-id",
      //   },
      // ]);
    };

    streamMessage();
  }, [threadId]);

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="relative flex flex-col h-screen">
        <ThreadHeader />
        {/* Main content area - flex-1 để chiếm hết không gian còn lại */}
        <div className="flex-1 overflow-hidden">
          <ScrollArea className="h-full">
            <section className="w-full max-w-4xl mx-auto p-5">
              {/* Show previous messages */}
              {messages.map((msg, index) => (
                <Chat key={`msg-${index}`} message={msg} />
              ))}
              {/* Show the currently streaming message */}
              {currentMessage && (
                <Chat message={currentMessage} isTyping={isTyping} />
              )}
            </section>
            {/* MessageInput - cố định ở dưới cùng */}
            <div className="sticky bottom-0 pb-2 bg-background">
              <div className="w-full max-w-4xl mx-auto">
                <MessageInput className="w-full" onSendMessage={() => {}} />
              </div>
            </div>
          </ScrollArea>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}

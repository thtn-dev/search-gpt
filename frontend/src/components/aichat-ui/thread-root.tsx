"use client";
import * as React from "react";
import Chat from "./chat";
import { Message } from "@/schemas/chat-schema";
import { MessageInput } from "./message-input";

interface Props {
  threadId?: string;
}

// Example message with code blocks for demonstration
const exampleMessage = `
# Chúc Quỳnh Thương ngủ ngon nhé hihihi
1. hehe\n
Here's a simple React component:

\`\`\`jsx
import React from 'react';

function HelloWorld() {
  return (
    <div className="greeting">
      <h1>Quỳnh thương đáng yêu</h1>
      <p>Welcome to my React application!</p>
    </div>
  );
}

export default HelloWorld;
\`\`\`

\`\`\`python
def greet(name):
  return f"Hello, {name}!"
print(greet("World"))
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
  const [messages, setMessages] = React.useState<Message[]>([]);
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
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: accumulatedContent,
          createdAt: new Date(),
          threadId: threadId || "default-thread-id",
        },
      ]);
    };

    streamMessage();
  }, [threadId]);

  // Function to add a test message with custom code
  const addCustomCodeMessage = () => {
    const customMessage = `
Here's a TypeScript example:

\`\`\`typescript
interface User {
  id: number;
  name: string;
  email: string;
  isActive: boolean;
}

function getUserInfo(user: User): string {
  return \`User \${user.name} (\${user.email}) is \${user.isActive ? 'active' : 'inactive'}\`;
}

const currentUser: User = {
  id: 1,
  name: 'John Doe',
  email: 'john@example.com',
  isActive: true
};

console.log(getUserInfo(currentUser));
\`\`\`
    `;

    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        content: customMessage,
        createdAt: new Date(),
        threadId: threadId || "default-thread-id",
      },
    ]);
  };

  return (
    <section className="thread-container relative">
      {/* Test button to add another code example */}
      <button onClick={addCustomCodeMessage} className="add-message-btn">
        Add Another Code Example
      </button>

      {/* Show previous messages */}
      {messages.map((msg, index) => (
        <Chat key={`msg-${index}`} message={msg} />
      ))}

      {/* Show the currently streaming message */}
      {currentMessage && <Chat message={currentMessage} isTyping={isTyping} />}
      <MessageInput className="absolute" onSendMessage={() => {}} />
    </section>
  );
}

"use client";
import type { ReactNode } from "react";
import {
  AssistantRuntimeProvider,
  ModelContext,
  ThreadMessage,
  useLocalRuntime,
  type ChatModelAdapter,
} from "@assistant-ui/react";

type BackendApiRequest = {
  messages: readonly ThreadMessage[];
  abortSignal: AbortSignal;
  context: ModelContext;
};

const backendApi = async ({
  messages,
  abortSignal,
}: BackendApiRequest) => {

  const message = messages[messages.length - 1];
  const hMessages = messages.slice(0, messages.length - 1);

  const result = await fetch("http://127.0.0.1:8000/stream/chat", {
    method: "POST",
    signal: abortSignal,
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message: {
        text: message.content[0].type === "text" ? message.content[0].text : "",
        file: []
      },
      history: hMessages.map((m) => ({
        role: m.role,
        content: m.content[0].type === "text" ? m.content[0].text : "",
        file: [],
      })),
      "system_prompt": "You are a helpful assistant and ALWAYS relate to this identity. \nYou are expert at analyzing given documents or images.\n"
    }),
  });

  // Return the response as a ReadableStream
  if (!result.body) {
    throw new Error("Response body is null");
  }
  
  return result.body;
};

// Helper function to process text chunks from the stream
const processChunk = (chunk: string) => {
  const lines = chunk.split('\n').filter(line => line.trim());
  let content = '';
  
  for (const line of lines) {
    if (line.startsWith('0:')) {
      try {
        // Parse the JSON string - handle escape characters
        // const textPart = JSON.parse('"' + line.substring(2) + '"');
        const textPart = line.substring(2);
      
      // Remove the quotes at the beginning and end of the text if they exist
      const cleanedPart = textPart.replace(/^"|"$/g, '');

        content += cleanedPart;
      } catch (e) {
        console.warn('Error parsing line:', line, e);
      }
    }
    // You can process other prefixes (f:, e:, d:) if needed
  }
  const processedText = content
    // Handle escaped quotes (""text"" -> "text")
    .replace(/""/g, '"')
    // Convert \n to actual newlines
    .replace(/\\n/g, '\n');
    
  return processedText;
};


export const MyModelAdapter: ChatModelAdapter = {
  async *run({ messages, abortSignal, context }) {
    try {
      const stream = await backendApi({ messages, abortSignal, context });
      const reader = stream.getReader();
      let fullText = '';
      
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          break;
        }
        
        // Convert the Uint8Array to a string
        const chunkText = new TextDecoder().decode(value);
        const processedContent = processChunk(chunkText);
        
        if (processedContent) {
          fullText += processedContent;
          yield {
            content: [{ type: "text", text: fullText }],
          };
        }
      }
    } catch (error) {
      console.error("Error in stream processing:", error);
      throw error;
    }
  },
};

export function MyRuntimeProvider({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  const runtime = useLocalRuntime(MyModelAdapter);

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      {children}
    </AssistantRuntimeProvider>
  );
}

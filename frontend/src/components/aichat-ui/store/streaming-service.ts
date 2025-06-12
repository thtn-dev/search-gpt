'use client';
// Optional: Export type definitions for better TypeScript support
export interface StreamData {
  metadata?: MessageStreamMetadata;
  chk?: string;
  eofs?: boolean;
}

export interface MessageStreamMetadata {
  thread_id: string;
  ai_message_id: string;
}

// Alternative version with more detailed logging
export const processStreamingResponse = async (
  reader: ReadableStreamDefaultReader<Uint8Array>,
  onUpdate: (content: string) => void,
  onBeforeUpdate?: (metadata: MessageStreamMetadata) => void,
  onComplete?: () => void,
  onError?: (error: Error) => void,
  enableLogging = false
): Promise<{ content: string; messageId?: string }> => {
  const decoder = new TextDecoder();
  let streamingContent = '';
  let aiMessageId = '';

  const log = (message: string, data?: unknown) => {
    if (enableLogging) {
      console.log(`[StreamProcessor] ${message}`, data || '');
    }
  };

  try {
    log('Starting stream processing');

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        log('Stream ended');
        break;
      }

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');

      for (const line of lines) {
        const trimmedLine = line.trim();
        if (trimmedLine === '') continue;

        if (trimmedLine.startsWith('data: ')) {
          try {
            const jsonStr = trimmedLine.substring(6);
            const data: StreamData = JSON.parse(jsonStr);

            if (data.metadata) {
              const { metadata } = data;
              aiMessageId = metadata.ai_message_id;
              onBeforeUpdate?.(metadata);
              log('Received message ID:', aiMessageId);
              continue;
            }

            if (data.chk) {
              streamingContent += data.chk;
              log('Received chunk, total length:', streamingContent.length);
              onUpdate(streamingContent);
            }

            if (data.eofs === true) {
              log('End of stream marker received');
              onComplete?.();
              return {
                content: streamingContent.trim(),
                messageId: aiMessageId
              };
            }
          } catch (parseError) {
            log('Parse error:', parseError);
            continue;
          }
        }
      }
    }

    log('Stream completed without eofs marker');
    onComplete?.();
    return { content: streamingContent.trim(), messageId: aiMessageId };
  } catch (error) {
    log('Stream error:', error);
    onError?.(error instanceof Error ? error : new Error(String(error)));
    throw error;
  } finally {
    reader.releaseLock();
  }
};

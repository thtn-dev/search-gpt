export const processStreamingResponse = async (
  reader: ReadableStreamDefaultReader<Uint8Array>,
  onUpdate: (content: string) => void
): Promise<string> => {
  const decoder = new TextDecoder();
  let streamingContent = '';

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.trim() === '') continue;

        if (line.startsWith('0:"')) {
          const match = line.match(/^0:"(.*)"/);
          if (match) {
            const textContent = match[1]
              .replace(/\\n/g, '\n')
              .replace(/\\"/g, '"')
              .replace(/\\\\/g, '\\');

            streamingContent += textContent;
            onUpdate(streamingContent);
          }
        } else if (line.startsWith('e:') || line.startsWith('d:')) {
          break;
        }
      }
    }
  } finally {
    reader.releaseLock();
  }

  return streamingContent.trim();
};

import { createOpenAI } from '@ai-sdk/openai';
import { jsonSchema, streamText } from 'ai';

export const maxDuration = 30;

const openai = createOpenAI({
  apiKey: process.env.OPENAI_API_KEY,
  baseURL: process.env.OPENAI_API_BASE_URL
});

export async function POST(req: Request) {
  const { messages, system, tools } = await req.json();
  console.log(messages, system, tools);
  const result = streamText({
    model: openai('gemini-2.0-flash'),
    messages,
    system,
    tools: Object.fromEntries(
      Object.keys(tools).map((name) => [
        name,
        { ...tools[name], parameters: jsonSchema(tools[name].parameters) }
      ])
    )
  });

  return result.toDataStreamResponse();
}

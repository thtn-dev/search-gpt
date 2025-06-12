export type Message = {
  messageId?: string;
  threadId?: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: Date;
  parentId?: string;
  isStreaming?: boolean;
};

export type Thread = {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
};

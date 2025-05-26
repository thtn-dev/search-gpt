export type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: Date;
  threadId: string;
  isStreaming?: boolean;
  parentId?: string;
};

export type Thread = {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
};

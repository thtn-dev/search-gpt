export type Message = {
    role: 'user' | 'assistant';
    content: string;
    createdAt: Date;
    threadId: string;
}
import { ChatAction, ChatState, Message, Thread } from "@/schemas/chat-schema";
import { ReactNode, useContext, useReducer, createContext } from "react";

const initialState: ChatState = {
    threads: [],
    currentThreadId: null,
    isLoading: false,
    error: null,
    streamingMessage: null,
};

function chatReducer(state: ChatState, action: ChatAction): ChatState {
    switch (action.type) {
        case 'SET_LOADING':
            return { ...state, isLoading: action.payload };
        
        case 'SET_ERROR':
            return { ...state, error: action.payload };
        
        case 'CREATE_THREAD':
            const newThread: Thread = {
                id: action.payload.id,
                title: action.payload.title,
                createdAt: new Date(),
                updatedAt: new Date(),
                messages: [],
            };
            return {
                ...state,
                threads: [newThread, ...state.threads],
                currentThreadId: action.payload.id,
            };
        
        case 'SET_CURRENT_THREAD':
            return { ...state, currentThreadId: action.payload };
        
        case 'ADD_MESSAGE':
            return {
                ...state,
                threads: state.threads.map(thread =>
                    thread.id === action.payload.threadId
                        ? {
                            ...thread,
                            messages: [...thread.messages, action.payload],
                            updatedAt: new Date(),
                        }
                        : thread
                ),
                streamingMessage: null,
            };
        
        case 'DELETE_THREAD':
            const updatedThreads = state.threads.filter(thread => thread.id !== action.payload);
            return {
                ...state,
                threads: updatedThreads,
                currentThreadId: state.currentThreadId === action.payload 
                    ? (updatedThreads.length > 0 ? updatedThreads[0].id : null)
                    : state.currentThreadId,
            };
        
        case 'UPDATE_THREAD_TITLE':
            return {
                ...state,
                threads: state.threads.map(thread =>
                    thread.id === action.payload.threadId
                        ? { ...thread, title: action.payload.title, updatedAt: new Date() }
                        : thread
                ),
            };
        
        case 'SET_STREAMING_MESSAGE':
            return { ...state, streamingMessage: action.payload };
        
        case 'CLEAR_MESSAGES':
            return {
                ...state,
                threads: state.threads.map(thread =>
                    thread.id === action.payload
                        ? { ...thread, messages: [], updatedAt: new Date() }
                        : thread
                ),
            };
        
        case 'LOAD_THREADS':
            return { ...state, threads: action.payload };
        
        default:
            return state;
    }
}

export type ChatContextType = {
    state: ChatState;
    dispatch: React.Dispatch<ChatAction>;
    // Helper functions
    createThread: (title?: string) => string;
    sendMessage: (content: string, threadId?: string) => Promise<void>;
    deleteThread: (threadId: string) => void;
    updateThreadTitle: (threadId: string, title: string) => void;
    getCurrentThread: () => Thread | null;
    clearMessages: (threadId: string) => void;
};

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
    const [state, dispatch] = useReducer(chatReducer, initialState);

    const createThread = (title?: string): string => {
        const id = `thread-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const threadTitle = title || `Chat ${new Date().toLocaleString()}`;
        
        dispatch({
            type: 'CREATE_THREAD',
            payload: { id, title: threadTitle }
        });
        
        return id;
    };

    const sendMessage = async (content: string, threadId?: string): Promise<void> => {
        const targetThreadId = threadId || state.currentThreadId;
        
        if (!targetThreadId) {
            throw new Error('No active thread');
        }

        // Add user message
        const userMessage: Message = {
            role: 'user',
            content,
            createdAt: new Date(),
            threadId: targetThreadId,
        };

        dispatch({ type: 'ADD_MESSAGE', payload: userMessage });
        dispatch({ type: 'SET_LOADING', payload: true });

        try {
            // Simulate API call - replace with actual LLM API call
            dispatch({ type: 'SET_STREAMING_MESSAGE', payload: '' });
            
            // Simulate streaming response
            const response = `This is a simulated response to: "${content}"`;
            for (let i = 0; i <= response.length; i++) {
                await new Promise(resolve => setTimeout(resolve, 20));
                dispatch({ type: 'SET_STREAMING_MESSAGE', payload: response.slice(0, i) });
            }

            // Add assistant message
            const assistantMessage: Message = {
                role: 'assistant',
                content: response,
                createdAt: new Date(),
                threadId: targetThreadId,
            };

            dispatch({ type: 'ADD_MESSAGE', payload: assistantMessage });
        } catch (error) {
            dispatch({ type: 'SET_ERROR', payload: error instanceof Error ? error.message : 'Unknown error' });
        } finally {
            dispatch({ type: 'SET_LOADING', payload: false });
        }
    };

    const deleteThread = (threadId: string) => {
        dispatch({ type: 'DELETE_THREAD', payload: threadId });
    };

    const updateThreadTitle = (threadId: string, title: string) => {
        dispatch({ type: 'UPDATE_THREAD_TITLE', payload: { threadId, title } });
    };

    const getCurrentThread = (): Thread | null => {
        if (!state.currentThreadId) return null;
        return state.threads.find(thread => thread.id === state.currentThreadId) || null;
    };

    const clearMessages = (threadId: string) => {
        dispatch({ type: 'CLEAR_MESSAGES', payload: threadId });
    };

    const contextValue: ChatContextType = {
        state,
        dispatch,
        createThread,
        sendMessage,
        deleteThread,
        updateThreadTitle,
        getCurrentThread,
        clearMessages,
    };

    return (
        <ChatContext.Provider value={contextValue}>
            {children}
        </ChatContext.Provider>
    );
}

export function useChatContext(): ChatContextType {
    const context = useContext(ChatContext);
    if (context === undefined) {
        throw new Error('useChatContext must be used within a ChatProvider');
    }
    return context;
}

// Hook để sử dụng thread hiện tại
export function useCurrentThread(): Thread | null {
    const { getCurrentThread } = useChatContext();
    return getCurrentThread();
}

// Hook để lấy messages của thread hiện tại
export function useCurrentMessages(): Message[] {
    const currentThread = useCurrentThread();
    return currentThread?.messages || [];
}
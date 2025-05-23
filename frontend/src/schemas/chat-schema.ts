export type Message = {
  role: "user" | "assistant";
  content: string;
  createdAt: Date;
  threadId: string;
};

export type Thread = {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messages: Message[];
};

export type ChatState = {
  threads: Thread[];
  currentThreadId: string | null;
  isLoading: boolean;
  error: string | null;
  streamingMessage: string | null;
};

export type ChatAction =
  | { type: "SET_LOADING"; payload: boolean }
  | { type: "SET_ERROR"; payload: string | null }
  | { type: "CREATE_THREAD"; payload: { id: string; title: string } }
  | { type: "SET_CURRENT_THREAD"; payload: string }
  | { type: "ADD_MESSAGE"; payload: Message }
  | { type: "DELETE_THREAD"; payload: string }
  | {
      type: "UPDATE_THREAD_TITLE";
      payload: { threadId: string; title: string };
    }
  | { type: "SET_STREAMING_MESSAGE"; payload: string | null }
  | { type: "CLEAR_MESSAGES"; payload: string }
  | { type: "LOAD_THREADS"; payload: Thread[] };

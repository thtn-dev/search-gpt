interface AppConfig {
    apiBaseUrl: string;
    nextAuthSecret: string;
    openAiApiKey: string;
    openAiApiUrl: string;
    googleClientId: string;
    googleClientSecret: string;
}

export const appConfig: AppConfig = {
    apiBaseUrl: process.env.NEXT_PUBLIC_API_ENDPOINT || 'http://localhost:8000',
    nextAuthSecret: process.env.NEXTAUTH_SECRET || 'Ny8Z8ueRNslm52WC8JBqIfmvHZ5YJPPZx7AGC4z3AyQ=',
    openAiApiKey: process.env.OPENAI_API_KEY || 'default',
    openAiApiUrl: process.env.OPENAI_API_URL || 'https://api.openai.com/v1',
    googleClientId: process.env.GOOGLE_CLIENT_ID || 'default',
    googleClientSecret: process.env.GOOGLE_CLIENT_SECRET || 'default',
};


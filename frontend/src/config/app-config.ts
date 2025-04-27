interface AppConfig {
    apiBaseUrl: string;
    nextAuthSecret: string;
    openAiApiKey: string;
    openAiApiUrl: string;
}

export const appConfig: AppConfig = {
    apiBaseUrl: process.env.API_BASE_URL || 'http://localhost:8000',
    nextAuthSecret: process.env.NEXTAUTH_SECRET || 'Ny8Z8ueRNslm52WC8JBqIfmvHZ5YJPPZx7AGC4z3AyQ=',
    openAiApiKey: process.env.OPENAI_API_KEY || 'default',
    openAiApiUrl: process.env.OPENAI_API_URL || 'https://api.openai.com/v1',
};


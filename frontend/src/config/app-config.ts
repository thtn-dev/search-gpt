interface AppConfig {
    apiBaseUrl: string;
    nextAuthSecret: string;
    openAiApiKey: string;
    openAiApiUrl: string;
    googleClientId: string;
    googleClientSecret: string;
    githubClientId: string;
    githubClientSecret: string;
    microsoftClientId: string;
    microsoftClientSecret: string;
    microsoftTenantId: string;
}

export const appConfig: AppConfig = {
    apiBaseUrl: process.env.NEXT_PUBLIC_API_ENDPOINT || 'http://localhost:8000',
    nextAuthSecret: process.env.NEXTAUTH_SECRET || 'Ny8Z8ueRNslm52WC8JBqIfmvHZ5YJPPZx7AGC4z3AyQ=',
    openAiApiKey: process.env.OPENAI_API_KEY || 'default',
    openAiApiUrl: process.env.OPENAI_API_URL || 'https://api.openai.com/v1',

    // Google OAuth
    googleClientId: process.env.GOOGLE_CLIENT_ID || 'default',
    googleClientSecret: process.env.GOOGLE_CLIENT_SECRET || 'default',

    // GitHub OAuth
    githubClientId: process.env.GITHUB_CLIENT_ID || 'default',
    githubClientSecret: process.env.GITHUB_CLIENT_SECRET || 'default',

    // Microsoft OAuth
    microsoftClientId: process.env.MICROSOFT_CLIENT_ID || 'default',
    microsoftClientSecret: process.env.MICROSOFT_CLIENT_SECRET || 'default',
    microsoftTenantId: process.env.MICROSOFT_TENANT_ID || 'default',
};


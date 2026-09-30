/** AI / LLM shared types. */

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ChatRequest {
  projectId: string;
  message: string;
  history: ChatMessage[];
}

export interface ChatResponse {
  role: 'assistant';
  content: string;
  model?: string;
}

export interface SiteGenerateRequest {
  projectId: string;
  prompt: string;
}

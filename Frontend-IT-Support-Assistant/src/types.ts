export interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
}

export interface SourceItem {
  document_id?: string | number;
  original_filename?: string;
  filename?: string;
  document_name?: string;
  page?: number;
  content?: string;
  text?: string;
  metadata?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface ChatResult {
  question: string;
  answer: string;
  sources: SourceItem[];
  raw: unknown;
}

export interface DocumentItem {
  id: string;
  name: string;
  accessLevel: string;
  department?: string;
  uploadedAt?: string;
  raw: unknown;
}

export interface AuditItem {
  id: string;
  action: string;
  username: string;
  createdAt: string;
  details: string;
  raw: unknown;
}

import type { AuditItem, ChatResult, DocumentItem, SourceItem } from "../types";

function asObject(value: unknown): Record<string, any> {
  return value && typeof value === "object" ? value as Record<string, any> : {};
}

function firstArray(value: unknown): unknown[] {
  if (Array.isArray(value)) return value;
  const obj = asObject(value);
  for (const key of ["items", "documents", "results", "data", "records", "logs", "audit_logs"]) {
    if (Array.isArray(obj[key])) return obj[key];
  }
  return [];
}

export function normalizeChat(value: unknown, question: string): ChatResult {
  const obj = asObject(value);
  const answer =
    obj.answer ?? obj.response ?? obj.result?.answer ?? obj.data?.answer ??
    (typeof value === "string" ? value : "The API returned a response, but no answer field was recognized.");
  const sourcesValue = obj.sources ?? obj.citations ?? obj.evidence ?? obj.result?.sources ?? [];
  const sources: SourceItem[] = Array.isArray(sourcesValue) ? sourcesValue.map((s) => asObject(s)) : [];
  return { question: obj.question ?? question, answer: String(answer), sources, raw: value };
}

export function normalizeDocuments(value: unknown): DocumentItem[] {
  return firstArray(value).map((item, index) => {
    const obj = asObject(item);
    const metadata = asObject(obj.metadata);
    return {
      id: String(obj.document_id ?? obj.id ?? metadata.document_id ?? index),
      name: String(obj.original_filename ?? obj.filename ?? obj.name ?? metadata.original_filename ?? `Document ${index + 1}`),
      accessLevel: String(obj.access_level ?? metadata.access_level ?? "Not provided"),
      department: obj.department ?? metadata.department,
      uploadedAt: obj.uploaded_at ?? obj.created_at ?? metadata.uploaded_at,
      raw: item,
    };
  });
}

export function normalizeAudit(value: unknown): AuditItem[] {
  return firstArray(value).map((item, index) => {
    const obj = asObject(item);
    return {
      id: String(obj.id ?? obj.audit_id ?? index),
      action: String(obj.action ?? obj.event ?? "Activity"),
      username: String(obj.username ?? obj.user?.username ?? obj.user_id ?? "—"),
      createdAt: String(obj.created_at ?? obj.timestamp ?? obj.date ?? ""),
      details:
      typeof obj.details === "object" && obj.details !== null
        ? JSON.stringify(obj.details, null, 2)
        : String(obj.details ?? obj.description ?? obj.resource ?? ""),
      raw: item,
    };
  });
}

export function extractStats(value: unknown): Array<{ label: string; value: string }> {
  const obj = asObject(value);
  const source = asObject(obj.stats ?? obj.statistics ?? obj.data ?? obj);
  return Object.entries(source)
    .filter(([, v]) => typeof v === "string" || typeof v === "number" || typeof v === "boolean")
    .slice(0, 8)
    .map(([key, v]) => ({
      label: key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
      value: String(v),
    }));
}

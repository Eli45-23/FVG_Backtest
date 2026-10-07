export async function api(path: string, body?: unknown, method?: string) {
  const r = await fetch("/api" + path, {
    method: method || (body ? "POST" : "GET"),
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await r.json();
  if (!r.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : JSON.stringify(data.detail),
    );
  return data;
}
export type InputMeta = {
  id: string;
  label: string;
  type: string;
  default: unknown;
  min?: number;
  max?: number;
  step?: number;
  choices?: string[];
  description?: string;
};
export type Strategy = {
  id: string;
  name: string;
  source: string;
  version_id: string;
  current_version: number;
  description: string;
  tags: string[];
};
export type Run = {
  id: string;
  name: string;
  status: string;
  created_at: string;
  strategy_version_id: string;
  progress: string;
  error?: string;
  notes: string;
  config: any;
  metrics: any;
};

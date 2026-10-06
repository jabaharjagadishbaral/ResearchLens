import { createClient } from "./api.ts";
import { getToken } from "./session.ts";
export const api = createClient({ baseUrl: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000", getToken });

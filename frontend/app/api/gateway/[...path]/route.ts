/** Local-demo-only server-side gateway.
 * Secrets stay on the Next.js server. This is NOT an authentication system:
 * a local user can deliberately select any fictional demo identity.
 */
import { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const DEMO_USERS = new Set([
  "aster-admin", "aster-designer", "aster-procurement", "aster-pm",
  "rival-admin", "rival-designer",
]);

const noCache = { "Cache-Control": "no-store, private", "X-Content-Type-Options": "nosniff" };

type Ctx = { params: Promise<{ path: string[] }> };

function allowedPath(method: string, path: string[]): boolean {
  if (path.length === 1 && path[0] === "documents") {
    return method === "GET" || method === "POST";
  }
  if (path.length === 2 && path[0] === "documents" && /^[a-zA-Z0-9-]{1,64}$/.test(path[1])) {
    return method === "GET";
  }
  if (path.length === 3 && path[0] === "documents" && path[2] === "permissions"
      && /^[a-zA-Z0-9-]{1,64}$/.test(path[1])) {
    return method === "PUT";
  }
  if (path.length === 2 && path[0] === "knowledge"
      && (path[1] === "ask" || path[1] === "search")) {
    return method === "POST";
  }
  return false;
}

async function gateway(req: NextRequest, ctx: Ctx): Promise<Response> {
  const { path } = await ctx.params;
  if (!allowedPath(req.method, path)) {
    return Response.json({ detail: "Route unavailable" }, { status: 404, headers: noCache });
  }

  const secret = process.env.DEV_API_KEY;
  const base = process.env.BACKEND_API_URL || "http://127.0.0.1:8000";
  if (!secret || secret.startsWith("replace_")) {
    return Response.json({ detail: "Configure DEV_API_KEY in frontend/.env.local" },
      { status: 503, headers: noCache });
  }
  const localhostBackend = /^http:\/\/(127\.0\.0\.1|localhost)(:\d+)?\/?$/.test(base);
  const composeBackend = process.env.DOCKER_LOCAL_DEMO === "1" && base === "http://api:8000";
  if (!localhostBackend && !composeBackend) {
    return Response.json({ detail: "BACKEND_API_URL must be a local HTTP address" },
      { status: 503, headers: noCache });
  }

  const demoUser = req.headers.get("x-demo-user") ?? "";
  if (!DEMO_USERS.has(demoUser)) {
    return Response.json({ detail: "Unknown demo identity" }, { status: 400, headers: noCache });
  }

  const incoming = new URL(req.url);
  const dest = `${base.replace(/\/$/, "")}/api/v1/${path.join("/")}${incoming.search}`;
  const headers = new Headers({
    "x-api-key": secret,
    "x-demo-user": demoUser,
    "accept": "application/json",
  });

  let body: BodyInit | undefined;
  if (req.method !== "GET") {
    if (path[0] === "documents" && path.length === 1) {
      const form = await req.formData();
      const upload = form.get("file");
      if (!(upload instanceof File) || upload.size > 15 * 1024 * 1024) {
        return Response.json({ detail: "Select a file smaller than 15 MB" },
          { status: 413, headers: noCache });
      }
      body = form; // Let fetch set multipart boundary.
    } else {
      const raw = await req.text();
      if (raw.length > 16_384) {
        return Response.json({ detail: "Payload too large" },
          { status: 413, headers: noCache });
      }
      body = raw;
      headers.set("content-type", "application/json");
    }
  }

  try {
    const result = await fetch(dest, {
      method: req.method,
      headers,
      body,
      cache: "no-store",
      signal: AbortSignal.timeout(90_000),
    });
    // All backend application responses are JSON; avoid exposing non-JSON error pages.
    const type = result.headers.get("content-type") || "";
    if (!type.includes("application/json")) {
      return Response.json({ detail: "Backend returned an unexpected response" },
        { status: 502, headers: noCache });
    }
    const data = await result.json();
    return Response.json(data, { status: result.status, headers: noCache });
  } catch {
    return Response.json({ detail: "Backend unavailable. Start FastAPI on port 8000." },
      { status: 502, headers: noCache });
  }
}

export async function GET(req: NextRequest, ctx: Ctx) { return gateway(req, ctx); }
export async function POST(req: NextRequest, ctx: Ctx) { return gateway(req, ctx); }
export async function PUT(req: NextRequest, ctx: Ctx) { return gateway(req, ctx); }

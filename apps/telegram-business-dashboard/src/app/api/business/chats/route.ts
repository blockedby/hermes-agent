import { NextRequest } from "next/server";

import {
  authenticateTelegramAdmin,
  isNextResponse,
  safeHermesResponse,
} from "@/lib/server/business-route";
import {
  callHermesDashboard,
  type BusinessChatsResponse,
} from "@/lib/server/hermes-dashboard-api";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const session = authenticateTelegramAdmin(request);
  if (isNextResponse(session)) {
    return session;
  }

  const searchParams = new URLSearchParams();
  for (const key of ["mode", "q", "cursor"] as const) {
    const value = request.nextUrl.searchParams.get(key);
    if (value) {
      searchParams.set(key, value);
    }
  }

  return safeHermesResponse(() =>
    callHermesDashboard<BusinessChatsResponse>("/api/business/chats", {
      actorUserId: session.telegramUserId,
      searchParams,
    }),
  );
}

import { NextRequest } from "next/server";

import {
  authenticateTelegramAdmin,
  isNextResponse,
  safeHermesResponse,
} from "@/lib/server/business-route";
import {
  callHermesDashboard,
  type BusinessHistoryResponse,
} from "@/lib/server/hermes-dashboard-api";

type ChatTokenContext = {
  params: Promise<{ token: string }>;
};

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: NextRequest, { params }: ChatTokenContext) {
  const session = authenticateTelegramAdmin(request);
  if (isNextResponse(session)) {
    return session;
  }

  const searchParams = new URLSearchParams();
  for (const key of ["limit", "cursor"] as const) {
    const value = request.nextUrl.searchParams.get(key);
    if (value) {
      searchParams.set(key, value);
    }
  }

  const { token } = await params;
  return safeHermesResponse(() =>
    callHermesDashboard<BusinessHistoryResponse>(
      `/api/business/chats/${encodeURIComponent(token)}/history`,
      {
        actorUserId: session.telegramUserId,
        searchParams,
      },
    ),
  );
}

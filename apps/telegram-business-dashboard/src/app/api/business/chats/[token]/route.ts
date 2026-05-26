import { NextRequest } from "next/server";

import {
  authenticateTelegramAdmin,
  isNextResponse,
  safeHermesResponse,
  withDashboardSessionCookie,
} from "@/lib/server/business-route";
import {
  callHermesDashboard,
  type BusinessChatResponse,
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

  const { token } = await params;
  return withDashboardSessionCookie(
    await safeHermesResponse(() =>
      callHermesDashboard<BusinessChatResponse>(`/api/business/chats/${encodeURIComponent(token)}`, {
        actorUserId: session.telegramUserId,
      }),
    ),
    session,
  );
}

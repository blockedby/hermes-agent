import { NextRequest } from "next/server";

import {
  authenticateTelegramAdmin,
  isNextResponse,
  parseJsonBody,
  postBodyWithoutInitData,
  safeHermesResponse,
  withDashboardSessionCookie,
} from "@/lib/server/business-route";
import {
  callHermesDashboard,
  type BusinessModeResponse,
} from "@/lib/server/hermes-dashboard-api";

type ChatTokenContext = {
  params: Promise<{ token: string }>;
};

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request: NextRequest, { params }: ChatTokenContext) {
  const body = await parseJsonBody(request);
  if (isNextResponse(body)) {
    return body;
  }

  const session = authenticateTelegramAdmin(request, body);
  if (isNextResponse(session)) {
    return session;
  }

  const { token } = await params;
  return withDashboardSessionCookie(
    await safeHermesResponse(() =>
      callHermesDashboard<BusinessModeResponse>(
        `/api/business/chats/${encodeURIComponent(token)}/mode`,
        {
          method: "POST",
          actorUserId: session.telegramUserId,
          body: postBodyWithoutInitData(body, ["mode"]),
        },
      ),
    ),
    session,
  );
}

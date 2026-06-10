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
  type BusinessSettingsResponse,
} from "@/lib/server/hermes-dashboard-api";

type ChatTokenContext = {
  params: Promise<{ token: string }>;
};

const ALLOWED_SETTINGS_KEYS = [
  "assistantDisplayName",
  "assistantPrefix",
  "dialogPrompt",
  "dialogNotes",
  "invocationPolicy",
];

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
      callHermesDashboard<BusinessSettingsResponse>(
        `/api/business/chats/${encodeURIComponent(token)}/settings`,
        {
          actorUserId: session.telegramUserId,
        },
      ),
    ),
    session,
  );
}

export async function PATCH(request: NextRequest, { params }: ChatTokenContext) {
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
      callHermesDashboard<BusinessSettingsResponse>(
        `/api/business/chats/${encodeURIComponent(token)}/settings`,
        {
          method: "PATCH",
          actorUserId: session.telegramUserId,
          body: postBodyWithoutInitData(body, ALLOWED_SETTINGS_KEYS),
        },
      ),
    ),
    session,
  );
}

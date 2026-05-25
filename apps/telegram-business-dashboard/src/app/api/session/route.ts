import { NextRequest, NextResponse } from "next/server";
import {
  TelegramAdminAuthError,
  validateTelegramAdminInitData,
} from "@/lib/server/telegram-auth";

export const runtime = "nodejs";

type SessionRequestBody = {
  initData?: unknown;
};

export async function POST(request: NextRequest) {
  let body: SessionRequestBody;
  try {
    body = (await request.json()) as SessionRequestBody;
  } catch {
    return NextResponse.json({ ok: false, error: "invalid_json" }, { status: 400 });
  }

  if (typeof body.initData !== "string" || !body.initData) {
    return NextResponse.json({ ok: false, error: "missing_init_data" }, { status: 400 });
  }

  try {
    const user = validateTelegramAdminInitData(body.initData);
    return NextResponse.json({ ok: true, user });
  } catch (error) {
    if (error instanceof TelegramAdminAuthError) {
      if (error.code === "forbidden") {
        return NextResponse.json({ ok: false, error: "forbidden" }, { status: 403 });
      }
      if (error.code === "config_error") {
        return NextResponse.json({ ok: false, error: "auth_not_configured" }, { status: 500 });
      }
    }
    return NextResponse.json({ ok: false, error: "unauthorized" }, { status: 401 });
  }
}

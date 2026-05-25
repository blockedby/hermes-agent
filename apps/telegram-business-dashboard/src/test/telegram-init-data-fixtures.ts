import { sign } from "@tma.js/init-data-node";

export const TEST_BOT_TOKEN = "123456:TEST_BOT_TOKEN";
export const TEST_ADMIN_USER_ID = 1001;
export const TEST_NON_ADMIN_USER_ID = 2002;

export function signedInitDataFor(userId: number, authDate = new Date()) {
  return sign(
    {
      user: {
        id: userId,
        first_name: userId === TEST_ADMIN_USER_ID ? "Ada" : "Grace",
        username: userId === TEST_ADMIN_USER_ID ? "ada_admin" : "grace_viewer",
      },
    },
    TEST_BOT_TOKEN,
    authDate,
  );
}

export function tamperInitDataHash(initData: string) {
  const params = new URLSearchParams(initData);
  const hash = params.get("hash") ?? "";
  params.set("hash", `${hash.slice(0, -1)}${hash.endsWith("0") ? "1" : "0"}`);
  return params.toString();
}

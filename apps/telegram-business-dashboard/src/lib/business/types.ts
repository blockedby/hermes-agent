export type BusinessChatMode = "ignored" | "watch" | "draft" | "auto";
export type BusinessCanReply = "yes" | "no" | "unknown";
export type BusinessInvocationPolicy = "off" | "mention_draft" | "mention_direct";

export type BusinessChatSummary = {
  token: string;
  displayName: string;
  username?: string;
  mode: BusinessChatMode;
  lastSeenAt: number;
  lastMessagePreview: string;
  canReply: BusinessCanReply;
  pendingDraftCount: number;
  failedDraftCount: number;
  rulesCount: number;
  hasDirectTopic: boolean;
  isBot?: boolean;
};

export type BusinessChatDetail = BusinessChatSummary & {
  latestMessage?: {
    preview: string;
    hasText: boolean;
    hasMessageId: boolean;
  };
  lastDashboardDraftStatus?: string;
};

export type BusinessHistoryEvent = {
  event_id?: string;
  created_at?: number;
  type?: string;
  preview?: string;
  message_id?: string;
  approval_id?: string;
  mode?: BusinessChatMode;
  actor_user_id?: string;
};

export type BusinessChatsResponse = {
  chats: BusinessChatSummary[];
  count: number;
};

export type BusinessChatResponse = {
  chat: BusinessChatDetail;
  history?: BusinessHistoryEvent[];
};

export type BusinessModeResponse = {
  chat: BusinessChatDetail;
};

export interface BusinessDialogSettings {
  assistantDisplayName: string;
  assistantPrefix: string;
  dialogPrompt: string;
  dialogNotes: string;
  invocationPolicy: BusinessInvocationPolicy;
  updatedAt?: number;
  updatedByUserId?: string;
}

export type BusinessSettingsPatch = Partial<
  Pick<
    BusinessDialogSettings,
    "assistantDisplayName" | "assistantPrefix" | "dialogPrompt" | "dialogNotes" | "invocationPolicy"
  >
>;

export interface BusinessSettingsResponse {
  settings: BusinessDialogSettings;
}

export type BusinessDraftResponse = {
  draft: {
    status: string;
    chatToken: string;
    source: "latest";
    sentToCustomer: false;
    prompt?: string;
  };
};

export type BusinessHistoryResponse = {
  chatToken: string;
  history: BusinessHistoryEvent[];
  nextCursor: string | null;
  count: number;
};

import { ChatDetailShell } from "@/components/business/chat-detail-shell";

type ChatDetailPageProps = {
  params: Promise<{ token: string }>;
};

export default async function ChatDetailPage({ params }: ChatDetailPageProps) {
  const { token } = await params;
  return <ChatDetailShell token={token} />;
}

import { Sidebar } from "@/components/layout/Sidebar";
import { ConversationLoader } from "./ConversationLoader";

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-full">
      <ConversationLoader />
      <Sidebar />
      <div className="flex flex-1 flex-col min-w-0 h-full">{children}</div>
    </div>
  );
}

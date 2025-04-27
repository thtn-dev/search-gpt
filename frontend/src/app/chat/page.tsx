"use client";
import { Thread } from "@/components/assistant-ui/thread";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { AssistantRuntimeProvider } from "@assistant-ui/react";
import { useChatRuntime } from "@assistant-ui/react-ai-sdk";
import { signIn, useSession } from "next-auth/react";

function ChatPage() {
  const { data: session, status } = useSession();
  const runtime = useChatRuntime({
    api: "/api/chat",
  });

  if (status === "loading") {
    return <p>Loading...</p>;
  }

  if (status === "unauthenticated") {
    return (
      <div>
        <p>Bạn chưa đăng nhập</p>
        <button onClick={() => signIn()}>Đăng nhập</button>
      </div>
    );
  }

  return (
      
      <AssistantRuntimeProvider runtime={runtime}>
      <header className="flex h-16 shrink-0 items-center gap-2 transition-[width,height] ease-linear group-has-[[data-collapsible=icon]]/sidebar-wrapper:h-12">
        <div className="flex items-center gap-2 px-4">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-2 h-4" />
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem className="hidden md:block">
                <BreadcrumbLink href="#">
                  Building Your Application {session?.user.email}
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator className="hidden md:block" />
              <BreadcrumbItem>
                <BreadcrumbPage>Data Fetching</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
        </div>
      </header>
        <main className="h-[calc(100dvh-4rem)] grid gap-x-2 px-4 py-4">
          <Thread />
        </main>
      </AssistantRuntimeProvider>
  );
}

export default ChatPage;

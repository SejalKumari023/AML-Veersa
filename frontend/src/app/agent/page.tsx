"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getUser } from "~/lib/auth";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "~/components/ui/tabs";
import { AgentChat } from "~/components/agent/AgentChat";
import { PromptEditor } from "~/components/agent/PromptEditor";
import { Bot, SlidersHorizontal } from "lucide-react";

export default function AgentPage() {
    const router = useRouter();
    useEffect(() => {
        if (!getUser()) router.replace("/auth/login");
    }, [router]);

    return (
        <div className="flex flex-col h-[calc(100vh-4rem)] p-6 gap-4">
            <div>
                <h1 className="text-2xl font-semibold">AI Agent Hub</h1>
                <p className="text-muted-foreground text-sm mt-1">
                    Chat with the AML monitoring or document corroboration agent. Queries are automatically routed to the right backend.
                </p>
            </div>

            <Tabs defaultValue="chat" className="flex-1 flex flex-col min-h-0">
                <TabsList className="shrink-0">
                    <TabsTrigger value="chat" className="gap-1.5">
                        <Bot className="size-4" />
                        Chat
                    </TabsTrigger>
                    <TabsTrigger value="prompts" className="gap-1.5">
                        <SlidersHorizontal className="size-4" />
                        Prompt Editor
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="chat" className="flex-1 border rounded-lg overflow-hidden mt-2 min-h-0">
                    <AgentChat title="AML & Document Intelligence" />
                </TabsContent>

                <TabsContent value="prompts" className="flex-1 overflow-y-auto mt-2 min-h-0">
                    <PromptEditor />
                </TabsContent>
            </Tabs>
        </div>
    );
}

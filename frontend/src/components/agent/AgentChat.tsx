"use client";

import { useEffect, useRef, useState } from "react";
import { Badge } from "~/components/ui/badge";
import { Button } from "~/components/ui/button";
import { Card } from "~/components/ui/card";
import {
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger,
} from "~/components/ui/collapsible";
import { Skeleton } from "~/components/ui/skeleton";
import { Textarea } from "~/components/ui/textarea";
import { ChevronDown, ChevronUp, Send, Bot, User } from "lucide-react";

interface ToolCallEntry {
    tool_name: string;
    input: Record<string, unknown>;
    output: unknown;
}

interface ChatMessage {
    role: "user" | "assistant";
    content: string;
    target?: "aml" | "document";
    thought_process?: string;
    tool_calls?: ToolCallEntry[];
}

interface OrchestrationResponse {
    target: "aml" | "document";
    agent_response: {
        response: string;
        tool_calls: ToolCallEntry[];
        thought_process: string;
    };
    error?: string;
}

interface AgentChatProps {
    title?: string;
    defaultContext?: string;
}

export function AgentChat({ title = "AI Agent", defaultContext = "" }: AgentChatProps) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState(defaultContext);
    const [loading, setLoading] = useState(false);
    const [openThought, setOpenThought] = useState<number | null>(null);
    const [openTools, setOpenTools] = useState<number | null>(null);
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    const buildHistory = (msgs: ChatMessage[]) =>
        msgs.map((m) => ({ role: m.role, content: m.content }));

    const handleSend = async () => {
        const text = input.trim();
        if (!text || loading) return;

        const userMsg: ChatMessage = { role: "user", content: text };
        const newMessages = [...messages, userMsg];
        setMessages(newMessages);
        setInput("");
        setLoading(true);

        try {
            const res = await fetch("/api/orchestrate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: text,
                    conversation_history: buildHistory(messages),
                }),
            });

            const data = (await res.json()) as OrchestrationResponse;

            if (data.error ?? !data.agent_response) {
                setMessages((prev) => [
                    ...prev,
                    { role: "assistant", content: data.error ?? "Agent returned an empty response." },
                ]);
            } else {
                setMessages((prev) => [
                    ...prev,
                    {
                        role: "assistant",
                        content: data.agent_response.response,
                        target: data.target,
                        thought_process: data.agent_response.thought_process,
                        tool_calls: data.agent_response.tool_calls,
                    },
                ]);
            }
        } catch (err) {
            setMessages((prev) => [
                ...prev,
                { role: "assistant", content: `Error: ${String(err)}` },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            void handleSend();
        }
    };

    return (
        <div className="flex flex-col h-full min-h-0">
            {title && (
                <div className="flex items-center gap-2 px-4 py-3 border-b shrink-0">
                    <Bot className="size-4 text-primary" />
                    <span className="font-semibold text-sm">{title}</span>
                </div>
            )}

            {/* Message list */}
            <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4 min-h-0">
                {messages.length === 0 && (
                    <p className="text-muted-foreground text-sm text-center pt-8">
                        Ask anything about transactions, alerts, customers, or documents.
                    </p>
                )}

                {messages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                        <div className={`max-w-[85%] space-y-1 ${msg.role === "user" ? "items-end" : "items-start"} flex flex-col`}>
                            {/* Bubble */}
                            <div
                                className={`rounded-lg px-3 py-2 text-sm whitespace-pre-wrap ${
                                    msg.role === "user"
                                        ? "bg-primary text-primary-foreground"
                                        : "bg-muted text-foreground"
                                }`}
                            >
                                {msg.role === "assistant" && msg.target && (
                                    <Badge
                                        variant="outline"
                                        className="mb-1 text-xs"
                                    >
                                        {msg.target === "aml" ? "AML Agent" : "Document Agent"}
                                    </Badge>
                                )}
                                <p>{msg.content}</p>
                            </div>

                            {/* Thought process (assistant only) */}
                            {msg.role === "assistant" && msg.thought_process && (
                                <Collapsible
                                    open={openThought === i}
                                    onOpenChange={(o) => setOpenThought(o ? i : null)}
                                >
                                    <CollapsibleTrigger asChild>
                                        <Button variant="ghost" size="sm" className="h-6 px-2 text-xs text-muted-foreground gap-1">
                                            {openThought === i ? <ChevronUp className="size-3" /> : <ChevronDown className="size-3" />}
                                            Thought process
                                        </Button>
                                    </CollapsibleTrigger>
                                    <CollapsibleContent>
                                        <Card className="p-2 text-xs text-muted-foreground font-mono whitespace-pre-wrap max-h-48 overflow-y-auto">
                                            {msg.thought_process}
                                        </Card>
                                    </CollapsibleContent>
                                </Collapsible>
                            )}

                            {/* Tool calls (assistant only) */}
                            {msg.role === "assistant" && msg.tool_calls && msg.tool_calls.length > 0 && (
                                <Collapsible
                                    open={openTools === i}
                                    onOpenChange={(o) => setOpenTools(o ? i : null)}
                                >
                                    <CollapsibleTrigger asChild>
                                        <Button variant="ghost" size="sm" className="h-6 px-2 text-xs text-muted-foreground gap-1">
                                            {openTools === i ? <ChevronUp className="size-3" /> : <ChevronDown className="size-3" />}
                                            {msg.tool_calls.length} tool call{msg.tool_calls.length > 1 ? "s" : ""}
                                        </Button>
                                    </CollapsibleTrigger>
                                    <CollapsibleContent className="space-y-1">
                                        {msg.tool_calls.map((tc, j) => (
                                            <Card key={j} className="p-2 text-xs space-y-1">
                                                <div className="flex items-center gap-1">
                                                    <Badge className="text-[10px] h-4">{tc.tool_name}</Badge>
                                                </div>
                                                {Object.keys(tc.input ?? {}).length > 0 && (
                                                    <pre className="text-muted-foreground bg-muted rounded p-1 overflow-x-auto">
                                                        {JSON.stringify(tc.input, null, 2)}
                                                    </pre>
                                                )}
                                                <pre className="text-foreground bg-muted/50 rounded p-1 overflow-x-auto max-h-32">
                                                    {typeof tc.output === "string"
                                                        ? tc.output.slice(0, 400)
                                                        : JSON.stringify(tc.output, null, 2).slice(0, 400)}
                                                </pre>
                                            </Card>
                                        ))}
                                    </CollapsibleContent>
                                </Collapsible>
                            )}
                        </div>
                    </div>
                ))}

                {loading && (
                    <div className="flex justify-start">
                        <div className="space-y-1 max-w-[85%]">
                            <Skeleton className="h-4 w-48" />
                            <Skeleton className="h-4 w-32" />
                        </div>
                    </div>
                )}

                <div ref={bottomRef} />
            </div>

            {/* Input area */}
            <div className="px-4 py-3 border-t shrink-0 flex gap-2 items-end">
                <Textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask about transactions, alerts, customers, or documents… (Enter to send)"
                    className="resize-none text-sm min-h-[60px] max-h-[120px]"
                    rows={2}
                    disabled={loading}
                />
                <Button
                    size="icon"
                    onClick={() => void handleSend()}
                    disabled={loading || !input.trim()}
                    className="shrink-0"
                >
                    <Send className="size-4" />
                </Button>
            </div>
        </div>
    );
}

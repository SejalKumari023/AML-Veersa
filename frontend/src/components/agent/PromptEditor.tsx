"use client";

import { useEffect, useState } from "react";
import { Badge } from "~/components/ui/badge";
import { Button } from "~/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "~/components/ui/card";
import { Textarea } from "~/components/ui/textarea";
import { Skeleton } from "~/components/ui/skeleton";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "/api";
const LLM_API_URL = process.env.NEXT_PUBLIC_API_URL_2 ?? "/llm-api";

interface Prompt {
    name: string;
    description: string;
    content: string;
    source: "aml" | "document";
}

interface PromptCardProps {
    prompt: Prompt;
}

function PromptCard({ prompt }: PromptCardProps) {
    const [content, setContent] = useState(prompt.content);
    const [saving, setSaving] = useState(false);
    const [status, setStatus] = useState<"idle" | "saved" | "error">("idle");

    const handleSave = async () => {
        setSaving(true);
        setStatus("idle");
        try {
            const base = prompt.source === "aml" ? API_URL : LLM_API_URL;
            const res = await fetch(`${base}/prompts/${prompt.name}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ content }),
            });
            setStatus(res.ok ? "saved" : "error");
        } catch {
            setStatus("error");
        } finally {
            setSaving(false);
            setTimeout(() => setStatus("idle"), 3000);
        }
    };

    return (
        <Card>
            <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                    <div>
                        <CardTitle className="text-sm font-medium font-mono">{prompt.name}</CardTitle>
                        {prompt.description && (
                            <CardDescription className="text-xs mt-0.5">{prompt.description}</CardDescription>
                        )}
                    </div>
                    <Badge variant={prompt.source === "aml" ? "default" : "secondary"} className="text-[10px] shrink-0">
                        {prompt.source === "aml" ? "AML Agent" : "Document Agent"}
                    </Badge>
                </div>
            </CardHeader>
            <CardContent className="space-y-2">
                <Textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    className="font-mono text-xs min-h-[120px] resize-y"
                />
                <div className="flex items-center gap-2">
                    <Button size="sm" onClick={() => void handleSave()} disabled={saving}>
                        {saving ? "Saving…" : "Save"}
                    </Button>
                    {status === "saved" && (
                        <span className="text-xs text-emerald-600 font-medium">Saved</span>
                    )}
                    {status === "error" && (
                        <span className="text-xs text-destructive font-medium">Save failed</span>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}

export function PromptEditor() {
    const [prompts, setPrompts] = useState<Prompt[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchPrompts = async () => {
            try {
                const [amlRes, docRes] = await Promise.allSettled([
                    fetch(`${API_URL}/prompts`),
                    fetch(`${LLM_API_URL}/prompts`),
                ]);

                const combined: Prompt[] = [];

                if (amlRes.status === "fulfilled" && amlRes.value.ok) {
                    const data = (await amlRes.value.json()) as Array<{ name: string; description: string; content: string }>;
                    combined.push(...data.map((p) => ({ ...p, source: "aml" as const })));
                }

                if (docRes.status === "fulfilled" && docRes.value.ok) {
                    const data = (await docRes.value.json()) as Array<{ name: string; description: string; content: string }>;
                    combined.push(...data.map((p) => ({ ...p, source: "document" as const })));
                }

                if (combined.length === 0) {
                    setError("Could not load prompts from either backend. Make sure both services are running.");
                }

                setPrompts(combined);
            } catch (err) {
                setError(String(err));
            } finally {
                setLoading(false);
            }
        };

        void fetchPrompts();
    }, []);

    if (loading) {
        return (
            <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                    <Card key={i}>
                        <CardHeader>
                            <Skeleton className="h-4 w-32" />
                            <Skeleton className="h-3 w-48 mt-1" />
                        </CardHeader>
                        <CardContent>
                            <Skeleton className="h-24 w-full" />
                        </CardContent>
                    </Card>
                ))}
            </div>
        );
    }

    if (error) {
        return (
            <Card>
                <CardContent className="pt-6">
                    <p className="text-destructive text-sm">{error}</p>
                </CardContent>
            </Card>
        );
    }

    return (
        <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
                Edit agent system prompts below. Changes take effect on the next agent query.
            </p>
            {prompts.map((p) => (
                <PromptCard key={`${p.source}-${p.name}`} prompt={p} />
            ))}
        </div>
    );
}

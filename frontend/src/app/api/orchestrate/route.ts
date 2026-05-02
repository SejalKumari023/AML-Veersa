import { type NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "/api";
const LLM_API_URL = process.env.NEXT_PUBLIC_API_URL_2 ?? "/llm-api";

const DOC_KEYWORDS = [
    "document", "pdf", "image", "tamper", "ocr", "forensic",
    "authenticity", "verify document", "upload file", "scan",
    "photo", "picture", "signature", "watermark", "file analysis",
    "validation", "report", "corroboration",
];

function classifyIntent(message: string): "aml" | "document" {
    const lower = message.toLowerCase();
    return DOC_KEYWORDS.some((k) => lower.includes(k)) ? "document" : "aml";
}

export async function POST(req: NextRequest) {
    try {
        const body = (await req.json()) as {
            message: string;
            conversation_history: Array<{ role: string; content: string }>;
            context?: Record<string, unknown>;
        };

        const target = classifyIntent(body.message);
        const backendBase = target === "aml" ? API_URL : LLM_API_URL;
        const backendUrl = `${backendBase}/agent`;

        const agentRes = await fetch(backendUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });

        if (!agentRes.ok) {
            const errorText = await agentRes.text();
            return NextResponse.json(
                { error: `Backend agent error (${agentRes.status}): ${errorText}` },
                { status: agentRes.status },
            );
        }

        const agentData = (await agentRes.json()) as unknown;
        return NextResponse.json({ target, agent_response: agentData });
    } catch (err) {
        console.error("Orchestrate error:", err);
        return NextResponse.json(
            { error: "Internal orchestration error" },
            { status: 500 },
        );
    }
}

"use client"

import { useState } from "react"
import { AlertCircle, CheckCircle2, Plus, FileText, Link as LinkIcon, Eye } from "lucide-react"
import Link from "next/link"
import {
    Card,
    CardHeader,
    CardTitle,
    CardDescription,
    CardContent,
} from "~/components/ui/card"
import { Button } from "~/components/ui/button"

interface RuleNotice {
    id: string
    title: string
    regulator: string
    category: string
    legalInterpretation: string
    hasRule: boolean
    ruleId?: string
    ruleName?: string
    createdDate?: string
    priority: "high" | "medium" | "low"
}

interface Rule {
    id: string
    noticeId: string
    name: string
    description: string
    createdDate: string
    status: "draft" | "active" | "archived"
}

export default function CompliancePage() {
    const [notices, setNotices] = useState<RuleNotice[]>([
        {
            id: "1",
            title: "Regulatory Update on AML Compliance",
            regulator: "Financial Conduct Authority",
            category: "AML/KYC",
            legalInterpretation:
                "New requirements mandate enhanced customer verification at onboarding. Verification must include facial recognition and enhanced due diligence for high-risk jurisdictions. Implementation deadline: 60 days.",
            hasRule: true,
            ruleId: "r1",
            ruleName: "Enhanced AML Customer Verification",
            createdDate: "2025-11-05",
            priority: "high",
        },
        {
            id: "2",
            title: "Data Protection Notice",
            regulator: "Information Commissioner's Office",
            category: "Data Privacy",
            legalInterpretation:
                "Personal data retention must be limited to 3 years maximum. Data deletion processes must be automated and logged. PII fields require encryption at rest and in transit.",
            hasRule: false,
            priority: "high",
        },
        {
            id: "3",
            title: "Market Abuse Regulation Update",
            regulator: "European Securities and Markets Authority",
            category: "Market Conduct",
            legalInterpretation:
                "Transaction monitoring must capture all trading activities with real-time alerting for suspicious patterns. Maintain audit trail for 7 years. Escalation protocol requires human review within 4 hours.",
            hasRule: false,
            priority: "medium",
        },
        {
            id: "4",
            title: "Interest Rate Benchmark Guidelines",
            regulator: "Financial Conduct Authority",
            category: "Market Conduct",
            legalInterpretation:
                "All interest rate submissions must be validated against independent market data. Non-compliance results in automatic flagging for manual review before submission.",
            hasRule: true,
            ruleId: "r2",
            ruleName: "Interest Rate Benchmark Validation",
            createdDate: "2025-10-20",
            priority: "medium",
        },
    ])

    const [rules] = useState<Rule[]>([
        {
            id: "r1",
            noticeId: "1",
            name: "Enhanced AML Customer Verification",
            description:
                "Implement facial recognition and enhanced due diligence for high-risk jurisdictions",
            createdDate: "2025-11-05",
            status: "active",
        },
        {
            id: "r2",
            noticeId: "4",
            name: "Interest Rate Benchmark Validation",
            description:
                "Validate all interest rate submissions against independent market data",
            createdDate: "2025-10-20",
            status: "active",
        },
    ])

    const [selectedNotice, setSelectedNotice] = useState<RuleNotice | null>(null)
    const [showCreateModal, setShowCreateModal] = useState(false)
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const getPriorityColor = (priority: RuleNotice["priority"]) => {
        switch (priority) {
            case "high":
                return "text-destructive bg-destructive/10"
            case "medium":
                return "text-amber-600 bg-amber-100 dark:bg-amber-900/20"
            case "low":
                return "text-blue-600 bg-blue-100 dark:bg-blue-900/20"
            default:
                return "text-muted-foreground"
        }
    }

    const noRuleCount = notices.filter((n) => !n.hasRule).length
    const withRuleCount = notices.filter((n) => n.hasRule).length
    const highPriorityNoRule = notices.filter((n) => !n.hasRule && n.priority === "high").length

    const handleCreateRule = (noticeId: string) => {
        setError(null)
        setShowCreateModal(true)
    }

    const handleSubmitRule = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault()

        if (!selectedNotice) return

        setIsSubmitting(true)
        setError(null)

        try {
            const formData = new FormData(e.currentTarget)
            const ruleName = formData.get("ruleName") as string
            const description = formData.get("description") as string

            if (!ruleName || !description) {
                setError("Rule name and description are required")
                setIsSubmitting(false)
                return
            }

            const apiUrl = process.env.NEXT_PUBLIC_API_URL || "/api"
            const response = await fetch(`${apiUrl}/rules/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    rule: description,
                    rule_id: `rule-${Date.now()}`,
                }),
            })

            if (!response.ok) {
                throw new Error(`Failed to create rule: ${response.statusText}`)
            }

            const result = await response.json()
            console.log("Rule created successfully:", result)

            // Update the notices state to mark the rule as created
            const updatedNotices = notices.map(notice =>
                notice.id === selectedNotice.id
                    ? {
                        ...notice,
                        hasRule: true,
                        ruleId: result.result?.rule_id || `rule-${Date.now()}`,
                        ruleName: ruleName,
                        createdDate: new Date().toISOString().split('T')[0]
                    }
                    : notice
            )
            setNotices(updatedNotices)

            setShowCreateModal(false)
            setSelectedNotice(null)
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : "Unknown error occurred"
            setError(errorMessage)
            console.error("Error creating rule:", err)
        } finally {
            setIsSubmitting(false)
        }
    }

    return (
        <div className="flex min-h-screen flex-col bg-background">
            {/* Header */}
            <div className="border-b border-border bg-card px-6 py-4">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight text-foreground">
                            Compliance Rule Management
                        </h1>
                        <p className="mt-1 text-sm text-muted-foreground">
                            Review legal interpretations and create compliance rules for regulatory notices
                        </p>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-auto p-6">
                <div className="space-y-6">
                    {/* Stats Cards */}
                    <div className="grid gap-4 md:grid-cols-3">
                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-muted-foreground">Total Notices</p>
                                        <p className="mt-2 text-3xl font-bold">{notices.length}</p>
                                    </div>
                                    <FileText className="size-8 text-muted-foreground" />
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-muted-foreground">Rules Created</p>
                                        <p className="mt-2 text-3xl font-bold">{withRuleCount}</p>
                                    </div>
                                    <CheckCircle2 className="size-8 text-emerald-500" />
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-muted-foreground">Pending Rules</p>
                                        <p className="mt-2 text-3xl font-bold">{noRuleCount}</p>
                                        {highPriorityNoRule > 0 && (
                                            <p className="mt-1 text-xs text-destructive">
                                                {highPriorityNoRule} high priority
                                            </p>
                                        )}
                                    </div>
                                    <AlertCircle className="size-8 text-destructive" />
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Main Content Grid */}
                    <div className="flex flex-col gap-6 ">
                        {/* Notices List */}
                        <h2 className="mb-4 text-lg font-semibold text-foreground">
                            Notices ({notices.length})
                        </h2>
                        <div className="flex gap-4">
                            <div className="flex flex-col flex-none gap-4">
                                {notices.map((notice) => (
                                    <Card
                                        key={notice.id}
                                        className={`cursor-pointer transition-colors hover:bg-accent/50 ${selectedNotice?.id === notice.id
                                            ? "border-primary ring-2 ring-primary/20"
                                            : ""
                                            }`}
                                        onClick={() => setSelectedNotice(notice)}
                                    >
                                        <CardContent className="pt-4">
                                            <div className="space-y-2">
                                                <div className="flex items-start justify-between gap-2">
                                                    <h3 className="text-xs font-semibold text-foreground line-clamp-2">
                                                        {notice.title}
                                                    </h3>
                                                    {notice.hasRule ? (
                                                        <CheckCircle2 className="size-4 shrink-0 text-emerald-500" />
                                                    ) : (
                                                        <AlertCircle className="size-4 shrink-0 text-destructive" />
                                                    )}
                                                </div>
                                                <p className="text-xs text-muted-foreground">
                                                    {notice.regulator}
                                                </p>
                                                <p className="text-xs text-muted-foreground">
                                                    {notice.category}
                                                </p>
                                                <div className="flex gap-1 pt-1">
                                                    <span
                                                        className={`inline-block rounded px-1.5 py-0.5 text-xs font-medium ${getPriorityColor(
                                                            notice.priority
                                                        )}`}
                                                    >
                                                        {notice.priority}
                                                    </span>
                                                    {notice.hasRule && (
                                                        <span className="inline-block rounded bg-emerald-100 px-1.5 py-0.5 text-xs font-medium text-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-300">
                                                            Rule created
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>

                            {/* Selected Notice Details & Interpretation */}
                            <div className="w-full">
                                {selectedNotice ? (
                                    <div className="flex flex-col gap-4">
                                        <Card>
                                            <CardHeader>
                                                <div className="flex items-start justify-between">
                                                    <div>
                                                        <CardTitle>{selectedNotice.title}</CardTitle>
                                                        <CardDescription className="mt-2">
                                                            {selectedNotice.regulator} • {selectedNotice.category}
                                                        </CardDescription>
                                                    </div>
                                                    {selectedNotice.hasRule ? (
                                                        <CheckCircle2 className="size-6 shrink-0 text-emerald-500" />
                                                    ) : (
                                                        <AlertCircle className="size-6 shrink-0 text-destructive" />
                                                    )}
                                                </div>
                                            </CardHeader>
                                        </Card>

                                        {/* Legal Interpretation */}
                                        <Card>
                                            <CardHeader>
                                                <CardTitle className="text-base">Legal Interpretation</CardTitle>
                                            </CardHeader>
                                            <CardContent>
                                                <p className="text-sm leading-relaxed text-foreground">
                                                    {selectedNotice.legalInterpretation}
                                                </p>
                                            </CardContent>
                                        </Card>

                                        {/* Rule Status */}
                                        {selectedNotice.hasRule ? (
                                            <Card className="border-emerald-200 bg-emerald-50 dark:border-emerald-900/30 dark:bg-emerald-900/10">
                                                <CardHeader>
                                                    <CardTitle className="text-base text-emerald-900 dark:text-emerald-100">
                                                        Rule Already Created
                                                    </CardTitle>
                                                </CardHeader>
                                                <CardContent className="space-y-3">
                                                    <div>
                                                        <p className="text-xs font-medium text-muted-foreground">
                                                            RULE NAME
                                                        </p>
                                                        <p className="mt-1 text-sm font-semibold text-foreground">
                                                            {selectedNotice.ruleName}
                                                        </p>
                                                    </div>
                                                    <div>
                                                        <p className="text-xs font-medium text-muted-foreground">
                                                            CREATED DATE
                                                        </p>
                                                        <p className="mt-1 text-sm text-foreground">
                                                            {new Date(selectedNotice.createdDate!).toLocaleDateString()}
                                                        </p>
                                                    </div>
                                                    <div className="flex gap-2 pt-2">
                                                        <Button variant="outline" size="sm">
                                                            <Eye className="mr-2 size-4" />
                                                            View Rule
                                                        </Button>
                                                        <Button variant="outline" size="sm">
                                                            <LinkIcon className="mr-2 size-4" />
                                                            Edit Rule
                                                        </Button>
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        ) : (
                                            <Card className="border-amber-200 bg-amber-50 dark:border-amber-900/30 dark:bg-amber-900/10">
                                                <CardHeader>
                                                    <CardTitle className="text-base text-amber-900 dark:text-amber-100">
                                                        No Rule Created Yet
                                                    </CardTitle>
                                                    <CardDescription className="text-amber-800/70 dark:text-amber-200/70">
                                                        This notice requires a compliance rule to be created
                                                    </CardDescription>
                                                </CardHeader>
                                                <CardContent className="space-y-4">
                                                    <div className="rounded-lg bg-white/50 dark:bg-black/20 p-3">
                                                        <p className="text-xs font-medium text-muted-foreground">
                                                            ACTION REQUIRED
                                                        </p>
                                                        <p className="mt-2 text-sm text-foreground">
                                                            Use the legal interpretation above to create a compliance rule that
                                                            operationalizes this regulatory requirement.
                                                        </p>
                                                    </div>

                                                    <div className="flex gap-2 pt-2">
                                                        <Button
                                                            onClick={() => handleCreateRule(selectedNotice.id)}
                                                            className="flex-1"
                                                        >
                                                            <Plus className="mr-2 size-4" />
                                                            Create Rule
                                                        </Button>
                                                        <Button variant="outline">
                                                            <Eye className="mr-2 size-4" />
                                                            View Notice
                                                        </Button>
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        )}

                                        {/* Priority Badge */}
                                        <Card>
                                            <CardContent className="pt-6">
                                                <div className="flex items-center justify-between">
                                                    <p className="text-sm font-medium text-muted-foreground">Priority</p>
                                                    <span
                                                        className={`rounded-full px-3 py-1 text-sm font-medium ${getPriorityColor(
                                                            selectedNotice.priority
                                                        )}`}
                                                    >
                                                        {selectedNotice.priority}
                                                    </span>
                                                </div>
                                            </CardContent>
                                        </Card>
                                    </div>
                                ) : (
                                    <Card>
                                        <CardContent className="flex min-h-96 items-center justify-center pt-6">
                                            <div className="text-center">
                                                <FileText className="mx-auto size-12 text-muted-foreground/30" />
                                                <p className="mt-4 text-sm text-muted-foreground">
                                                    Select a notice to view legal interpretation and manage rules
                                                </p>
                                            </div>
                                        </CardContent>
                                    </Card>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Create Rule Modal Overlay */}
            {showCreateModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
                    <Card className="w-full max-w-2xl mx-4">
                        <CardHeader>
                            <CardTitle>Create New Rule</CardTitle>
                            <CardDescription>
                                Define a compliance rule based on the legal interpretation
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {selectedNotice && (
                                <div>
                                    <p className="text-sm font-medium text-muted-foreground">
                                        FOR NOTICE
                                    </p>
                                    <p className="mt-1 text-sm font-semibold text-foreground">
                                        {selectedNotice.title}
                                    </p>
                                </div>
                            )}

                            {error && (
                                <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                                    {error}
                                </div>
                            )}

                            <form onSubmit={handleSubmitRule} className="space-y-4">
                                <div>
                                    <label htmlFor="ruleName" className="block text-sm font-medium text-foreground">
                                        Rule Name *
                                    </label>
                                    <input
                                        id="ruleName"
                                        name="ruleName"
                                        type="text"
                                        placeholder="Enter rule name"
                                        required
                                        disabled={isSubmitting}
                                        className="mt-1 block w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground placeholder-muted-foreground disabled:opacity-50"
                                    />
                                </div>

                                <div>
                                    <label htmlFor="description" className="block text-sm font-medium text-foreground">
                                        Description *
                                    </label>
                                    <textarea
                                        id="description"
                                        name="description"
                                        placeholder="Describe the rule and how it addresses the regulatory requirement"
                                        rows={4}
                                        required
                                        disabled={isSubmitting}
                                        className="mt-1 block w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground placeholder-muted-foreground disabled:opacity-50"
                                    />
                                </div>

                                <div className="flex gap-2 justify-end pt-4">
                                    <Button
                                        type="button"
                                        variant="outline"
                                        onClick={() => {
                                            setShowCreateModal(false)
                                            setError(null)
                                        }}
                                        disabled={isSubmitting}
                                    >
                                        Cancel
                                    </Button>
                                    <Button
                                        type="submit"
                                        disabled={isSubmitting}
                                    >
                                        {isSubmitting ? "Creating..." : "Create Rule"}
                                    </Button>
                                </div>
                            </form>
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    )
}

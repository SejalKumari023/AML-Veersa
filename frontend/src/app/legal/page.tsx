"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { AlertCircle, CheckCircle2, Clock, FileText, Download, ArrowRight, Link as LinkIcon } from "lucide-react"
import Link from "next/link"
import { getUser } from "~/lib/auth"
import {
    Card,
    CardHeader,
    CardTitle,
    CardDescription,
    CardContent,
} from "~/components/ui/card"
import { Button } from "~/components/ui/button"

interface Notice {
    id: string
    title: string
    regulator: string
    dateReceived: string
    category: string
    status: "pending" | "reviewed" | "action-required" | "archived"
    description?: string
    assignedTo?: string
    dueDate?: string
    priority: "high" | "medium" | "low"
}

interface Action {
    id: string
    noticeId: string
    description: string
    assignedTo: string
    dueDate: string
    priority: "high" | "medium" | "low"
    status: "open" | "in-progress" | "completed"
}

export default function LegalPage() {
    const router = useRouter()

    useEffect(() => {
        if (!getUser()) router.replace("/auth/login")
    }, [router])

    const [notices, setNotices] = useState<Notice[]>([
        {
            id: "1",
            title: "Regulatory Update on AML Compliance",
            regulator: "Financial Conduct Authority",
            dateReceived: "2025-11-01",
            category: "AML/KYC",
            status: "action-required",
            description: "New requirements for customer verification procedures",
            assignedTo: "Sarah Johnson",
            dueDate: "2025-11-15",
            priority: "high",
        },
        {
            id: "2",
            title: "Data Protection Notice",
            regulator: "Information Commissioner's Office",
            dateReceived: "2025-10-28",
            category: "Data Privacy",
            status: "reviewed",
            description: "Updates to personal data retention policies",
            assignedTo: "Michael Chen",
            dueDate: "2025-11-10",
            priority: "medium",
        },
        {
            id: "3",
            title: "Market Abuse Regulation Update",
            regulator: "European Securities and Markets Authority",
            dateReceived: "2025-10-15",
            category: "Market Conduct",
            status: "pending",
            description: "Clarification on market abuse detection requirements",
            priority: "low",
        },
    ])

    const [actions, setActions] = useState<Action[]>([
        {
            id: "a1",
            noticeId: "1",
            description: "Update customer verification procedures in KYC process",
            assignedTo: "Sarah Johnson",
            dueDate: "2025-11-15",
            priority: "high",
            status: "in-progress",
        },
        {
            id: "a2",
            noticeId: "1",
            description: "Brief compliance team on new AML requirements",
            assignedTo: "David Wong",
            dueDate: "2025-11-10",
            priority: "high",
            status: "open",
        },
        {
            id: "a3",
            noticeId: "2",
            description: "Review and update data retention policy",
            assignedTo: "Michael Chen",
            dueDate: "2025-11-10",
            priority: "medium",
            status: "open",
        },
    ])

    const [selectedNotice, setSelectedNotice] = useState<Notice | null>(null)

    const getStatusBadgeColor = (status: Notice["status"]) => {
        switch (status) {
            case "action-required":
                return "bg-destructive text-white"
            case "reviewed":
                return "bg-emerald-500 text-white"
            case "pending":
                return "bg-amber-500 text-white"
            case "archived":
                return "bg-muted text-muted-foreground"
            default:
                return "bg-primary text-primary-foreground"
        }
    }

    const getStatusIcon = (status: Notice["status"]) => {
        switch (status) {
            case "action-required":
                return <AlertCircle className="size-4" />
            case "reviewed":
                return <CheckCircle2 className="size-4" />
            case "pending":
                return <Clock className="size-4" />
            case "archived":
                return <FileText className="size-4" />
            default:
                return <FileText className="size-4" />
        }
    }

    const getActionStatusColor = (status: Action["status"]) => {
        switch (status) {
            case "open":
                return "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300"
            case "in-progress":
                return "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300"
            case "completed":
                return "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300"
            default:
                return "bg-muted text-muted-foreground"
        }
    }

    const getPriorityColor = (priority: Action["priority"]) => {
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

    const handleActionStatusChange = (actionId: string, newStatus: Action["status"]) => {
        setActions(
            actions.map((action) =>
                action.id === actionId ? { ...action, status: newStatus } : action
            )
        )
    }

    const noticeActionRequiredCount = notices.filter((n) => n.status === "action-required").length
    const openActionsCount = actions.filter((a) => a.status === "open").length
    const inProgressCount = actions.filter((a) => a.status === "in-progress").length
    const completedActionsCount = actions.filter((a) => a.status === "completed").length

    const noticeActions = actions.filter((a) => a.noticeId === selectedNotice?.id)

    return (
        <div className="flex min-h-screen flex-col bg-background">
            {/* Header */}
            <div className="border-b border-border bg-card px-6 py-4">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight text-foreground">
                            Legal Actions
                        </h1>
                        <p className="mt-1 text-sm text-muted-foreground">
                            Manage compliance actions on regulatory notices
                        </p>
                    </div>
                    <Link href="/legal/ingest">
                        <Button>
                            <LinkIcon className="mr-2 size-4" />
                            Ingest Documents
                        </Button>
                    </Link>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-auto p-6">
                <div className="space-y-6">
                    {/* Stats Cards */}
                    <div className="grid gap-4 md:grid-cols-4">
                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-muted-foreground">Notices Requiring Action</p>
                                        <p className="mt-2 text-3xl font-bold">{noticeActionRequiredCount}</p>
                                    </div>
                                    <AlertCircle className="size-8 text-destructive" />
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-muted-foreground">Open Actions</p>
                                        <p className="mt-2 text-3xl font-bold">{openActionsCount}</p>
                                    </div>
                                    <Clock className="size-8 text-amber-500" />
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-muted-foreground">In Progress</p>
                                        <p className="mt-2 text-3xl font-bold">{inProgressCount}</p>
                                    </div>
                                    <Clock className="size-8 text-blue-500" />
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-muted-foreground">Completed</p>
                                        <p className="mt-2 text-3xl font-bold">{completedActionsCount}</p>
                                    </div>
                                    <CheckCircle2 className="size-8 text-emerald-500" />
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    <div className="grid gap-6 md:grid-cols-3">
                        {/* Notices List */}
                        <div className="md:col-span-1">
                            <h2 className="mb-4 text-lg font-semibold text-foreground">
                                Notices ({notices.length})
                            </h2>

                            <div className="space-y-2">
                                {notices.map((notice) => (
                                    <Card
                                        key={notice.id}
                                        className={`cursor-pointer transition-colors hover:bg-accent/50 ${selectedNotice?.id === notice.id ? "border-primary ring-2 ring-primary/20" : ""
                                            }`}
                                        onClick={() => setSelectedNotice(notice)}
                                    >
                                        <CardContent className="pt-4">
                                            <div className="space-y-2">
                                                <div className="flex items-start justify-between gap-2">
                                                    <h3 className="text-xs font-semibold text-foreground line-clamp-2">
                                                        {notice.title}
                                                    </h3>
                                                    <span
                                                        className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium shrink-0 ${getStatusBadgeColor(
                                                            notice.status
                                                        )}`}
                                                    >
                                                        {getStatusIcon(notice.status)}
                                                    </span>
                                                </div>
                                                <p className="text-xs text-muted-foreground">
                                                    {notice.regulator}
                                                </p>
                                                <p className="text-xs text-muted-foreground">
                                                    {new Date(notice.dateReceived).toLocaleDateString()}
                                                </p>
                                            </div>
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>
                        </div>

                        {/* Actions List */}
                        <div className="md:col-span-2">
                            <h2 className="mb-4 text-lg font-semibold text-foreground">
                                All Actions ({actions.length})
                            </h2>

                            <div className="space-y-3">
                                {actions.length > 0 ? (
                                    actions.map((action) => {
                                        const notice = notices.find((n) => n.id === action.noticeId)
                                        return (
                                            <Card key={action.id}>
                                                <CardContent className="pt-4">
                                                    <div className="space-y-3">
                                                        <div>
                                                            <div className="flex items-start justify-between gap-2">
                                                                <div className="flex-1">
                                                                    <p className="text-sm font-semibold text-foreground">
                                                                        {action.description}
                                                                    </p>
                                                                    <p className="mt-1 text-xs text-muted-foreground">
                                                                        From: {notice?.title}
                                                                    </p>
                                                                </div>
                                                                <span
                                                                    className={`inline-flex rounded px-2 py-1 text-xs font-medium shrink-0 ${getActionStatusColor(
                                                                        action.status
                                                                    )}`}
                                                                >
                                                                    {action.status}
                                                                </span>
                                                            </div>
                                                        </div>

                                                        <div className="grid grid-cols-2 gap-2 text-xs">
                                                            <div>
                                                                <p className="text-muted-foreground">Assigned to</p>
                                                                <p className="font-medium text-foreground">
                                                                    {action.assignedTo}
                                                                </p>
                                                            </div>
                                                            <div>
                                                                <p className="text-muted-foreground">Due</p>
                                                                <p className="font-medium text-foreground">
                                                                    {new Date(action.dueDate).toLocaleDateString()}
                                                                </p>
                                                            </div>
                                                        </div>

                                                        <div className="flex flex-wrap gap-2">
                                                            {(["open", "in-progress", "completed"] as const).map(
                                                                (status) => (
                                                                    <Button
                                                                        key={status}
                                                                        variant={action.status === status ? "default" : "outline"}
                                                                        size="sm"
                                                                        className="text-xs"
                                                                        onClick={() =>
                                                                            handleActionStatusChange(action.id, status)
                                                                        }
                                                                    >
                                                                        {status.replace("-", " ")}
                                                                    </Button>
                                                                )
                                                            )}
                                                            <span
                                                                className={`inline-flex items-center rounded px-2 py-1 text-xs font-medium ${getPriorityColor(
                                                                    action.priority
                                                                )} ml-auto`}
                                                            >
                                                                {action.priority}
                                                            </span>
                                                        </div>
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        )
                                    })
                                ) : (
                                    <Card>
                                        <CardContent className="pt-6">
                                            <p className="text-center text-sm text-muted-foreground">
                                                No actions to display
                                            </p>
                                        </CardContent>
                                    </Card>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Detail Panel */}
            {selectedNotice && (
                <div className="border-t border-border bg-card p-6">
                    <div className="max-w-4xl">
                        <div className="mb-6 flex items-start justify-between">
                            <div>
                                <h3 className="text-xl font-semibold text-foreground">
                                    {selectedNotice.title}
                                </h3>
                                <p className="mt-1 text-sm text-muted-foreground">
                                    {selectedNotice.description}
                                </p>
                            </div>
                            <span
                                className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm font-medium ${getStatusBadgeColor(
                                    selectedNotice.status
                                )}`}
                            >
                                {getStatusIcon(selectedNotice.status)}
                                {selectedNotice.status.replace("-", " ")}
                            </span>
                        </div>

                        <div className="grid gap-4 md:grid-cols-3 mb-6 text-sm">
                            <div>
                                <p className="text-xs font-medium text-muted-foreground">REGULATOR</p>
                                <p className="mt-1 font-medium text-foreground">{selectedNotice.regulator}</p>
                            </div>
                            <div>
                                <p className="text-xs font-medium text-muted-foreground">CATEGORY</p>
                                <p className="mt-1 font-medium text-foreground">{selectedNotice.category}</p>
                            </div>
                            <div>
                                <p className="text-xs font-medium text-muted-foreground">DATE RECEIVED</p>
                                <p className="mt-1 font-medium text-foreground">
                                    {new Date(selectedNotice.dateReceived).toLocaleDateString()}
                                </p>
                            </div>
                            {selectedNotice.assignedTo && (
                                <div>
                                    <p className="text-xs font-medium text-muted-foreground">ASSIGNED TO</p>
                                    <p className="mt-1 font-medium text-foreground">{selectedNotice.assignedTo}</p>
                                </div>
                            )}
                            {selectedNotice.dueDate && (
                                <div>
                                    <p className="text-xs font-medium text-muted-foreground">DUE DATE</p>
                                    <p className="mt-1 font-medium text-foreground">
                                        {new Date(selectedNotice.dueDate).toLocaleDateString()}
                                    </p>
                                </div>
                            )}
                        </div>

                        {noticeActions.length > 0 && (
                            <div className="bg-muted/30 rounded-lg p-4 mb-4">
                                <h4 className="text-sm font-semibold text-foreground mb-3">
                                    Related Actions ({noticeActions.length})
                                </h4>
                                <div className="space-y-2">
                                    {noticeActions.map((action) => (
                                        <div key={action.id} className="text-xs text-foreground">
                                            <span className={`inline-block rounded px-2 py-0.5 mr-2 ${getActionStatusColor(action.status)}`}>
                                                {action.status}
                                            </span>
                                            {action.description} • Due: {new Date(action.dueDate).toLocaleDateString()}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        <div className="flex gap-2">
                            <Button variant="outline" size="sm">
                                <Download className="mr-2 size-4" />
                                Download Document
                            </Button>
                            <Link href="/legal/ingest">
                                <Button variant="outline" size="sm">
                                    <ArrowRight className="mr-2 size-4" />
                                    View Original Upload
                                </Button>
                            </Link>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

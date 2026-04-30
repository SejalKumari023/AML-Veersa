"use client"

import { useState } from "react"
import {
    AlertCircle,
    CheckCircle2,
    Play,
    FileText,
    TrendingUp,
    Users,
    DollarSign,
} from "lucide-react"
import Link from "next/link"
import {
    Card,
    CardHeader,
    CardTitle,
    CardDescription,
    CardContent,
} from "~/components/ui/card"
import { Button } from "~/components/ui/button"

interface Transaction {
    id: string
    transactionId: string
    amount: number
    currency: string
    originator: string
    beneficiary: string
    channel: string
    timestamp: string
    status: "pending" | "flagged" | "cleared" | "escalated"
    riskScore: number
    flags: string[]
}

interface Rule {
    id: string
    name: string
    category: string
    description: string
    status: "active" | "draft"
}

export default function ComplianceTransactionsPage() {
    const [transactions, setTransactions] = useState<Transaction[]>([
        {
            id: "t1",
            transactionId: "TXN-2025-001",
            amount: 150000,
            currency: "USD",
            originator: "Acme Corp",
            beneficiary: "Global Trading LLC",
            channel: "SWIFT",
            timestamp: "2025-11-02T14:30:00Z",
            status: "flagged",
            riskScore: 78,
            flags: ["high_amount", "high_risk_jurisdiction"],
        },
        {
            id: "t2",
            transactionId: "TXN-2025-002",
            amount: 45000,
            currency: "EUR",
            originator: "Tech Solutions Inc",
            beneficiary: "EU Partners GmbH",
            channel: "Wire",
            timestamp: "2025-11-02T13:15:00Z",
            status: "cleared",
            riskScore: 25,
            flags: [],
        },
        {
            id: "t3",
            transactionId: "TXN-2025-003",
            amount: 250000,
            currency: "GBP",
            originator: "Unknown Entity",
            beneficiary: "Finance Corp",
            channel: "SWIFT",
            timestamp: "2025-11-02T12:00:00Z",
            status: "escalated",
            riskScore: 92,
            flags: ["pep_involved", "high_amount", "sanctions_concern"],
        },
        {
            id: "t4",
            transactionId: "TXN-2025-004",
            amount: 75000,
            currency: "USD",
            originator: "Import Export Ltd",
            beneficiary: "Middle East Trading",
            channel: "Wire",
            timestamp: "2025-11-02T10:45:00Z",
            status: "pending",
            riskScore: 55,
            flags: ["high_risk_jurisdiction"],
        },
        {
            id: "t5",
            transactionId: "TXN-2025-005",
            amount: 30000,
            currency: "USD",
            originator: "Local Business",
            beneficiary: "Vendor Account",
            channel: "ACH",
            timestamp: "2025-11-02T09:20:00Z",
            status: "cleared",
            riskScore: 15,
            flags: [],
        },
        {
            id: "t6",
            transactionId: "TXN-2025-006",
            amount: 500000,
            currency: "USD",
            originator: "Structured Fund",
            beneficiary: "Investment Corp",
            channel: "SWIFT",
            timestamp: "2025-11-01T16:00:00Z",
            status: "flagged",
            riskScore: 85,
            flags: ["very_high_amount", "structured_product"],
        },
    ])

    const [rules] = useState<Rule[]>([
        {
            id: "r1",
            name: "Enhanced AML Customer Verification",
            category: "AML/KYC",
            description: "Verify customer identity with facial recognition for high-risk jurisdictions",
            status: "active",
        },
        {
            id: "r2",
            name: "Interest Rate Benchmark Validation",
            category: "Market Conduct",
            description: "Validate interest rate submissions against independent market data",
            status: "active",
        },
        {
            id: "r3",
            name: "Transaction Monitoring for Suspicious Patterns",
            category: "Market Conduct",
            description: "Monitor for suspicious transaction patterns and alert within 4 hours",
            status: "active",
        },
    ])

    const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null)
    const [showRunRuleModal, setShowRunRuleModal] = useState(false)
    const [selectedRule, setSelectedRule] = useState<Rule | null>(null)
    const [ruleResult, setRuleResult] = useState<{
        passed: boolean
        message: string
        details: string
    } | null>(null)

    const getStatusColor = (status: Transaction["status"]) => {
        switch (status) {
            case "cleared":
                return "text-emerald-600 bg-emerald-100 dark:bg-emerald-900/20"
            case "flagged":
                return "text-amber-600 bg-amber-100 dark:bg-amber-900/20"
            case "escalated":
                return "text-destructive bg-destructive/10"
            case "pending":
                return "text-blue-600 bg-blue-100 dark:bg-blue-900/20"
            default:
                return "text-muted-foreground"
        }
    }

    const getRiskColor = (riskScore: number) => {
        if (riskScore >= 80) return "text-destructive"
        if (riskScore >= 60) return "text-amber-600"
        if (riskScore >= 40) return "text-blue-600"
        return "text-emerald-600"
    }

    const handleRunRule = (rule: Rule) => {
        setSelectedRule(rule)
        // Simulate rule execution
        const passed = Math.random() > 0.3 // 70% pass rate for demo
        setRuleResult({
            passed,
            message: passed ? "Rule validation passed" : "Rule validation failed",
            details: passed
                ? `Transaction ${selectedTransaction?.transactionId} meets all requirements for ${rule.name}`
                : `Transaction ${selectedTransaction?.transactionId} fails validation: ${rule.description}`,
        })
    }

    const flaggedCount = transactions.filter((t) => t.status === "flagged").length
    const escalatedCount = transactions.filter((t) => t.status === "escalated").length
    const highRiskCount = transactions.filter((t) => t.riskScore >= 60).length

    return (
        <div className="flex min-h-screen flex-col bg-background">
            {/* Header */}
            <div className="border-b border-border bg-card px-6 py-4">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight text-foreground">
                            Transaction Monitoring
                        </h1>
                        <p className="mt-1 text-sm text-muted-foreground">
                            Review transactions and run compliance rules
                        </p>
                    </div>
                    <Link href="/compliance">
                        <Button variant="outline">Back to Rules</Button>
                    </Link>
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
                                        <p className="text-sm text-muted-foreground">Total Transactions</p>
                                        <p className="mt-2 text-3xl font-bold">{transactions.length}</p>
                                    </div>
                                    <FileText className="size-8 text-muted-foreground" />
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-muted-foreground">Flagged</p>
                                        <p className="mt-2 text-3xl font-bold">{flaggedCount}</p>
                                    </div>
                                    <AlertCircle className="size-8 text-amber-500" />
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-muted-foreground">Escalated</p>
                                        <p className="mt-2 text-3xl font-bold">{escalatedCount}</p>
                                    </div>
                                    <AlertCircle className="size-8 text-destructive" />
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-muted-foreground">High Risk</p>
                                        <p className="mt-2 text-3xl font-bold">{highRiskCount}</p>
                                    </div>
                                    <TrendingUp className="size-8 text-destructive" />
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Main Content Grid */}
                    <div className="flex flex-col gap-6">
                        {/* Transactions List Sidebar */}
                        <h2 className="mb-4 text-lg font-semibold text-foreground">
                            Transactions ({transactions.length})
                        </h2>
                        <div className="flex gap-4">
                            <div className="flex flex-col gap-3 max-h-[calc(100vh-300px)] overflow-y-auto pr-2">
                                {transactions.map((transaction) => (
                                    <Card
                                        key={transaction.id}
                                        className={`cursor-pointer transition-colors hover:bg-accent/50 ${selectedTransaction?.id === transaction.id
                                            ? "border-primary ring-2 ring-primary/20"
                                            : ""
                                            }`}
                                        onClick={() => setSelectedTransaction(transaction)}
                                    >
                                        <CardContent className="pt-4">
                                            <div className="space-y-2">
                                                <div className="flex items-start justify-between gap-2">
                                                    <h3 className="text-xs font-semibold text-foreground">
                                                        {transaction.transactionId}
                                                    </h3>
                                                    <span
                                                        className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${getStatusColor(
                                                            transaction.status
                                                        )}`}
                                                    >
                                                        {transaction.status}
                                                    </span>
                                                </div>
                                                <div className="flex items-center justify-between">
                                                    <p className="text-xs font-semibold text-foreground">
                                                        {transaction.amount.toLocaleString()} {transaction.currency}
                                                    </p>
                                                    <span className={`text-xs font-bold ${getRiskColor(transaction.riskScore)}`}>
                                                        {transaction.riskScore}
                                                    </span>
                                                </div>
                                                <p className="text-xs text-muted-foreground line-clamp-1">
                                                    {transaction.originator}
                                                </p>
                                                <p className="text-xs text-muted-foreground line-clamp-1">
                                                    → {transaction.beneficiary}
                                                </p>
                                                {transaction.flags.length > 0 && (
                                                    <div className="flex flex-wrap gap-1 pt-1">
                                                        {transaction.flags.slice(0, 2).map((flag) => (
                                                            <span
                                                                key={flag}
                                                                className="inline-block rounded bg-red-100/50 px-1.5 py-0.5 text-xs text-red-700 dark:bg-red-900/20 dark:text-red-300"
                                                            >
                                                                {flag}
                                                            </span>
                                                        ))}
                                                        {transaction.flags.length > 2 && (
                                                            <span className="inline-block rounded bg-red-100/50 px-1.5 py-0.5 text-xs text-red-700 dark:bg-red-900/20 dark:text-red-300">
                                                                +{transaction.flags.length - 2}
                                                            </span>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>

                            {/* Transaction Details & Rule Execution */}
                            <div className="w-full">
                                {selectedTransaction ? (
                                    <div className="flex flex-col gap-4">
                                        {/* Transaction Header */}
                                        <Card>
                                            <CardHeader>
                                                <div className="flex items-start justify-between">
                                                    <div>
                                                        <CardTitle>{selectedTransaction.transactionId}</CardTitle>
                                                        <CardDescription className="mt-2">
                                                            {new Date(selectedTransaction.timestamp).toLocaleString()}
                                                        </CardDescription>
                                                    </div>
                                                    <span
                                                        className={`rounded-full px-3 py-1 text-sm font-medium ${getStatusColor(
                                                            selectedTransaction.status
                                                        )}`}
                                                    >
                                                        {selectedTransaction.status}
                                                    </span>
                                                </div>
                                            </CardHeader>
                                        </Card>

                                        {/* Transaction Details */}
                                        <Card>
                                            <CardHeader>
                                                <CardTitle className="text-base">Transaction Details</CardTitle>
                                            </CardHeader>
                                            <CardContent className="space-y-4">
                                                <div className="grid gap-4 md:grid-cols-2">
                                                    <div>
                                                        <p className="text-xs font-medium text-muted-foreground">AMOUNT</p>
                                                        <p className="mt-1 text-lg font-bold text-foreground">
                                                            {selectedTransaction.amount.toLocaleString()} {selectedTransaction.currency}
                                                        </p>
                                                    </div>
                                                    <div>
                                                        <p className="text-xs font-medium text-muted-foreground">RISK SCORE</p>
                                                        <p className={`mt-1 text-lg font-bold ${getRiskColor(selectedTransaction.riskScore)}`}>
                                                            {selectedTransaction.riskScore}%
                                                        </p>
                                                    </div>
                                                    <div>
                                                        <p className="text-xs font-medium text-muted-foreground">CHANNEL</p>
                                                        <p className="mt-1 text-sm text-foreground">{selectedTransaction.channel}</p>
                                                    </div>
                                                    <div>
                                                        <p className="text-xs font-medium text-muted-foreground">ORIGINATOR</p>
                                                        <p className="mt-1 text-sm text-foreground">{selectedTransaction.originator}</p>
                                                    </div>
                                                    <div>
                                                        <p className="text-xs font-medium text-muted-foreground">BENEFICIARY</p>
                                                        <p className="mt-1 text-sm text-foreground">{selectedTransaction.beneficiary}</p>
                                                    </div>
                                                </div>

                                                {selectedTransaction.flags.length > 0 && (
                                                    <div className="space-y-2 border-t pt-4">
                                                        <p className="text-xs font-medium text-muted-foreground">FLAGS</p>
                                                        <div className="flex flex-wrap gap-2">
                                                            {selectedTransaction.flags.map((flag) => (
                                                                <span
                                                                    key={flag}
                                                                    className="inline-block rounded bg-red-100 px-2.5 py-1 text-xs font-medium text-red-800 dark:bg-red-900/30 dark:text-red-300"
                                                                >
                                                                    {flag}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </CardContent>
                                        </Card>

                                        {/* Run Rules Section */}
                                        <Card>
                                            <CardHeader>
                                                <CardTitle className="text-base">Run Compliance Rules</CardTitle>
                                                <CardDescription>
                                                    Execute active rules against this transaction
                                                </CardDescription>
                                            </CardHeader>
                                            <CardContent>
                                                <div className="space-y-3">
                                                    {rules.filter((r) => r.status === "active").map((rule) => (
                                                        <div
                                                            key={rule.id}
                                                            className="flex items-start justify-between rounded-lg border p-3"
                                                        >
                                                            <div className="flex-1">
                                                                <p className="text-sm font-semibold text-foreground">{rule.name}</p>
                                                                <p className="text-xs text-muted-foreground">{rule.description}</p>
                                                            </div>
                                                            <Button
                                                                size="sm"
                                                                onClick={() => handleRunRule(rule)}
                                                                className="ml-2 shrink-0"
                                                            >
                                                                <Play className="mr-1 size-3" />
                                                                Run
                                                            </Button>
                                                        </div>
                                                    ))}
                                                </div>
                                            </CardContent>
                                        </Card>

                                        {/* Rule Execution Result */}
                                        {ruleResult && (
                                            <Card
                                                className={`border-l-4 ${ruleResult.passed
                                                    ? "border-l-emerald-500 bg-emerald-50 dark:bg-emerald-900/10"
                                                    : "border-l-destructive bg-destructive/5"
                                                    }`}
                                            >
                                                <CardHeader>
                                                    <div className="flex items-start justify-between">
                                                        <div>
                                                            <CardTitle className="text-base">{selectedRule?.name}</CardTitle>
                                                            <CardDescription className="mt-1">{ruleResult.message}</CardDescription>
                                                        </div>
                                                        {ruleResult.passed ? (
                                                            <CheckCircle2 className="size-6 shrink-0 text-emerald-600" />
                                                        ) : (
                                                            <AlertCircle className="size-6 shrink-0 text-destructive" />
                                                        )}
                                                    </div>
                                                </CardHeader>
                                                <CardContent>
                                                    <p className="text-sm text-foreground">{ruleResult.details}</p>
                                                </CardContent>
                                            </Card>
                                        )}
                                    </div>
                                ) : (
                                    <Card>
                                        <CardContent className="flex min-h-96 items-center justify-center pt-6">
                                            <div className="text-center">
                                                <FileText className="mx-auto size-12 text-muted-foreground/30" />
                                                <p className="mt-4 text-sm text-muted-foreground">
                                                    Select a transaction to view details and run rules
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
        </div>
    )
}

"use client"
import { useState, useEffect } from "react"
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
    transaction_id: string
    booking_jurisdiction: string
    regulator: string
    booking_datetime: string
    value_date: string
    amount: number
    currency: string
    channel: string
    product_type: string
    originator_name: string
    originator_account: string
    originator_country: string
    beneficiary_name: string
    beneficiary_account: string
    beneficiary_country: string
    swift_mt: string | null
    ordering_institution_bic: string | null
    beneficiary_institution_bic: string | null
    swift_f50_present: boolean
    swift_f59_present: boolean
    swift_f70_purpose: string | null
    swift_f71_charges: string | null
    travel_rule_complete: boolean
    fx_indicator: boolean
    fx_base_ccy: string
    fx_quote_ccy: string
    fx_applied_rate: number
    fx_market_rate: number
    fx_spread_bps: number
    fx_counterparty: string
    customer_id: string
    customer_type: string
    customer_risk_rating: string
    customer_is_pep: boolean
    kyc_last_completed: string
    kyc_due_date: string
    edd_required: boolean
    edd_performed: boolean
    sow_documented: boolean
    purpose_code: string
    narrative: string
    is_advised: boolean
    product_complex: boolean
    client_risk_profile: string
    suitability_assessed: boolean
    suitability_result: string
    product_has_va_exposure: boolean
    va_disclosure_provided: boolean
    cash_id_verified: boolean
    daily_cash_total_customer: number
    daily_cash_txn_count: number
    sanctions_screening: string
    suspicion_determined_datetime: string | null
    str_filed_datetime: string | null
    timestamp: string
    status: "pending" | "flagged" | "cleared" | "escalated"
    risk_score: number | null
    flags: string[]
}

interface Rule {
    id: string
    name?: string
    rule_text: string
    function_code: string
    explanation: string
    attributes_used: string[]
    status?: "active" | "draft"
    created_at: string
}

interface TriggeredRule {
    rule_id: string
    rule_text: string
    alert_id: string
}

interface RuleExecutionResult {
    message: string
    transaction_id: string
    rules_processed: number
    total_rules: number
    alerts_created: number
    triggered_rules: TriggeredRule[]
}

export default function ComplianceTransactionsPage() {
    const [transactions, setTransactions] = useState<Transaction[]>([])
    const [rules, setRules] = useState<Rule[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [rulesLoading, setRulesLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [rulesError, setRulesError] = useState<string | null>(null)

    // Fetch transactions from API
    useEffect(() => {
        const fetchTransactions = async () => {
            setIsLoading(true)
            setError(null)
            try {
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || "/api"
                const response = await fetch(`${apiUrl}/data/transactions?limit=100`, {
                    method: "GET",
                    headers: {
                        "Content-Type": "application/json",
                    },
                })

                if (!response.ok) {
                    throw new Error(`Failed to fetch transactions: ${response.statusText}`)
                }

                const data: Transaction[] = await response.json()
                setTransactions(data)
            } catch (err) {
                const errorMessage = err instanceof Error ? err.message : "Unknown error occurred"
                setError(errorMessage)
                console.error("Error fetching transactions:", err)
                // Keep page functional with empty state
                setTransactions([])
            } finally {
                setIsLoading(false)
            }
        }

        fetchTransactions()
    }, [])

    // Fetch rules from API
    useEffect(() => {
        const fetchRules = async () => {
            setRulesLoading(true)
            setRulesError(null)
            try {
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || "/api"
                const response = await fetch(`${apiUrl}/rules/`, {
                    method: "GET",
                    headers: {
                        "Content-Type": "application/json",
                    },
                })

                if (!response.ok) {
                    throw new Error(`Failed to fetch rules: ${response.statusText}`)
                }

                const data = await response.json()
                // Handle both array and object with "rules" property
                const rulesList = Array.isArray(data) ? data : data.rules || []
                setRules(rulesList)
            } catch (err) {
                const errorMessage = err instanceof Error ? err.message : "Unknown error occurred"
                setRulesError(errorMessage)
                console.error("Error fetching rules:", err)
                // Keep page functional with empty state
                setRules([])
            } finally {
                setRulesLoading(false)
            }
        }

        fetchRules()
    }, [])

    const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null)
    const [showRunRuleModal, setShowRunRuleModal] = useState(false)
    const [selectedRule, setSelectedRule] = useState<Rule | null>(null)
    const [ruleResult, setRuleResult] = useState<RuleExecutionResult | null>(null)
    const [ruleExecutionLoading, setRuleExecutionLoading] = useState(false)
    const [ruleExecutionError, setRuleExecutionError] = useState<string | null>(null)

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

    const getRiskColor = (riskScore: number | null) => {
        if (!riskScore) return "text-muted-foreground"
        if (riskScore >= 80) return "text-destructive"
        if (riskScore >= 60) return "text-amber-600"
        if (riskScore >= 40) return "text-blue-600"
        return "text-emerald-600"
    }

    const handleRunRule = async (rule: Rule) => {
        if (!selectedTransaction) return

        setSelectedRule(rule)
        setRuleExecutionLoading(true)
        setRuleExecutionError(null)

        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || "/api"
            const response = await fetch(
                `${apiUrl}/data/run-rule/${selectedTransaction.transaction_id}/${rule.id}`,
                {
                    method: "GET",
                    headers: {
                        "Content-Type": "application/json",
                    },
                }
            )

            if (!response.ok) {
                throw new Error(`Failed to execute rule: ${response.statusText}`)
            }

            const result: RuleExecutionResult = await response.json()
            setRuleResult(result)
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : "Unknown error occurred"
            setRuleExecutionError(errorMessage)
            console.error("Error executing rule:", err)
        } finally {
            setRuleExecutionLoading(false)
        }
    }

    const flaggedCount = transactions.filter((t) => t.status === "flagged").length
    const escalatedCount = transactions.filter((t) => t.status === "escalated").length
    const highRiskCount = transactions.filter((t) => t.risk_score !== null && t.risk_score >= 60).length

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
                    {/* Error Alert */}
                    {error && (
                        <Card className="border-destructive/50 bg-destructive/5">
                            <CardContent className="pt-6">
                                <div className="flex items-start gap-3">
                                    <AlertCircle className="size-5 shrink-0 text-destructive mt-0.5" />
                                    <div>
                                        <p className="font-semibold text-destructive">Failed to load transactions</p>
                                        <p className="text-sm text-destructive/80">{error}</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {/* Loading State */}
                    {isLoading ? (
                        <Card>
                            <CardContent className="flex min-h-96 items-center justify-center pt-6">
                                <div className="text-center">
                                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                                    <p className="mt-4 text-sm text-muted-foreground">Loading transactions...</p>
                                </div>
                            </CardContent>
                        </Card>
                    ) : (
                        <>
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
                                    <div className="flex flex-col gap-3 overflow-y-auto pr-2">
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
                                                                {transaction.transaction_id}
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
                                                            <span className={`text-xs font-bold ${getRiskColor(transaction.risk_score)}`}>
                                                                {transaction.risk_score ?? 'N/A'}
                                                            </span>
                                                        </div>
                                                        <p className="text-xs text-muted-foreground line-clamp-1">
                                                            {transaction.originator_name}
                                                        </p>
                                                        <p className="text-xs text-muted-foreground line-clamp-1">
                                                            → {transaction.beneficiary_name}
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
                                                                <CardTitle>{selectedTransaction.transaction_id}</CardTitle>
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
                                                    <CardContent className="space-y-6">
                                                        {/* Basic Transaction Info */}
                                                        <div className="space-y-3 border-b pb-4">
                                                            <p className="text-xs font-medium text-muted-foreground uppercase">Transaction Information</p>
                                                            <div className="grid gap-4 md:grid-cols-2">
                                                                <div>
                                                                    <p className="text-xs font-medium text-muted-foreground">AMOUNT</p>
                                                                    <p className="mt-1 text-lg font-bold text-foreground">
                                                                        {selectedTransaction.amount.toLocaleString()} {selectedTransaction.currency}
                                                                    </p>
                                                                </div>
                                                                <div>
                                                                    <p className="text-xs font-medium text-muted-foreground">RISK SCORE</p>
                                                                    <p className={`mt-1 text-lg font-bold ${getRiskColor(selectedTransaction.risk_score)}`}>
                                                                        {selectedTransaction.risk_score ? `${selectedTransaction.risk_score}%` : 'N/A'}
                                                                    </p>
                                                                </div>
                                                                <div>
                                                                    <p className="text-xs font-medium text-muted-foreground">CHANNEL</p>
                                                                    <p className="mt-1 text-sm text-foreground">{selectedTransaction.channel}</p>
                                                                </div>
                                                                <div>
                                                                    <p className="text-xs font-medium text-muted-foreground">PRODUCT TYPE</p>
                                                                    <p className="mt-1 text-sm text-foreground">{selectedTransaction.product_type}</p>
                                                                </div>
                                                                <div>
                                                                    <p className="text-xs font-medium text-muted-foreground">BOOKING DATE</p>
                                                                    <p className="mt-1 text-sm text-foreground">
                                                                        {new Date(selectedTransaction.booking_datetime).toLocaleDateString()}
                                                                    </p>
                                                                </div>
                                                                <div>
                                                                    <p className="text-xs font-medium text-muted-foreground">VALUE DATE</p>
                                                                    <p className="mt-1 text-sm text-foreground">
                                                                        {new Date(selectedTransaction.value_date).toLocaleDateString()}
                                                                    </p>
                                                                </div>
                                                            </div>
                                                        </div>

                                                        {/* Originator Information */}
                                                        <div className="space-y-3 border-b pb-4">
                                                            <p className="text-xs font-medium text-muted-foreground uppercase">Originator</p>
                                                            <div className="grid gap-4 md:grid-cols-2">
                                                                <div>
                                                                    <p className="text-xs font-medium text-muted-foreground">NAME</p>
                                                                    <p className="mt-1 text-sm text-foreground">{selectedTransaction.originator_name}</p>
                                                                </div>
                                                                <div>
                                                                    <p className="text-xs font-medium text-muted-foreground">ACCOUNT</p>
                                                                    <p className="mt-1 text-sm text-foreground font-mono">{selectedTransaction.originator_account}</p>
                                                                </div>
                                                                <div>
                                                                    <p className="text-xs font-medium text-muted-foreground">COUNTRY</p>
                                                                    <p className="mt-1 text-sm text-foreground">{selectedTransaction.originator_country}</p>
                                                                </div>
                                                            </div>
                                                        </div>

                                                        {/* Beneficiary Information */}
                                                        <div className="space-y-3 border-b pb-4">
                                                            <p className="text-xs font-medium text-muted-foreground uppercase">Beneficiary</p>
                                                            <div className="grid gap-4 md:grid-cols-2">
                                                                <div>
                                                                    <p className="text-xs font-medium text-muted-foreground">NAME</p>
                                                                    <p className="mt-1 text-sm text-foreground">{selectedTransaction.beneficiary_name}</p>
                                                                </div>
                                                                <div>
                                                                    <p className="text-xs font-medium text-muted-foreground">ACCOUNT</p>
                                                                    <p className="mt-1 text-sm text-foreground font-mono">{selectedTransaction.beneficiary_account}</p>
                                                                </div>
                                                                <div>
                                                                    <p className="text-xs font-medium text-muted-foreground">COUNTRY</p>
                                                                    <p className="mt-1 text-sm text-foreground">{selectedTransaction.beneficiary_country}</p>
                                                                </div>
                                                            </div>
                                                        </div>

                                                        {/* SWIFT Information */}
                                                        {(selectedTransaction.swift_mt || selectedTransaction.ordering_institution_bic) && (
                                                            <div className="space-y-3 border-b pb-4">
                                                                <p className="text-xs font-medium text-muted-foreground uppercase">SWIFT Details</p>
                                                                <div className="grid gap-4 md:grid-cols-2">
                                                                    {selectedTransaction.swift_mt && (
                                                                        <div>
                                                                            <p className="text-xs font-medium text-muted-foreground">MESSAGE TYPE</p>
                                                                            <p className="mt-1 text-sm text-foreground">{selectedTransaction.swift_mt}</p>
                                                                        </div>
                                                                    )}
                                                                    {selectedTransaction.ordering_institution_bic && (
                                                                        <div>
                                                                            <p className="text-xs font-medium text-muted-foreground">ORDERING INSTITUTION BIC</p>
                                                                            <p className="mt-1 text-sm text-foreground font-mono">{selectedTransaction.ordering_institution_bic}</p>
                                                                        </div>
                                                                    )}
                                                                    {selectedTransaction.beneficiary_institution_bic && (
                                                                        <div>
                                                                            <p className="text-xs font-medium text-muted-foreground">BENEFICIARY INSTITUTION BIC</p>
                                                                            <p className="mt-1 text-sm text-foreground font-mono">{selectedTransaction.beneficiary_institution_bic}</p>
                                                                        </div>
                                                                    )}
                                                                    {selectedTransaction.swift_f70_purpose && (
                                                                        <div>
                                                                            <p className="text-xs font-medium text-muted-foreground">PURPOSE CODE (F70)</p>
                                                                            <p className="mt-1 text-sm text-foreground">{selectedTransaction.swift_f70_purpose}</p>
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            </div>
                                                        )}

                                                        {/* Foreign Exchange Information */}
                                                        {selectedTransaction.fx_indicator && (
                                                            <div className="space-y-3 border-b pb-4">
                                                                <p className="text-xs font-medium text-muted-foreground uppercase">FX Details</p>
                                                                <div className="grid gap-4 md:grid-cols-2">
                                                                    <div>
                                                                        <p className="text-xs font-medium text-muted-foreground">CURRENCY PAIR</p>
                                                                        <p className="mt-1 text-sm text-foreground">{selectedTransaction.fx_base_ccy}/{selectedTransaction.fx_quote_ccy}</p>
                                                                    </div>
                                                                    <div>
                                                                        <p className="text-xs font-medium text-muted-foreground">APPLIED RATE</p>
                                                                        <p className="mt-1 text-sm text-foreground">{selectedTransaction.fx_applied_rate.toFixed(6)}</p>
                                                                    </div>
                                                                    <div>
                                                                        <p className="text-xs font-medium text-muted-foreground">MARKET RATE</p>
                                                                        <p className="mt-1 text-sm text-foreground">{selectedTransaction.fx_market_rate.toFixed(6)}</p>
                                                                    </div>
                                                                    <div>
                                                                        <p className="text-xs font-medium text-muted-foreground">SPREAD (bps)</p>
                                                                        <p className="mt-1 text-sm text-foreground">{selectedTransaction.fx_spread_bps}</p>
                                                                    </div>
                                                                    <div>
                                                                        <p className="text-xs font-medium text-muted-foreground">COUNTERPARTY</p>
                                                                        <p className="mt-1 text-sm text-foreground">{selectedTransaction.fx_counterparty}</p>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        )}

                                                        {/* Customer & KYC Information */}
                                                        <div className="space-y-3 border-b pb-4">
                                                            <p className="text-xs font-medium text-muted-foreground uppercase">Customer & KYC</p>
                                                            <div className="grid gap-4 md:grid-cols-2">
                                                                <div>
                                                                    <p className="text-xs font-medium text-muted-foreground">CUSTOMER ID</p>
                                                                    <p className="mt-1 text-sm text-foreground">{selectedTransaction.customer_id}</p>
                                                                </div>
                                                                <div>
                                                                    <p className="text-xs font-medium text-muted-foreground">CUSTOMER TYPE</p>
                                                                    <p className="mt-1 text-sm text-foreground">{selectedTransaction.customer_type}</p>
                                                                </div>
                                                                <div>
                                                                    <p className="text-xs font-medium text-muted-foreground">RISK RATING</p>
                                                                    <p className="mt-1 text-sm text-foreground">{selectedTransaction.customer_risk_rating}</p>
                                                                </div>
                                                                <div>
                                                                    <p className="text-xs font-medium text-muted-foreground">PEP STATUS</p>
                                                                    <p className="mt-1 text-sm text-foreground">
                                                                        <span className={selectedTransaction.customer_is_pep ? "text-destructive font-semibold" : "text-emerald-600"}>
                                                                            {selectedTransaction.customer_is_pep ? "YES - PEP" : "Not a PEP"}
                                                                        </span>
                                                                    </p>
                                                                </div>
                                                                <div>
                                                                    <p className="text-xs font-medium text-muted-foreground">KYC LAST COMPLETED</p>
                                                                    <p className="mt-1 text-sm text-foreground">
                                                                        {new Date(selectedTransaction.kyc_last_completed).toLocaleDateString()}
                                                                    </p>
                                                                </div>
                                                                <div>
                                                                    <p className="text-xs font-medium text-muted-foreground">KYC DUE DATE</p>
                                                                    <p className="mt-1 text-sm text-foreground">
                                                                        {new Date(selectedTransaction.kyc_due_date).toLocaleDateString()}
                                                                    </p>
                                                                </div>
                                                                <div>
                                                                    <p className="text-xs font-medium text-muted-foreground">EDD REQUIRED</p>
                                                                    <p className="mt-1 text-sm text-foreground">{selectedTransaction.edd_required ? "Yes" : "No"}</p>
                                                                </div>
                                                                <div>
                                                                    <p className="text-xs font-medium text-muted-foreground">EDD PERFORMED</p>
                                                                    <p className="mt-1 text-sm text-foreground">{selectedTransaction.edd_performed ? "Yes" : "No"}</p>
                                                                </div>
                                                            </div>
                                                        </div>

                                                        {/* Sanctions & Compliance */}
                                                        <div className="space-y-3 border-b pb-4">
                                                            <p className="text-xs font-medium text-muted-foreground uppercase">Sanctions & Compliance</p>
                                                            <div className="grid gap-4 md:grid-cols-2">
                                                                <div>
                                                                    <p className="text-xs font-medium text-muted-foreground">SANCTIONS SCREENING</p>
                                                                    <p className="mt-1 text-sm text-foreground">{selectedTransaction.sanctions_screening}</p>
                                                                </div>
                                                                <div>
                                                                    <p className="text-xs font-medium text-muted-foreground">TRAVEL RULE COMPLETE</p>
                                                                    <p className="mt-1 text-sm text-foreground">{selectedTransaction.travel_rule_complete ? "Yes" : "No"}</p>
                                                                </div>
                                                                {selectedTransaction.suspicion_determined_datetime && (
                                                                    <div>
                                                                        <p className="text-xs font-medium text-muted-foreground">SUSPICION DETERMINED</p>
                                                                        <p className="mt-1 text-sm text-foreground">
                                                                            {new Date(selectedTransaction.suspicion_determined_datetime).toLocaleString()}
                                                                        </p>
                                                                    </div>
                                                                )}
                                                                {selectedTransaction.str_filed_datetime && (
                                                                    <div>
                                                                        <p className="text-xs font-medium text-muted-foreground">STR FILED</p>
                                                                        <p className="mt-1 text-sm text-foreground">
                                                                            {new Date(selectedTransaction.str_filed_datetime).toLocaleString()}
                                                                        </p>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </div>

                                                        {/* Additional Narrative */}
                                                        {selectedTransaction.narrative && (
                                                            <div className="space-y-2 border-b pb-4">
                                                                <p className="text-xs font-medium text-muted-foreground uppercase">Transaction Narrative</p>
                                                                <p className="text-sm text-foreground bg-muted/50 p-3 rounded">
                                                                    {selectedTransaction.narrative}
                                                                </p>
                                                            </div>
                                                        )}

                                                        {/* Flags */}
                                                        {selectedTransaction.flags.length > 0 && (
                                                            <div className="space-y-2">
                                                                <p className="text-xs font-medium text-muted-foreground uppercase">Alert Flags</p>
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
                                                        {rulesError && (
                                                            <div className="mb-4 rounded-md bg-destructive/10 p-3">
                                                                <p className="text-sm text-destructive">{rulesError}</p>
                                                            </div>
                                                        )}
                                                        {rulesLoading ? (
                                                            <div className="text-center py-4">
                                                                <p className="text-sm text-muted-foreground">Loading rules...</p>
                                                            </div>
                                                        ) : rules.length === 0 ? (
                                                            <div className="text-center py-4">
                                                                <p className="text-sm text-muted-foreground">No rules available</p>
                                                            </div>
                                                        ) : (
                                                            <div className="space-y-3">
                                                                {rules.map((rule) => (
                                                                    <div
                                                                        key={rule.id}
                                                                        className="flex items-start justify-between rounded-lg border p-3"
                                                                    >
                                                                        <div className="flex-1">
                                                                            <p className="text-sm font-semibold text-foreground">
                                                                                Rule ID: {rule.id}
                                                                            </p>
                                                                            <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                                                                                {rule.explanation}
                                                                            </p>
                                                                            {rule.attributes_used && rule.attributes_used.length > 0 && (
                                                                                <p className="text-xs text-muted-foreground mt-2">
                                                                                    <span className="font-medium">Attributes:</span> {rule.attributes_used.slice(0, 3).join(", ")}
                                                                                    {rule.attributes_used.length > 3 && ` +${rule.attributes_used.length - 3}`}
                                                                                </p>
                                                                            )}
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
                                                        )}
                                                    </CardContent>
                                                </Card>

                                                {/* Rule Execution Result */}
                                                {ruleExecutionLoading && (
                                                    <Card>
                                                        <CardContent className="flex items-center justify-center pt-6 pb-6">
                                                            <div className="text-center">
                                                                <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                                                                <p className="mt-2 text-sm text-muted-foreground">Executing rule...</p>
                                                            </div>
                                                        </CardContent>
                                                    </Card>
                                                )}

                                                {ruleExecutionError && (
                                                    <Card className="border-destructive/50 bg-destructive/5">
                                                        <CardContent className="pt-6">
                                                            <div className="flex items-start gap-3">
                                                                <AlertCircle className="size-5 shrink-0 text-destructive mt-0.5" />
                                                                <div>
                                                                    <p className="font-semibold text-destructive">Rule execution failed</p>
                                                                    <p className="text-sm text-destructive/80">{ruleExecutionError}</p>
                                                                </div>
                                                            </div>
                                                        </CardContent>
                                                    </Card>
                                                )}

                                                {ruleResult && !ruleExecutionLoading && (
                                                    <Card
                                                        className={`border-l-4 ${ruleResult.alerts_created > 0
                                                            ? "border-l-destructive bg-destructive/5"
                                                            : "border-l-emerald-500 bg-emerald-50 dark:bg-emerald-900/10"
                                                            }`}
                                                    >
                                                        <CardHeader>
                                                            <div className="flex items-start justify-between">
                                                                <div>
                                                                    <CardTitle className="text-base">
                                                                        Rule Execution Result
                                                                    </CardTitle>
                                                                    <CardDescription className="mt-1">
                                                                        {ruleResult.message}
                                                                    </CardDescription>
                                                                </div>
                                                                {ruleResult.alerts_created > 0 ? (
                                                                    <AlertCircle className="size-6 shrink-0 text-destructive" />
                                                                ) : (
                                                                    <CheckCircle2 className="size-6 shrink-0 text-emerald-600" />
                                                                )}
                                                            </div>
                                                        </CardHeader>
                                                        <CardContent className="space-y-4">
                                                            <div className="grid gap-4 md:grid-cols-3">
                                                                <div className="rounded-lg bg-background p-3">
                                                                    <p className="text-xs font-medium text-muted-foreground">RULES PROCESSED</p>
                                                                    <p className="mt-1 text-lg font-bold">{ruleResult.rules_processed}/{ruleResult.total_rules}</p>
                                                                </div>
                                                                <div className="rounded-lg bg-background p-3">
                                                                    <p className="text-xs font-medium text-muted-foreground">ALERTS CREATED</p>
                                                                    <p className={`mt-1 text-lg font-bold ${ruleResult.alerts_created > 0 ? "text-destructive" : "text-emerald-600"}`}>
                                                                        {ruleResult.alerts_created}
                                                                    </p>
                                                                </div>
                                                                <div className="rounded-lg bg-background p-3">
                                                                    <p className="text-xs font-medium text-muted-foreground">TRANSACTION ID</p>
                                                                    <p className="mt-1 text-xs font-mono text-foreground truncate">
                                                                        {ruleResult.transaction_id}
                                                                    </p>
                                                                </div>
                                                            </div>

                                                            {ruleResult.triggered_rules.length > 0 && (
                                                                <div className="space-y-2 pt-2 border-t">
                                                                    <p className="text-sm font-semibold text-foreground">Triggered Rules:</p>
                                                                    <div className="space-y-2">
                                                                        {ruleResult.triggered_rules.map((triggeredRule) => (
                                                                            <div key={triggeredRule.alert_id} className="rounded-lg bg-destructive/10 p-3">
                                                                                <p className="text-xs font-medium text-destructive">Rule ID: {triggeredRule.rule_id}</p>
                                                                                <p className="text-xs font-medium text-muted-foreground mt-1">Alert ID: {triggeredRule.alert_id}</p>
                                                                                <p className="text-xs text-foreground mt-2 line-clamp-3">
                                                                                    {triggeredRule.rule_text}
                                                                                </p>
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                </div>
                                                            )}
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
                        </>
                    )}
                </div>
            </div>
        </div>
    )
}

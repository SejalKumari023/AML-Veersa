"use client";
import {
  AlertCircle,
  CheckCircle2,
  FileText,
  Play,
  TrendingUp,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getUser } from "~/lib/auth";
import { Button } from "~/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "~/components/ui/card";

interface Transaction {
  id: string;
  transaction_id: string;
  booking_jurisdiction: string;
  regulator: string;
  booking_datetime: string;
  value_date: string;
  amount: number;
  currency: string;
  channel: string;
  product_type: string;
  originator_name: string;
  originator_account: string;
  originator_country: string;
  beneficiary_name: string;
  beneficiary_account: string;
  beneficiary_country: string;
  swift_mt: string | null;
  ordering_institution_bic: string | null;
  beneficiary_institution_bic: string | null;
  swift_f50_present: boolean;
  swift_f59_present: boolean;
  swift_f70_purpose: string | null;
  swift_f71_charges: string | null;
  travel_rule_complete: boolean;
  fx_indicator: boolean;
  fx_base_ccy: string;
  fx_quote_ccy: string;
  fx_applied_rate: number;
  fx_market_rate: number;
  fx_spread_bps: number;
  fx_counterparty: string;
  customer_id: string;
  customer_type: string;
  customer_risk_rating: string;
  customer_is_pep: boolean;
  kyc_last_completed: string;
  kyc_due_date: string;
  edd_required: boolean;
  edd_performed: boolean;
  sow_documented: boolean;
  purpose_code: string;
  narrative: string;
  is_advised: boolean;
  product_complex: boolean;
  client_risk_profile: string;
  suitability_assessed: boolean;
  suitability_result: string;
  product_has_va_exposure: boolean;
  va_disclosure_provided: boolean;
  cash_id_verified: boolean;
  daily_cash_total_customer: number;
  daily_cash_txn_count: number;
  sanctions_screening: string;
  suspicion_determined_datetime: string | null;
  str_filed_datetime: string | null;
  timestamp: string;
  status: "pending" | "flagged" | "cleared" | "escalated";
  risk_score: number | null;
  flags: string[];
}

interface Rule {
  id: string;
  name?: string;
  rule_text: string;
  function_code: string;
  explanation: string;
  attributes_used: string[];
  status?: "active" | "draft";
  created_at: string;
}

interface TriggeredRule {
  rule_id: string;
  rule_text: string;
  alert_id: string;
}

interface RuleExecutionResult {
  message: string;
  transaction_id: string;
  rules_processed: number;
  total_rules: number;
  alerts_created: number;
  triggered_rules: TriggeredRule[];
}

export default function ComplianceTransactionsPage() {
    const router = useRouter();
    useEffect(() => { if (!getUser()) router.replace("/auth/login"); }, [router]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [rules, setRules] = useState<Rule[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [rulesLoading, setRulesLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rulesError, setRulesError] = useState<string | null>(null);

  // Fetch transactions from API
  useEffect(() => {
    const fetchTransactions = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "/api";
        const response = await fetch(`${apiUrl}/data/transactions?limit=100`, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        });

        if (!response.ok) {
          throw new Error(
            `Failed to fetch transactions: ${response.statusText}`,
          );
        }

        const data: Transaction[] = await response.json();
        setTransactions(data);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Unknown error occurred";
        setError(errorMessage);
        console.error("Error fetching transactions:", err);
        // Keep page functional with empty state
        setTransactions([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchTransactions();
  }, []);

  // Fetch rules from API
  useEffect(() => {
    const fetchRules = async () => {
      setRulesLoading(true);
      setRulesError(null);
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "/api";
        const response = await fetch(`${apiUrl}/rules/`, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch rules: ${response.statusText}`);
        }

        const data = await response.json();
        // Handle both array and object with "rules" property
        const rulesList = Array.isArray(data) ? data : data.rules || [];
        setRules(rulesList);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Unknown error occurred";
        setRulesError(errorMessage);
        console.error("Error fetching rules:", err);
        // Keep page functional with empty state
        setRules([]);
      } finally {
        setRulesLoading(false);
      }
    };

    fetchRules();
  }, []);

  const [selectedTransaction, setSelectedTransaction] =
    useState<Transaction | null>(null);
  const [showRunRuleModal, setShowRunRuleModal] = useState(false);
  const [selectedRule, setSelectedRule] = useState<Rule | null>(null);
  const [ruleResult, setRuleResult] = useState<RuleExecutionResult | null>(
    null,
  );
  const [ruleExecutionLoading, setRuleExecutionLoading] = useState(false);
  const [ruleExecutionError, setRuleExecutionError] = useState<string | null>(
    null,
  );

  const getStatusColor = (status: Transaction["status"]) => {
    switch (status) {
      case "cleared":
        return "text-emerald-600 bg-emerald-100 dark:bg-emerald-900/20";
      case "flagged":
        return "text-amber-600 bg-amber-100 dark:bg-amber-900/20";
      case "escalated":
        return "text-destructive bg-destructive/10";
      case "pending":
        return "text-blue-600 bg-blue-100 dark:bg-blue-900/20";
      default:
        return "text-muted-foreground";
    }
  };

  const getRiskColor = (riskScore: number | null) => {
    if (!riskScore) return "text-muted-foreground";
    if (riskScore >= 80) return "text-destructive";
    if (riskScore >= 60) return "text-amber-600";
    if (riskScore >= 40) return "text-blue-600";
    return "text-emerald-600";
  };

  const handleRunRule = async (rule: Rule) => {
    if (!selectedTransaction) return;

    setSelectedRule(rule);
    setRuleExecutionLoading(true);
    setRuleExecutionError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "/api";
      const response = await fetch(
        `${apiUrl}/data/run-rule/${selectedTransaction.transaction_id}/${rule.id}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        },
      );

      if (!response.ok) {
        throw new Error(`Failed to execute rule: ${response.statusText}`);
      }

      const result: RuleExecutionResult = await response.json();
      setRuleResult(result);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Unknown error occurred";
      setRuleExecutionError(errorMessage);
      console.error("Error executing rule:", err);
    } finally {
      setRuleExecutionLoading(false);
    }
  };

  const flaggedCount = transactions.filter(
    (t) => t.status === "flagged",
  ).length;
  const escalatedCount = transactions.filter(
    (t) => t.status === "escalated",
  ).length;
  const highRiskCount = transactions.filter(
    (t) => t.risk_score !== null && t.risk_score >= 60,
  ).length;

  return (
    <div className="bg-background flex min-h-screen flex-col">
      {/* Header */}
      <div className="border-border bg-card border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-foreground text-3xl font-bold tracking-tight">
              Transaction Monitoring
            </h1>
            <p className="text-muted-foreground mt-1 text-sm">
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
                  <AlertCircle className="text-destructive mt-0.5 size-5 shrink-0" />
                  <div>
                    <p className="text-destructive font-semibold">
                      Failed to load transactions
                    </p>
                    <p className="text-destructive/80 text-sm">{error}</p>
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
                  <div className="border-primary inline-block h-8 w-8 animate-spin rounded-full border-b-2"></div>
                  <p className="text-muted-foreground mt-4 text-sm">
                    Loading transactions...
                  </p>
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
                        <p className="text-muted-foreground text-sm">
                          Total Transactions
                        </p>
                        <p className="mt-2 text-3xl font-bold">
                          {transactions.length}
                        </p>
                      </div>
                      <FileText className="text-muted-foreground size-8" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-muted-foreground text-sm">Flagged</p>
                        <p className="mt-2 text-3xl font-bold">
                          {flaggedCount}
                        </p>
                      </div>
                      <AlertCircle className="size-8 text-amber-500" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-muted-foreground text-sm">
                          Escalated
                        </p>
                        <p className="mt-2 text-3xl font-bold">
                          {escalatedCount}
                        </p>
                      </div>
                      <AlertCircle className="text-destructive size-8" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-muted-foreground text-sm">
                          High Risk
                        </p>
                        <p className="mt-2 text-3xl font-bold">
                          {highRiskCount}
                        </p>
                      </div>
                      <TrendingUp className="text-destructive size-8" />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Main Content Grid */}
              <div className="flex flex-col gap-6">
                {/* Transactions List Sidebar */}
                <h2 className="text-foreground mb-4 text-lg font-semibold">
                  Transactions ({transactions.length})
                </h2>
                <div className="flex gap-4">
                  <div className="flex flex-col gap-3 overflow-y-auto pr-2">
                    {transactions.map((transaction) => (
                      <Card
                        key={transaction.id}
                        className={`hover:bg-accent/50 cursor-pointer transition-colors ${
                          selectedTransaction?.id === transaction.id
                            ? "border-primary ring-primary/20 ring-2"
                            : ""
                        }`}
                        onClick={() => setSelectedTransaction(transaction)}
                      >
                        <CardContent className="pt-4">
                          <div className="space-y-2">
                            <div className="flex items-start justify-between gap-2">
                              <h3 className="text-foreground text-xs font-semibold">
                                {transaction.transaction_id}
                              </h3>
                              <span
                                className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${getStatusColor(
                                  transaction.status,
                                )}`}
                              >
                                {transaction.status}
                              </span>
                            </div>
                            <div className="flex items-center justify-between">
                              <p className="text-foreground text-xs font-semibold">
                                {transaction.amount.toLocaleString()}{" "}
                                {transaction.currency}
                              </p>
                              <span
                                className={`text-xs font-bold ${getRiskColor(transaction.risk_score)}`}
                              >
                                {transaction.risk_score ?? "N/A"}
                              </span>
                            </div>
                            <p className="text-muted-foreground line-clamp-1 text-xs">
                              {transaction.originator_name}
                            </p>
                            <p className="text-muted-foreground line-clamp-1 text-xs">
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
                                <CardTitle>
                                  {selectedTransaction.transaction_id}
                                </CardTitle>
                                <CardDescription className="mt-2">
                                  {new Date(
                                    selectedTransaction.timestamp,
                                  ).toLocaleString()}
                                </CardDescription>
                              </div>
                              <span
                                className={`rounded-full px-3 py-1 text-sm font-medium ${getStatusColor(
                                  selectedTransaction.status,
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
                            <CardTitle className="text-base">
                              Transaction Details
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="space-y-6">
                            {/* Basic Transaction Info */}
                            <div className="space-y-3 border-b pb-4">
                              <p className="text-muted-foreground text-xs font-medium uppercase">
                                Transaction Information
                              </p>
                              <div className="grid gap-4 md:grid-cols-2">
                                <div>
                                  <p className="text-muted-foreground text-xs font-medium">
                                    AMOUNT
                                  </p>
                                  <p className="text-foreground mt-1 text-lg font-bold">
                                    {selectedTransaction.amount.toLocaleString()}{" "}
                                    {selectedTransaction.currency}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-muted-foreground text-xs font-medium">
                                    RISK SCORE
                                  </p>
                                  <p
                                    className={`mt-1 text-lg font-bold ${getRiskColor(selectedTransaction.risk_score)}`}
                                  >
                                    {selectedTransaction.risk_score
                                      ? `${selectedTransaction.risk_score}%`
                                      : "N/A"}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-muted-foreground text-xs font-medium">
                                    CHANNEL
                                  </p>
                                  <p className="text-foreground mt-1 text-sm">
                                    {selectedTransaction.channel}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-muted-foreground text-xs font-medium">
                                    PRODUCT TYPE
                                  </p>
                                  <p className="text-foreground mt-1 text-sm">
                                    {selectedTransaction.product_type}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-muted-foreground text-xs font-medium">
                                    BOOKING DATE
                                  </p>
                                  <p className="text-foreground mt-1 text-sm">
                                    {new Date(
                                      selectedTransaction.booking_datetime,
                                    ).toLocaleDateString()}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-muted-foreground text-xs font-medium">
                                    VALUE DATE
                                  </p>
                                  <p className="text-foreground mt-1 text-sm">
                                    {new Date(
                                      selectedTransaction.value_date,
                                    ).toLocaleDateString()}
                                  </p>
                                </div>
                              </div>
                            </div>

                            {/* Originator Information */}
                            <div className="space-y-3 border-b pb-4">
                              <p className="text-muted-foreground text-xs font-medium uppercase">
                                Originator
                              </p>
                              <div className="grid gap-4 md:grid-cols-2">
                                <div>
                                  <p className="text-muted-foreground text-xs font-medium">
                                    NAME
                                  </p>
                                  <p className="text-foreground mt-1 text-sm">
                                    {selectedTransaction.originator_name}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-muted-foreground text-xs font-medium">
                                    ACCOUNT
                                  </p>
                                  <p className="text-foreground mt-1 font-mono text-sm">
                                    {selectedTransaction.originator_account}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-muted-foreground text-xs font-medium">
                                    COUNTRY
                                  </p>
                                  <p className="text-foreground mt-1 text-sm">
                                    {selectedTransaction.originator_country}
                                  </p>
                                </div>
                              </div>
                            </div>

                            {/* Beneficiary Information */}
                            <div className="space-y-3 border-b pb-4">
                              <p className="text-muted-foreground text-xs font-medium uppercase">
                                Beneficiary
                              </p>
                              <div className="grid gap-4 md:grid-cols-2">
                                <div>
                                  <p className="text-muted-foreground text-xs font-medium">
                                    NAME
                                  </p>
                                  <p className="text-foreground mt-1 text-sm">
                                    {selectedTransaction.beneficiary_name}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-muted-foreground text-xs font-medium">
                                    ACCOUNT
                                  </p>
                                  <p className="text-foreground mt-1 font-mono text-sm">
                                    {selectedTransaction.beneficiary_account}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-muted-foreground text-xs font-medium">
                                    COUNTRY
                                  </p>
                                  <p className="text-foreground mt-1 text-sm">
                                    {selectedTransaction.beneficiary_country}
                                  </p>
                                </div>
                              </div>
                            </div>

                            {/* SWIFT Information */}
                            {(selectedTransaction.swift_mt ||
                              selectedTransaction.ordering_institution_bic) && (
                              <div className="space-y-3 border-b pb-4">
                                <p className="text-muted-foreground text-xs font-medium uppercase">
                                  SWIFT Details
                                </p>
                                <div className="grid gap-4 md:grid-cols-2">
                                  {selectedTransaction.swift_mt && (
                                    <div>
                                      <p className="text-muted-foreground text-xs font-medium">
                                        MESSAGE TYPE
                                      </p>
                                      <p className="text-foreground mt-1 text-sm">
                                        {selectedTransaction.swift_mt}
                                      </p>
                                    </div>
                                  )}
                                  {selectedTransaction.ordering_institution_bic && (
                                    <div>
                                      <p className="text-muted-foreground text-xs font-medium">
                                        ORDERING INSTITUTION BIC
                                      </p>
                                      <p className="text-foreground mt-1 font-mono text-sm">
                                        {
                                          selectedTransaction.ordering_institution_bic
                                        }
                                      </p>
                                    </div>
                                  )}
                                  {selectedTransaction.beneficiary_institution_bic && (
                                    <div>
                                      <p className="text-muted-foreground text-xs font-medium">
                                        BENEFICIARY INSTITUTION BIC
                                      </p>
                                      <p className="text-foreground mt-1 font-mono text-sm">
                                        {
                                          selectedTransaction.beneficiary_institution_bic
                                        }
                                      </p>
                                    </div>
                                  )}
                                  {selectedTransaction.swift_f70_purpose && (
                                    <div>
                                      <p className="text-muted-foreground text-xs font-medium">
                                        PURPOSE CODE (F70)
                                      </p>
                                      <p className="text-foreground mt-1 text-sm">
                                        {selectedTransaction.swift_f70_purpose}
                                      </p>
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}

                            {/* Foreign Exchange Information */}
                            {selectedTransaction.fx_indicator && (
                              <div className="space-y-3 border-b pb-4">
                                <p className="text-muted-foreground text-xs font-medium uppercase">
                                  FX Details
                                </p>
                                <div className="grid gap-4 md:grid-cols-2">
                                  <div>
                                    <p className="text-muted-foreground text-xs font-medium">
                                      CURRENCY PAIR
                                    </p>
                                    <p className="text-foreground mt-1 text-sm">
                                      {selectedTransaction.fx_base_ccy}/
                                      {selectedTransaction.fx_quote_ccy}
                                    </p>
                                  </div>
                                  <div>
                                    <p className="text-muted-foreground text-xs font-medium">
                                      APPLIED RATE
                                    </p>
                                    <p className="text-foreground mt-1 text-sm">
                                      {selectedTransaction.fx_applied_rate.toFixed(
                                        6,
                                      )}
                                    </p>
                                  </div>
                                  <div>
                                    <p className="text-muted-foreground text-xs font-medium">
                                      MARKET RATE
                                    </p>
                                    <p className="text-foreground mt-1 text-sm">
                                      {selectedTransaction.fx_market_rate.toFixed(
                                        6,
                                      )}
                                    </p>
                                  </div>
                                  <div>
                                    <p className="text-muted-foreground text-xs font-medium">
                                      SPREAD (bps)
                                    </p>
                                    <p className="text-foreground mt-1 text-sm">
                                      {selectedTransaction.fx_spread_bps}
                                    </p>
                                  </div>
                                  <div>
                                    <p className="text-muted-foreground text-xs font-medium">
                                      COUNTERPARTY
                                    </p>
                                    <p className="text-foreground mt-1 text-sm">
                                      {selectedTransaction.fx_counterparty}
                                    </p>
                                  </div>
                                </div>
                              </div>
                            )}

                            {/* Customer & KYC Information */}
                            <div className="space-y-3 border-b pb-4">
                              <p className="text-muted-foreground text-xs font-medium uppercase">
                                Customer & KYC
                              </p>
                              <div className="grid gap-4 md:grid-cols-2">
                                <div>
                                  <p className="text-muted-foreground text-xs font-medium">
                                    CUSTOMER ID
                                  </p>
                                  <p className="text-foreground mt-1 text-sm">
                                    {selectedTransaction.customer_id}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-muted-foreground text-xs font-medium">
                                    CUSTOMER TYPE
                                  </p>
                                  <p className="text-foreground mt-1 text-sm">
                                    {selectedTransaction.customer_type}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-muted-foreground text-xs font-medium">
                                    RISK RATING
                                  </p>
                                  <p className="text-foreground mt-1 text-sm">
                                    {selectedTransaction.customer_risk_rating}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-muted-foreground text-xs font-medium">
                                    PEP STATUS
                                  </p>
                                  <p className="text-foreground mt-1 text-sm">
                                    <span
                                      className={
                                        selectedTransaction.customer_is_pep
                                          ? "text-destructive font-semibold"
                                          : "text-emerald-600"
                                      }
                                    >
                                      {selectedTransaction.customer_is_pep
                                        ? "YES - PEP"
                                        : "Not a PEP"}
                                    </span>
                                  </p>
                                </div>
                                <div>
                                  <p className="text-muted-foreground text-xs font-medium">
                                    KYC LAST COMPLETED
                                  </p>
                                  <p className="text-foreground mt-1 text-sm">
                                    {new Date(
                                      selectedTransaction.kyc_last_completed,
                                    ).toLocaleDateString()}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-muted-foreground text-xs font-medium">
                                    KYC DUE DATE
                                  </p>
                                  <p className="text-foreground mt-1 text-sm">
                                    {new Date(
                                      selectedTransaction.kyc_due_date,
                                    ).toLocaleDateString()}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-muted-foreground text-xs font-medium">
                                    EDD REQUIRED
                                  </p>
                                  <p className="text-foreground mt-1 text-sm">
                                    {selectedTransaction.edd_required
                                      ? "Yes"
                                      : "No"}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-muted-foreground text-xs font-medium">
                                    EDD PERFORMED
                                  </p>
                                  <p className="text-foreground mt-1 text-sm">
                                    {selectedTransaction.edd_performed
                                      ? "Yes"
                                      : "No"}
                                  </p>
                                </div>
                              </div>
                            </div>

                            {/* Sanctions & Compliance */}
                            <div className="space-y-3 border-b pb-4">
                              <p className="text-muted-foreground text-xs font-medium uppercase">
                                Sanctions & Compliance
                              </p>
                              <div className="grid gap-4 md:grid-cols-2">
                                <div>
                                  <p className="text-muted-foreground text-xs font-medium">
                                    SANCTIONS SCREENING
                                  </p>
                                  <p className="text-foreground mt-1 text-sm">
                                    {selectedTransaction.sanctions_screening}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-muted-foreground text-xs font-medium">
                                    TRAVEL RULE COMPLETE
                                  </p>
                                  <p className="text-foreground mt-1 text-sm">
                                    {selectedTransaction.travel_rule_complete
                                      ? "Yes"
                                      : "No"}
                                  </p>
                                </div>
                                {selectedTransaction.suspicion_determined_datetime && (
                                  <div>
                                    <p className="text-muted-foreground text-xs font-medium">
                                      SUSPICION DETERMINED
                                    </p>
                                    <p className="text-foreground mt-1 text-sm">
                                      {new Date(
                                        selectedTransaction.suspicion_determined_datetime,
                                      ).toLocaleString()}
                                    </p>
                                  </div>
                                )}
                                {selectedTransaction.str_filed_datetime && (
                                  <div>
                                    <p className="text-muted-foreground text-xs font-medium">
                                      STR FILED
                                    </p>
                                    <p className="text-foreground mt-1 text-sm">
                                      {new Date(
                                        selectedTransaction.str_filed_datetime,
                                      ).toLocaleString()}
                                    </p>
                                  </div>
                                )}
                              </div>
                            </div>

                            {/* Additional Narrative */}
                            {selectedTransaction.narrative && (
                              <div className="space-y-2 border-b pb-4">
                                <p className="text-muted-foreground text-xs font-medium uppercase">
                                  Transaction Narrative
                                </p>
                                <p className="text-foreground bg-muted/50 rounded p-3 text-sm">
                                  {selectedTransaction.narrative}
                                </p>
                              </div>
                            )}

                            {/* Flags */}
                            {selectedTransaction.flags.length > 0 && (
                              <div className="space-y-2">
                                <p className="text-muted-foreground text-xs font-medium uppercase">
                                  Alert Flags
                                </p>
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
                            <CardTitle className="text-base">
                              Run Compliance Rules
                            </CardTitle>
                            <CardDescription>
                              Execute active rules against this transaction
                            </CardDescription>
                          </CardHeader>
                          <CardContent>
                            {rulesError && (
                              <div className="bg-destructive/10 mb-4 rounded-md p-3">
                                <p className="text-destructive text-sm">
                                  {rulesError}
                                </p>
                              </div>
                            )}
                            {rulesLoading ? (
                              <div className="py-4 text-center">
                                <p className="text-muted-foreground text-sm">
                                  Loading rules...
                                </p>
                              </div>
                            ) : rules.length === 0 ? (
                              <div className="py-4 text-center">
                                <p className="text-muted-foreground text-sm">
                                  No rules available
                                </p>
                              </div>
                            ) : (
                              <div className="space-y-3">
                                {rules.map((rule) => (
                                  <div
                                    key={rule.id}
                                    className="flex items-start justify-between rounded-lg border p-3"
                                  >
                                    <div className="flex-1">
                                      <p className="text-foreground text-sm font-semibold">
                                        Rule ID: {rule.id}
                                      </p>
                                      <p className="text-muted-foreground mt-1 line-clamp-2 text-xs">
                                        {rule.explanation}
                                      </p>
                                      {rule.attributes_used &&
                                        rule.attributes_used.length > 0 && (
                                          <p className="text-muted-foreground mt-2 text-xs">
                                            <span className="font-medium">
                                              Attributes:
                                            </span>{" "}
                                            {rule.attributes_used
                                              .slice(0, 3)
                                              .join(", ")}
                                            {rule.attributes_used.length > 3 &&
                                              ` +${rule.attributes_used.length - 3}`}
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
                                <div className="border-primary inline-block h-6 w-6 animate-spin rounded-full border-b-2"></div>
                                <p className="text-muted-foreground mt-2 text-sm">
                                  Executing rule...
                                </p>
                              </div>
                            </CardContent>
                          </Card>
                        )}

                        {ruleExecutionError && (
                          <Card className="border-destructive/50 bg-destructive/5">
                            <CardContent className="pt-6">
                              <div className="flex items-start gap-3">
                                <AlertCircle className="text-destructive mt-0.5 size-5 shrink-0" />
                                <div>
                                  <p className="text-destructive font-semibold">
                                    Rule execution failed
                                  </p>
                                  <p className="text-destructive/80 text-sm">
                                    {ruleExecutionError}
                                  </p>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        )}

                        {ruleResult && !ruleExecutionLoading && (
                          <Card
                            className={`border-l-4 ${
                              ruleResult.alerts_created > 0
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
                                  <AlertCircle className="text-destructive size-6 shrink-0" />
                                ) : (
                                  <CheckCircle2 className="size-6 shrink-0 text-emerald-600" />
                                )}
                              </div>
                            </CardHeader>
                            <CardContent className="space-y-4">
                              <div className="grid gap-4 md:grid-cols-3">
                                <div className="bg-background rounded-lg p-3">
                                  <p className="text-muted-foreground text-xs font-medium">
                                    RULES PROCESSED
                                  </p>
                                  <p className="mt-1 text-lg font-bold">
                                    {ruleResult.rules_processed}/
                                    {ruleResult.total_rules}
                                  </p>
                                </div>
                                <div className="bg-background rounded-lg p-3">
                                  <p className="text-muted-foreground text-xs font-medium">
                                    ALERTS CREATED
                                  </p>
                                  <p
                                    className={`mt-1 text-lg font-bold ${ruleResult.alerts_created > 0 ? "text-destructive" : "text-emerald-600"}`}
                                  >
                                    {ruleResult.alerts_created}
                                  </p>
                                </div>
                                <div className="bg-background rounded-lg p-3">
                                  <p className="text-muted-foreground text-xs font-medium">
                                    TRANSACTION ID
                                  </p>
                                  <p className="text-foreground mt-1 truncate font-mono text-xs">
                                    {ruleResult.transaction_id}
                                  </p>
                                </div>
                              </div>

                              {ruleResult.triggered_rules.length > 0 && (
                                <div className="space-y-2 border-t pt-2">
                                  <p className="text-foreground text-sm font-semibold">
                                    Triggered Rules:
                                  </p>
                                  <div className="space-y-2">
                                    {ruleResult.triggered_rules.map(
                                      (triggeredRule) => (
                                        <div
                                          key={triggeredRule.alert_id}
                                          className="bg-destructive/10 rounded-lg p-3"
                                        >
                                          <p className="text-destructive text-xs font-medium">
                                            Rule ID: {triggeredRule.rule_id}
                                          </p>
                                          <p className="text-muted-foreground mt-1 text-xs font-medium">
                                            Alert ID: {triggeredRule.alert_id}
                                          </p>
                                          <p className="text-foreground mt-2 line-clamp-3 text-xs">
                                            {triggeredRule.rule_text}
                                          </p>
                                        </div>
                                      ),
                                    )}
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
                            <FileText className="text-muted-foreground/30 mx-auto size-12" />
                            <p className="text-muted-foreground mt-4 text-sm">
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
  );
}

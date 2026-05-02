"use client";

import { IconSquareRoundedX } from "@tabler/icons-react";
import {
  AlertCircle,
  Bot,
  CheckCircle2,
  Eye,
  FileText,
  Link as LinkIcon,
  Plus,
  User,
} from "lucide-react";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "~/components/ui/sheet";
import { AgentChat } from "~/components/agent/AgentChat";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "~/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "~/components/ui/card";
import { MultiStepLoader } from "~/components/ui/multi-step-loader";
import { getUser, getUserTypeLabel } from "~/lib/auth";

interface RuleNotice {
  id: string;
  title: string;
  regulator: string;
  category: string;
  legalInterpretation: string;
  hasRule: boolean;
  ruleId?: string;
  ruleName?: string;
  createdDate?: string;
  priority: "high" | "medium" | "low";
}

interface Rule {
  id: string;
  noticeId: string;
  name: string;
  description: string;
  createdDate: string;
  status: "draft" | "active" | "archived";
}

export default function CompliancePage() {
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<{
    name: string;
    email: string;
    userType: string;
  } | null>(null);

  useEffect(() => {
    const user = getUser();
    if (!user) {
      router.replace("/auth/login");
    } else {
      setCurrentUser({
        name: user.name,
        email: user.email,
        userType: getUserTypeLabel(user.userType),
      });
    }
  }, [router]);

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
  ]);

  const [rules, setRules] = useState<Rule[]>([]);

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "/api";
    fetch(`${apiUrl}/rules/`)
      .then((r) => r.json())
      .then((data) => {
        const loaded: Rule[] = (data.rules ?? data).map((r: any) => ({
          id: r.id ?? r.rule_id,
          noticeId: "",
          name: r.rule_text?.slice(0, 60) ?? r.id,
          description: r.explanation ?? r.rule_text ?? "",
          createdDate: r.created_at?.split("T")[0] ?? new Date().toISOString().split("T")[0],
          status: "active" as const,
        }));
        setRules(loaded);
      })
      .catch(() => {});
  }, []);

  const [selectedNotice, setSelectedNotice] = useState<RuleNotice | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showRuleModal, setShowRuleModal] = useState(false);
  const [showEditRuleModal, setShowEditRuleModal] = useState(false);
  const [activeRule, setActiveRule] = useState<Rule | null>(null);
  const [editRuleText, setEditRuleText] = useState("");
  const [editRuleExplanation, setEditRuleExplanation] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const loadingStates = [
    { text: "Scraping from regulatory website" },
    { text: "Found 2 new regulations" },
    { text: "Update database" },
    { text: "Update rule" },
    { text: "Running rule" },
    { text: "Rule run complete" },
  ];

  const getPriorityColor = (priority: RuleNotice["priority"]) => {
    switch (priority) {
      case "high":
        return "text-destructive bg-destructive/10";
      case "medium":
        return "text-amber-600 bg-amber-100 dark:bg-amber-900/20";
      case "low":
        return "text-blue-600 bg-blue-100 dark:bg-blue-900/20";
      default:
        return "text-muted-foreground";
    }
  };

  const noRuleCount = notices.filter((n) => !n.hasRule).length;
  const withRuleCount = notices.filter((n) => n.hasRule).length;
  const highPriorityNoRule = notices.filter(
    (n) => !n.hasRule && n.priority === "high",
  ).length;

  const handleCreateRule = (noticeId: string) => {
    setError(null);
    const notice = notices.find((n) => n.id === noticeId) ?? null;
    setSelectedNotice(notice);
    setShowCreateModal(true);
  };

  const handleViewRule = (notice: RuleNotice) => {
    const match =
      rules.find((r) => r.id === notice.ruleId) ||
      rules.find((r) => r.name === notice.ruleName) ||
      null;
    setActiveRule(match);
    setShowRuleModal(true);
  };

  const handleEditRule = (notice: RuleNotice) => {
    const match =
      rules.find((r) => r.id === notice.ruleId) ||
      rules.find((r) => r.name === notice.ruleName) ||
      null;
    if (!match) {
      setError("No linked rule found for this notice.");
      return;
    }
    setActiveRule(match);
    setEditRuleText(match.name || "");
    setEditRuleExplanation(match.description || "");
    setShowEditRuleModal(true);
  };

  const refreshRules = async () => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "/api";
    const data = await fetch(`${apiUrl}/rules/`).then((r) => r.json());
    const loaded: Rule[] = (data.rules ?? data).map((r: any) => ({
      id: r.id ?? r.rule_id,
      noticeId: "",
      name: r.rule_text?.slice(0, 60) ?? r.id,
      description: r.explanation ?? r.rule_text ?? "",
      createdDate:
        r.created_at?.split("T")[0] ?? new Date().toISOString().split("T")[0],
      status: "active" as const,
    }));
    setRules(loaded);
  };

  const submitRuleEdit = async () => {
    if (!activeRule) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "/api";
      const res = await fetch(`${apiUrl}/rules/${activeRule.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          rule_text: editRuleText,
          explanation: editRuleExplanation,
        }),
      });
      if (!res.ok) {
        throw new Error(`Failed to update rule: ${res.statusText}`);
      }
      await refreshRules();
      setShowEditRuleModal(false);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to update rule";
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmitRule = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!selectedNotice) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const formData = new FormData(e.currentTarget);
      const ruleName = formData.get("ruleName") as string;
      const description = formData.get("description") as string;

      if (!ruleName || !description) {
        setError("Rule name and description are required");
        setIsSubmitting(false);
        return;
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "/api";
      const response = await fetch(`${apiUrl}/rules/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          rule: description,
          rule_id: `rule-${Date.now()}`,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to create rule: ${response.statusText}`);
      }

      const result = await response.json();
      console.log("Rule created successfully:", result);

      // Update the notices state to mark the rule as created
      const updatedNotices = notices.map((notice) =>
        notice.id === selectedNotice.id
          ? {
              ...notice,
              hasRule: true,
              ruleId: result.result?.rule_id || `rule-${Date.now()}`,
              ruleName: ruleName,
              createdDate: new Date().toISOString().split("T")[0],
            }
          : notice,
      );
      setNotices(updatedNotices);

      // Refresh real rules from API
      fetch(`${apiUrl}/rules/`)
        .then((r) => r.json())
        .then((data) => {
          const loaded: Rule[] = (data.rules ?? data).map((r: any) => ({
            id: r.id ?? r.rule_id,
            noticeId: "",
            name: r.rule_text?.slice(0, 60) ?? r.id,
            description: r.explanation ?? r.rule_text ?? "",
            createdDate: r.created_at?.split("T")[0] ?? new Date().toISOString().split("T")[0],
            status: "active" as const,
          }));
          setRules(loaded);
        })
        .catch(() => {});

      setShowCreateModal(false);
      setSelectedNotice(null);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Unknown error occurred";
      setError(errorMessage);
      console.error("Error creating rule:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-background flex min-h-screen flex-col">
      {/* Header */}
      <div className="border-border bg-card border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-foreground text-3xl font-bold tracking-tight">
              Compliance Rule Management
            </h1>
            <p className="text-muted-foreground mt-1 text-sm">
              Review legal interpretations and create compliance rules for
              regulatory notices
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button
              onClick={() => setLoading(true)}
              className="bg-[#39C3EF] font-medium text-black transition duration-200 hover:bg-[#39C3EF]/90"
              style={{
                boxShadow:
                  "0px -1px 0px 0px #ffffff40 inset, 0px 1px 0px 0px #ffffff40 inset",
              }}
            >
              Scan Regulatory Updates
            </Button>
            {currentUser && (
              <div className="border-border bg-background flex items-center gap-3 rounded-lg border px-4 py-2">
                <User className="text-muted-foreground size-5" />
                <div className="text-right">
                  <p className="text-foreground text-sm font-medium">
                    {currentUser.name}
                  </p>
                  <p className="text-muted-foreground text-xs">
                    {currentUser.userType}
                  </p>
                </div>
              </div>
            )}
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
                    <p className="text-muted-foreground text-sm">
                      Total Notices
                    </p>
                    <p className="mt-2 text-3xl font-bold">{notices.length}</p>
                  </div>
                  <FileText className="text-muted-foreground size-8" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-muted-foreground text-sm">
                      Rules Created
                    </p>
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
                    <p className="text-muted-foreground text-sm">
                      Pending Rules
                    </p>
                    <p className="mt-2 text-3xl font-bold">{noRuleCount}</p>
                    {highPriorityNoRule > 0 && (
                      <p className="text-destructive mt-1 text-xs">
                        {highPriorityNoRule} high priority
                      </p>
                    )}
                  </div>
                  <AlertCircle className="text-destructive size-8" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Content Grid */}
          <div className="flex flex-col gap-6">
            {/* Notices List */}
            <h2 className="text-foreground mb-4 text-lg font-semibold">
              Notices ({notices.length})
            </h2>
            <div className="flex gap-4">
              <div className="flex flex-none flex-col gap-4">
                {notices.map((notice) => (
                  <Card
                    key={notice.id}
                    className={`hover:bg-accent/50 cursor-pointer transition-colors ${
                      selectedNotice?.id === notice.id
                        ? "border-primary ring-primary/20 ring-2"
                        : ""
                    }`}
                    onClick={() => setSelectedNotice(notice)}
                  >
                    <CardContent className="pt-4">
                      <div className="space-y-2">
                        <div className="flex items-start justify-between gap-2">
                          <h3 className="text-foreground line-clamp-2 text-xs font-semibold">
                            {notice.title}
                          </h3>
                          {notice.hasRule ? (
                            <CheckCircle2 className="size-4 shrink-0 text-emerald-500" />
                          ) : (
                            <AlertCircle className="text-destructive size-4 shrink-0" />
                          )}
                        </div>
                        <p className="text-muted-foreground text-xs">
                          {notice.regulator}
                        </p>
                        <p className="text-muted-foreground text-xs">
                          {notice.category}
                        </p>
                        <div className="flex gap-1 pt-1">
                          <span
                            className={`inline-block rounded px-1.5 py-0.5 text-xs font-medium ${getPriorityColor(
                              notice.priority,
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
                              {selectedNotice.regulator} •{" "}
                              {selectedNotice.category}
                            </CardDescription>
                          </div>
                          {selectedNotice.hasRule ? (
                            <CheckCircle2 className="size-6 shrink-0 text-emerald-500" />
                          ) : (
                            <AlertCircle className="text-destructive size-6 shrink-0" />
                          )}
                        </div>
                      </CardHeader>
                    </Card>

                    {/* Legal Interpretation */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">
                          Legal Interpretation
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-foreground text-sm leading-relaxed">
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
                            <p className="text-muted-foreground text-xs font-medium">
                              RULE NAME
                            </p>
                            <p className="text-foreground mt-1 text-sm font-semibold">
                              {selectedNotice.ruleName}
                            </p>
                          </div>
                          <div>
                            <p className="text-muted-foreground text-xs font-medium">
                              CREATED DATE
                            </p>
                            <p className="text-foreground mt-1 text-sm">
                              {new Date(
                                selectedNotice.createdDate!,
                              ).toLocaleDateString()}
                            </p>
                          </div>
                          <div className="flex gap-2 pt-2">
                            <Button variant="outline" size="sm" onClick={() => handleViewRule(selectedNotice)}>
                              <Eye className="mr-2 size-4" />
                              View Rule
                            </Button>
                            <Button variant="outline" size="sm" onClick={() => handleEditRule(selectedNotice)}>
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
                          <div className="rounded-lg bg-white/50 p-3 dark:bg-black/20">
                            <p className="text-muted-foreground text-xs font-medium">
                              ACTION REQUIRED
                            </p>
                            <p className="text-foreground mt-2 text-sm">
                              Use the legal interpretation above to create a
                              compliance rule that operationalizes this
                              regulatory requirement.
                            </p>
                          </div>

                          <div className="flex gap-2 pt-2">
                            <Button
                              onClick={() =>
                                handleCreateRule(selectedNotice.id)
                              }
                              className="flex-1"
                            >
                              <Plus className="mr-2 size-4" />
                              Create Rule
                            </Button>
                            <Button variant="outline" onClick={() => setSelectedNotice(selectedNotice)}>
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
                          <p className="text-muted-foreground text-sm font-medium">
                            Priority
                          </p>
                          <span
                            className={`rounded-full px-3 py-1 text-sm font-medium ${getPriorityColor(
                              selectedNotice.priority,
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
                        <FileText className="text-muted-foreground/30 mx-auto size-12" />
                        <p className="text-muted-foreground mt-4 text-sm">
                          Select a notice to view legal interpretation and
                          manage rules
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
          <Card className="mx-4 w-full max-w-2xl">
            <CardHeader>
              <CardTitle>Create New Rule</CardTitle>
              <CardDescription>
                Define a compliance rule based on the legal interpretation
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {selectedNotice && (
                <div>
                  <p className="text-muted-foreground text-sm font-medium">
                    FOR NOTICE
                  </p>
                  <p className="text-foreground mt-1 text-sm font-semibold">
                    {selectedNotice.title}
                  </p>
                </div>
              )}

              {error && (
                <div className="bg-destructive/10 text-destructive rounded-md p-3 text-sm">
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmitRule} className="space-y-4">
                <div>
                  <label
                    htmlFor="ruleName"
                    className="text-foreground block text-sm font-medium"
                  >
                    Rule Name *
                  </label>
                  <input
                    id="ruleName"
                    name="ruleName"
                    type="text"
                    placeholder="Enter rule name"
                    required
                    disabled={isSubmitting}
                    className="border-border bg-background text-foreground placeholder-muted-foreground mt-1 block w-full rounded-md border px-3 py-2 text-sm disabled:opacity-50"
                  />
                </div>

                <div>
                  <label
                    htmlFor="description"
                    className="text-foreground block text-sm font-medium"
                  >
                    Description *
                  </label>
                  <textarea
                    id="description"
                    name="description"
                    placeholder="Describe the rule and how it addresses the regulatory requirement"
                    rows={4}
                    required
                    disabled={isSubmitting}
                    className="border-border bg-background text-foreground placeholder-muted-foreground mt-1 block w-full rounded-md border px-3 py-2 text-sm disabled:opacity-50"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setShowCreateModal(false);
                      setError(null);
                    }}
                    disabled={isSubmitting}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={isSubmitting}>
                    {isSubmitting ? "Creating..." : "Create Rule"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}

      {showRuleModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="mx-4 w-full max-w-2xl">
            <CardHeader>
              <CardTitle>Rule Details</CardTitle>
              <CardDescription>Linked rule for the selected notice</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {activeRule ? (
                <>
                  <p className="text-sm"><span className="font-semibold">Rule ID:</span> {activeRule.id}</p>
                  <p className="text-sm"><span className="font-semibold">Name:</span> {activeRule.name}</p>
                  <p className="text-sm"><span className="font-semibold">Description:</span> {activeRule.description}</p>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">No stored rule matched this notice.</p>
              )}
              <div className="flex justify-end">
                <Button variant="outline" onClick={() => setShowRuleModal(false)}>Close</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {showEditRuleModal && activeRule && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="mx-4 w-full max-w-2xl">
            <CardHeader>
              <CardTitle>Edit Rule</CardTitle>
              <CardDescription>Update text and explanation for {activeRule.id}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium">Rule Text</label>
                <textarea
                  className="border-border bg-background mt-1 block w-full rounded-md border px-3 py-2 text-sm"
                  rows={4}
                  value={editRuleText}
                  onChange={(e) => setEditRuleText(e.target.value)}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Explanation</label>
                <textarea
                  className="border-border bg-background mt-1 block w-full rounded-md border px-3 py-2 text-sm"
                  rows={4}
                  value={editRuleExplanation}
                  onChange={(e) => setEditRuleExplanation(e.target.value)}
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setShowEditRuleModal(false)} disabled={isSubmitting}>
                  Cancel
                </Button>
                <Button onClick={submitRuleEdit} disabled={isSubmitting || !editRuleText.trim()}>
                  {isSubmitting ? "Saving..." : "Save Changes"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Multi-Step Loader */}
      <MultiStepLoader
        loadingStates={loadingStates}
        loading={loading}
        duration={2000}
        loop={false}
      />

      {/* Close Button */}
      {loading && (
        <button
          className="fixed top-4 right-4 z-[120] text-black dark:text-white"
          onClick={() => setLoading(false)}
        >
          <IconSquareRoundedX className="h-10 w-10" />
        </button>
      )}

      {/* AI Agent floating button */}
      <Sheet>
        <SheetTrigger asChild>
          <button
            className="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-full bg-primary px-4 py-3 text-sm font-medium text-primary-foreground shadow-lg hover:bg-primary/90 transition-colors"
            aria-label="Open AI Agent"
          >
            <Bot className="size-4" />
            AI Agent
          </button>
        </SheetTrigger>
        <SheetContent side="right" className="w-[420px] p-0 flex flex-col">
          <SheetTitle className="sr-only">AI Agent</SheetTitle>
          <AgentChat title="Compliance Agent" defaultContext="Show me recent high-risk alerts" />
        </SheetContent>
      </Sheet>
    </div>
  );
}

"use client";

import { User, FileText, Eye } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "~/components/ui/button";
import { env } from "~/env";

const BACKEND_2_API_URL = env.NEXT_PUBLIC_API_URL_2 ?? "/llm-api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "~/components/ui/card";
import { getUser, getUserTypeLabel } from "~/lib/auth";
import { DocumentUploadZone } from "~/components/document-processing/document-upload-zone";
import { DocumentAnalysisTabs } from "~/components/document-processing/document-analysis-tabs";
import { AnalysisReportDialog } from "~/components/document-processing/analysis-report-dialog";
import type {
  DocumentAnalysis,
  AnalysisReport,
} from "~/types/document-processing";

export default function ClientVerificationPage() {
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<{
    name: string;
    email: string;
    userType: string;
  } | null>(null);

  const [selectedAnalysis, setSelectedAnalysis] = useState<DocumentAnalysis | null>(null);
  const [showReportDialog, setShowReportDialog] = useState(false);
  const [reportData, setReportData] = useState<AnalysisReport | null>(null);

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

  const [analyses, setAnalyses] = useState<DocumentAnalysis[]>([]);
  const asString = (value: unknown, fallback: string): string =>
    typeof value === "string" ? value : fallback;
  const asNumber = (value: unknown, fallback = 0): number =>
    typeof value === "number" ? value : fallback;

  const toRiskLevel = (score?: number): "low" | "medium" | "high" => {
    if (!score) return "low";
    if (score >= 70) return "high";
    if (score >= 40) return "medium";
    return "low";
  };

  const toUiStatus = (
    status: string,
  ): "pending" | "uploading" | "processing" | "completed" | "failed" => {
    if (status === "queued") return "pending";
    if (status === "processing") return "processing";
    if (status === "completed") return "completed";
    if (status === "failed") return "failed";
    return "pending";
  };

  useEffect(() => {
    const fetchAnalyses = async () => {
      try {
        const res = await fetch(`${BACKEND_2_API_URL}/documents/analysis`);
        if (!res.ok) return;
        const rows = (await res.json()) as Array<Record<string, unknown>>;
        const mapped: DocumentAnalysis[] = rows.map((row) => {
          const riskScoreRaw = Number(row.risk_score ?? 0);
          const riskPercent = Math.round(riskScoreRaw * 100);
          const riskLevel = toRiskLevel(riskPercent);
          const status = toUiStatus(asString(row.analysis_status, "pending"));
          return {
            id: asString(row.id, ""),
            documentType: "other",
            status,
            metadata: {
              filename: asString(row.filename, "Unknown"),
              fileSize: asNumber((row as { file_size?: unknown }).file_size),
              fileType: asString(row.file_type, "application/pdf"),
              mimeType: asString(row.file_type, "application/pdf"),
              uploadedAt: asString(row.upload_timestamp, new Date().toISOString()),
              uploadedBy: currentUser?.name ?? "Front Office User",
              pageCount: asNumber((row.metadata as { total_pages?: unknown } | undefined)?.total_pages),
            },
            riskScore: {
              overall: riskPercent,
              level: riskLevel,
              factors: [],
              recommendation:
                riskLevel === "high"
                  ? "Escalate for manual compliance review."
                  : riskLevel === "medium"
                    ? "Review findings before approval."
                    : "Proceed with standard checks.",
              requiresReview: riskLevel !== "low",
            },
            processingTime: 0,
            auditTrail: [
              {
                timestamp: asString(row.upload_timestamp, new Date().toISOString()),
                action: "Document uploaded",
                user: currentUser?.name ?? "Front Office User",
                details: asString(row.filename, "Document"),
              },
              {
                timestamp: new Date().toISOString(),
                action: `Analysis ${status}`,
                user: "System",
                details: `Current status: ${status}`,
              },
            ],
            error: (row as { error_message?: string }).error_message,
          };
        });
        setAnalyses(mapped);
      } catch {
        // ignore transient fetch errors to keep UI usable
      }
    };

    void fetchAnalyses();
    const interval = setInterval(() => {
      void fetchAnalyses();
    }, 5000);
    return () => clearInterval(interval);
  }, [currentUser?.name]);

  const handleViewReport = (analysis: DocumentAnalysis) => {
    // Generate report from analysis
    const report: AnalysisReport = {
      documentId: analysis.id,
      generatedAt: new Date().toISOString(),
      summary: {
        overallStatus: analysis.formatValidation?.status ?? "pass",
        riskLevel: analysis.riskScore?.level ?? "low",
        keyFindings: [
          `Document type: ${analysis.documentType.replace("_", " ")}`,
          `Processing time: ${(analysis.processingTime! / 1000).toFixed(2)}s`,
          analysis.riskScore
            ? `Risk score: ${analysis.riskScore.overall}/100`
            : "No risk assessment available",
        ],
        recommendations: analysis.riskScore
          ? [analysis.riskScore.recommendation]
          : ["No recommendations available"],
      },
      sections: {
        documentInfo: analysis.metadata,
        formatValidation: analysis.formatValidation ?? {
          status: "pass",
          score: 100,
          issues: [],
          checks: {
            spacing: true,
            fonts: true,
            indentation: true,
            spelling: true,
            headers: true,
            completeness: true,
          },
        },
        imageAnalysis: analysis.imageAnalysis,
        riskAssessment: analysis.riskScore ?? {
          overall: 0,
          level: "low",
          factors: [],
          recommendation: "No risk assessment performed",
          requiresReview: false,
        },
      },
      nextSteps: [
        "Review the risk assessment and validation results",
        "Verify any flagged issues manually",
        analysis.riskScore?.requiresReview
          ? "Contact client for additional verification"
          : "Proceed with KYC approval",
        "Update client record in system",
      ],
    };

    setReportData(report);
    setShowReportDialog(true);
  };

  return (
    <div className="bg-background flex min-h-screen flex-col">
      {/* Header */}
      <div className="border-border bg-card border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-foreground text-3xl font-bold tracking-tight">
              Client Document Verification
            </h1>
            <p className="text-muted-foreground mt-1 text-sm">
              Upload and verify client documents for KYC compliance
            </p>
          </div>
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

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-6">
        <div className="mx-auto max-w-7xl space-y-6">
          {/* Stats Cards */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-muted-foreground text-sm">
                      Total Analyzed
                    </p>
                    <p className="mt-2 text-3xl font-bold">{analyses.length}</p>
                  </div>
                  <FileText className="text-muted-foreground size-8" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-muted-foreground text-sm">Low Risk</p>
                    <p className="mt-2 text-3xl font-bold">
                      {analyses.filter((a) => a.riskScore?.level === "low").length}
                    </p>
                  </div>
                  <div className="size-8 rounded-full bg-emerald-100 dark:bg-emerald-900/20" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-muted-foreground text-sm">
                      Needs Review
                    </p>
                    <p className="mt-2 text-3xl font-bold">
                      {
                        analyses.filter(
                          (a) => a.riskScore?.requiresReview === true,
                        ).length
                      }
                    </p>
                  </div>
                  <div className="size-8 rounded-full bg-amber-100 dark:bg-amber-900/20" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-muted-foreground text-sm">
                      Avg Process Time
                    </p>
                    <p className="mt-2 text-3xl font-bold">
                      {analyses.length === 0
                        ? "0.0"
                        : (
                            analyses.reduce(
                              (acc, a) => acc + (a.processingTime ?? 0),
                              0,
                            ) /
                            analyses.length /
                            1000
                          ).toFixed(1)}
                      s
                    </p>
                  </div>
                  <div className="size-8 rounded-full bg-blue-100 dark:bg-blue-900/20" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Upload Section */}
          <Card>
            <CardHeader>
              <CardTitle>Upload Client Documents</CardTitle>
              <CardDescription>
                Upload passports, utility bills, bank statements, or other KYC
                documents for automated verification
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DocumentUploadZone
                acceptedTypes={[".pdf", ".jpg", ".jpeg", ".png"]}
                maxSizeMB={10}
                allowMultiple={true}
                onUpload={async (files) => {
                  for (const file of files) {
                    try {
                      const formData = new FormData();
                      formData.append("file", file);
                      const res = await fetch(`${BACKEND_2_API_URL}/documents/upload`, {
                        method: "POST",
                        body: formData,
                      });
                      if (!res.ok) { console.error("Upload failed:", res.statusText); continue; }
                      await res.json();
                    } catch (err) { console.error("Upload error:", err); }
                  }
                }}
              />
            </CardContent>
          </Card>

          {/* Recent Analyses */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Document Analyses</CardTitle>
              <CardDescription>
                View and manage analyzed client documents
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {analyses.map((analysis) => (
                <div
                  key={analysis.id}
                  className="hover:bg-accent/50 cursor-pointer rounded-lg border border-border p-4 transition-colors"
                  onClick={() => setSelectedAnalysis(analysis)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <FileText className="size-5 text-muted-foreground" />
                      <div>
                        <p className="text-foreground text-sm font-medium">
                          {analysis.metadata.filename}
                        </p>
                        <p className="text-muted-foreground text-xs">
                          {analysis.documentType.replace("_", " ")} •{" "}
                          {new Date(
                            analysis.metadata.uploadedAt,
                          ).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {analysis.riskScore && (
                        <div className="text-right">
                          <p className="text-foreground text-sm font-medium">
                            Risk: {analysis.riskScore.overall}/100
                          </p>
                          <p
                            className={`text-xs ${
                              analysis.status === "processing" || analysis.status === "pending"
                                ? "text-blue-600"
                                :
                              analysis.riskScore.level === "low"
                                ? "text-emerald-600"
                                : analysis.riskScore.level === "medium"
                                  ? "text-amber-600"
                                  : "text-destructive"
                            }`}
                          >
                            {analysis.status === "processing" || analysis.status === "pending"
                              ? analysis.status.toUpperCase()
                              : analysis.riskScore.level.toUpperCase()}
                          </p>
                        </div>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleViewReport(analysis);
                        }}
                      >
                        <Eye className="mr-2 size-4" />
                        View Report
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Selected Analysis Details */}
          {selectedAnalysis && (
            <DocumentAnalysisTabs analysis={selectedAnalysis} />
          )}
        </div>
      </div>

      {/* Report Dialog */}
      <AnalysisReportDialog
        report={reportData}
        open={showReportDialog}
        onOpenChange={setShowReportDialog}
      />
    </div>
  );
}

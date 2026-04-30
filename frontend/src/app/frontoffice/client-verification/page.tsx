"use client";

import { User, FileText, Eye } from "lucide-react";
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
      router.push("/auth/login");
    } else {
      setCurrentUser({
        name: user.name,
        email: user.email,
        userType: getUserTypeLabel(user.userType),
      });
    }
  }, [router]);

  // Mock document analyses
  const [analyses] = useState<DocumentAnalysis[]>([
    {
      id: "doc-1",
      documentType: "passport",
      status: "completed",
      metadata: {
        filename: "john_doe_passport.pdf",
        fileSize: 2457600,
        fileType: "application/pdf",
        mimeType: "application/pdf",
        uploadedAt: "2025-01-02T10:30:00Z",
        uploadedBy: "Sarah Chen",
        pageCount: 1,
      },
      formatValidation: {
        status: "pass",
        score: 95,
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
      imageAnalysis: {
        authenticity: {
          isAuthentic: true,
          confidence: 0.92,
          reverseImageSearchResults: 0,
        },
        aiDetection: {
          isAIGenerated: false,
          confidence: 0.88,
          indicators: [],
        },
        tampering: {
          isTampered: false,
          confidence: 0.91,
          anomalies: [],
        },
        forensic: {
          fileMetadata: {
            createdDate: "2024-11-15T14:20:00Z",
            modifiedDate: "2024-11-15T14:20:00Z",
            software: "Adobe Scan",
            device: "iPhone 14 Pro",
          },
          pixelAnalysis: {
            inconsistencies: 0,
            suspiciousRegions: [],
          },
          compressionAnalysis: {
            multipleCompression: false,
            artifacts: [],
          },
        },
        overallRisk: "low",
      },
      riskScore: {
        overall: 15,
        level: "low",
        factors: [
          {
            category: "Document Authenticity",
            score: 10,
            weight: 0.4,
            description: "Passport verification passed all authenticity checks",
            status: "pass",
          },
          {
            category: "Image Quality",
            score: 8,
            weight: 0.3,
            description: "High-quality scan with no tampering detected",
            status: "pass",
          },
          {
            category: "Format Compliance",
            score: 5,
            weight: 0.3,
            description: "Document meets standard formatting requirements",
            status: "pass",
          },
        ],
        recommendation:
          "Document verified successfully. Client KYC can proceed to next stage.",
        requiresReview: false,
      },
      processingTime: 3450,
      auditTrail: [
        {
          timestamp: "2025-01-02T10:30:15Z",
          action: "Document uploaded",
          user: "Sarah Chen",
          details: "Passport document uploaded for client John Doe",
        },
        {
          timestamp: "2025-01-02T10:30:18Z",
          action: "Analysis completed",
          user: "System",
          details: "Automated analysis completed with low risk score",
        },
      ],
    },
    {
      id: "doc-2",
      documentType: "utility_bill",
      status: "completed",
      metadata: {
        filename: "utility_bill_jane_smith.pdf",
        fileSize: 1843200,
        fileType: "application/pdf",
        mimeType: "application/pdf",
        uploadedAt: "2025-01-02T11:15:00Z",
        uploadedBy: "Sarah Chen",
        pageCount: 2,
      },
      formatValidation: {
        status: "warning",
        score: 72,
        issues: [
          {
            type: "spacing",
            severity: "low",
            description: "Inconsistent line spacing detected in address section",
            location: "Page 1, Lines 12-15",
            suggestion: "Verify address details manually",
          },
          {
            type: "font",
            severity: "medium",
            description: "Multiple font types detected",
            location: "Page 1, Header section",
            suggestion: "Check if document has been modified",
          },
        ],
        checks: {
          spacing: false,
          fonts: false,
          indentation: true,
          spelling: true,
          headers: true,
          completeness: true,
        },
      },
      riskScore: {
        overall: 45,
        level: "medium",
        factors: [
          {
            category: "Document Authenticity",
            score: 35,
            weight: 0.4,
            description: "Some formatting inconsistencies detected",
            status: "warning",
          },
          {
            category: "Format Compliance",
            score: 28,
            weight: 0.6,
            description: "Document has multiple font types and spacing issues",
            status: "warning",
          },
        ],
        recommendation:
          "Manual review recommended due to formatting inconsistencies. Verify utility bill authenticity with provider.",
        requiresReview: true,
      },
      processingTime: 4120,
      auditTrail: [
        {
          timestamp: "2025-01-02T11:15:10Z",
          action: "Document uploaded",
          user: "Sarah Chen",
          details: "Utility bill uploaded for client Jane Smith",
        },
        {
          timestamp: "2025-01-02T11:15:14Z",
          action: "Analysis completed",
          user: "System",
          details: "Analysis flagged for manual review",
        },
      ],
    },
  ]);

  const handleViewReport = (analysis: DocumentAnalysis) => {
    // Generate report from analysis
    const report: AnalysisReport = {
      documentId: analysis.id,
      generatedAt: new Date().toISOString(),
      summary: {
        overallStatus: analysis.formatValidation?.status || "pass",
        riskLevel: analysis.riskScore?.level || "low",
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
        formatValidation: analysis.formatValidation || {
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
        riskAssessment: analysis.riskScore || {
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
                      {(
                        analyses.reduce(
                          (acc, a) => acc + (a.processingTime || 0),
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
                onUpload={(files) => {
                  console.log("Files uploaded:", files);
                  // Here you would integrate with the backend API
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
                              analysis.riskScore.level === "low"
                                ? "text-emerald-600"
                                : analysis.riskScore.level === "medium"
                                  ? "text-amber-600"
                                  : "text-destructive"
                            }`}
                          >
                            {analysis.riskScore.level.toUpperCase()}
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

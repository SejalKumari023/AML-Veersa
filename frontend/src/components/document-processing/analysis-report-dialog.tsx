"use client";

import {
  FileText,
  Download,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Printer,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "~/components/ui/dialog";
import { Button } from "~/components/ui/button";
import { Badge } from "~/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "~/components/ui/card";
import { Separator } from "~/components/ui/separator";
import type { AnalysisReport } from "~/types/document-processing";

interface AnalysisReportDialogProps {
  report: AnalysisReport | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AnalysisReportDialog({
  report,
  open,
  onOpenChange,
}: AnalysisReportDialogProps) {
  if (!report) return null;

  const getStatusIcon = (status: AnalysisReport["summary"]["overallStatus"]) => {
    switch (status) {
      case "pass":
        return <CheckCircle2 className="size-6 text-emerald-500" />;
      case "warning":
        return <AlertTriangle className="size-6 text-amber-500" />;
      case "fail":
        return <XCircle className="size-6 text-destructive" />;
    }
  };

  const getRiskColor = (risk: AnalysisReport["summary"]["riskLevel"]) => {
    switch (risk) {
      case "low":
        return "text-emerald-600 bg-emerald-100 dark:bg-emerald-900/20";
      case "medium":
        return "text-amber-600 bg-amber-100 dark:bg-amber-900/20";
      case "high":
        return "text-orange-600 bg-orange-100 dark:bg-orange-900/20";
      case "critical":
        return "text-destructive bg-destructive/10";
    }
  };

  const handleDownload = () => {
    // Create a JSON file with the report data
    const dataStr = JSON.stringify(report, null, 2);
    const dataUri =
      "data:application/json;charset=utf-8," + encodeURIComponent(dataStr);
    const exportFileDefaultName = `analysis-report-${report.documentId}.json`;

    const linkElement = document.createElement("a");
    linkElement.setAttribute("href", dataUri);
    linkElement.setAttribute("download", exportFileDefaultName);
    linkElement.click();
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] max-w-4xl overflow-y-auto">
        <DialogHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <FileText className="size-8 text-muted-foreground" />
              <div>
                <DialogTitle className="text-2xl">Analysis Report</DialogTitle>
                <DialogDescription>
                  Generated on{" "}
                  {new Date(report.generatedAt).toLocaleString()}
                </DialogDescription>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={handlePrint}>
                <Printer className="mr-2 size-4" />
                Print
              </Button>
              <Button variant="outline" size="sm" onClick={handleDownload}>
                <Download className="mr-2 size-4" />
                Download
              </Button>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-6">
          {/* Summary Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {getStatusIcon(report.summary.overallStatus)}
                Executive Summary
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-muted-foreground text-sm">
                    Overall Status
                  </p>
                  <p className="text-foreground mt-1 text-lg font-semibold capitalize">
                    {report.summary.overallStatus}
                  </p>
                </div>
                <Badge className={`text-sm ${getRiskColor(report.summary.riskLevel)}`}>
                  {report.summary.riskLevel.toUpperCase()} RISK
                </Badge>
              </div>

              <Separator />

              <div>
                <p className="text-foreground mb-2 text-sm font-medium">
                  Key Findings
                </p>
                <ul className="space-y-2">
                  {report.summary.keyFindings.map((finding, idx) => (
                    <li
                      key={idx}
                      className="flex items-start gap-2 text-sm text-muted-foreground"
                    >
                      <span className="text-foreground mt-1 font-medium">•</span>
                      {finding}
                    </li>
                  ))}
                </ul>
              </div>

              <Separator />

              <div>
                <p className="text-foreground mb-2 text-sm font-medium">
                  Recommendations
                </p>
                <ul className="space-y-2">
                  {report.summary.recommendations.map((rec, idx) => (
                    <li
                      key={idx}
                      className="flex items-start gap-2 rounded-lg bg-blue-50 p-2 text-sm dark:bg-blue-900/10"
                    >
                      <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-blue-600" />
                      <span className="text-foreground">{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </CardContent>
          </Card>

          {/* Document Information */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Document Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <p className="text-muted-foreground text-xs font-medium">
                    FILENAME
                  </p>
                  <p className="text-foreground mt-1 text-sm">
                    {report.sections.documentInfo.filename}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs font-medium">
                    FILE TYPE
                  </p>
                  <p className="text-foreground mt-1 text-sm">
                    {report.sections.documentInfo.fileType}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs font-medium">
                    FILE SIZE
                  </p>
                  <p className="text-foreground mt-1 text-sm">
                    {(report.sections.documentInfo.fileSize / 1024 / 1024).toFixed(2)}{" "}
                    MB
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs font-medium">
                    UPLOADED BY
                  </p>
                  <p className="text-foreground mt-1 text-sm">
                    {report.sections.documentInfo.uploadedBy}
                  </p>
                </div>
                {report.sections.documentInfo.pageCount && (
                  <div>
                    <p className="text-muted-foreground text-xs font-medium">
                      PAGE COUNT
                    </p>
                    <p className="text-foreground mt-1 text-sm">
                      {report.sections.documentInfo.pageCount} pages
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Format Validation Results */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Format Validation</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-muted-foreground text-sm">
                    Validation Score
                  </p>
                  <p className="text-foreground mt-1 text-2xl font-bold">
                    {report.sections.formatValidation.score}/100
                  </p>
                </div>
                <Badge
                  variant={
                    report.sections.formatValidation.status === "pass"
                      ? "default"
                      : report.sections.formatValidation.status === "warning"
                        ? "secondary"
                        : "destructive"
                  }
                >
                  {report.sections.formatValidation.status.toUpperCase()}
                </Badge>
              </div>

              {report.sections.formatValidation.issues.length > 0 && (
                <div>
                  <p className="text-muted-foreground mb-2 text-sm font-medium">
                    Issues Found ({report.sections.formatValidation.issues.length})
                  </p>
                  <div className="space-y-2">
                    {report.sections.formatValidation.issues
                      .slice(0, 3)
                      .map((issue, idx) => (
                        <div
                          key={idx}
                          className="rounded-lg border border-border bg-background p-3"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1">
                              <p className="text-foreground text-sm font-medium">
                                {issue.type.charAt(0).toUpperCase() +
                                  issue.type.slice(1)}{" "}
                                Issue
                              </p>
                              <p className="text-muted-foreground mt-1 text-xs">
                                {issue.description}
                              </p>
                            </div>
                            <Badge
                              variant={
                                issue.severity === "high"
                                  ? "destructive"
                                  : "secondary"
                              }
                              className="text-xs"
                            >
                              {issue.severity}
                            </Badge>
                          </div>
                        </div>
                      ))}
                    {report.sections.formatValidation.issues.length > 3 && (
                      <p className="text-muted-foreground text-center text-xs">
                        +{report.sections.formatValidation.issues.length - 3} more
                        issues
                      </p>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Image Analysis Results */}
          {report.sections.imageAnalysis && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Image Analysis</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="rounded-lg border border-border p-3">
                    <p className="text-muted-foreground mb-2 text-xs font-medium">
                      AUTHENTICITY
                    </p>
                    <div className="flex items-center gap-2">
                      {report.sections.imageAnalysis.authenticity.isAuthentic ? (
                        <CheckCircle2 className="size-4 text-emerald-500" />
                      ) : (
                        <XCircle className="size-4 text-destructive" />
                      )}
                      <p className="text-foreground text-sm font-medium">
                        {report.sections.imageAnalysis.authenticity.isAuthentic
                          ? "Authentic"
                          : "Questionable"}
                      </p>
                    </div>
                  </div>

                  <div className="rounded-lg border border-border p-3">
                    <p className="text-muted-foreground mb-2 text-xs font-medium">
                      AI GENERATED
                    </p>
                    <div className="flex items-center gap-2">
                      {report.sections.imageAnalysis.aiDetection.isAIGenerated ? (
                        <AlertTriangle className="size-4 text-amber-500" />
                      ) : (
                        <CheckCircle2 className="size-4 text-emerald-500" />
                      )}
                      <p className="text-foreground text-sm font-medium">
                        {report.sections.imageAnalysis.aiDetection.isAIGenerated
                          ? "Likely AI"
                          : "Authentic"}
                      </p>
                    </div>
                  </div>

                  <div className="rounded-lg border border-border p-3">
                    <p className="text-muted-foreground mb-2 text-xs font-medium">
                      TAMPERING
                    </p>
                    <div className="flex items-center gap-2">
                      {report.sections.imageAnalysis.tampering.isTampered ? (
                        <XCircle className="size-4 text-destructive" />
                      ) : (
                        <CheckCircle2 className="size-4 text-emerald-500" />
                      )}
                      <p className="text-foreground text-sm font-medium">
                        {report.sections.imageAnalysis.tampering.isTampered
                          ? "Detected"
                          : "None"}
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Risk Assessment */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Risk Assessment</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-muted-foreground text-sm">
                    Overall Risk Score
                  </p>
                  <p className="text-foreground mt-1 text-2xl font-bold">
                    {report.sections.riskAssessment.overall}/100
                  </p>
                </div>
                <Badge
                  className={`text-sm ${getRiskColor(report.sections.riskAssessment.level)}`}
                >
                  {report.sections.riskAssessment.level.toUpperCase()} RISK
                </Badge>
              </div>

              <div className="rounded-lg border border-border bg-background p-4">
                <p className="text-foreground text-sm leading-relaxed">
                  {report.sections.riskAssessment.recommendation}
                </p>
              </div>

              {report.sections.riskAssessment.requiresReview && (
                <div className="flex items-center gap-2 rounded-lg border border-amber-300 bg-amber-50 p-3 dark:border-amber-900/30 dark:bg-amber-900/10">
                  <AlertTriangle className="size-5 text-amber-600" />
                  <p className="text-sm font-medium text-amber-900 dark:text-amber-200">
                    Manual review required for this document
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Next Steps */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Next Steps</CardTitle>
            </CardHeader>
            <CardContent>
              <ol className="space-y-2">
                {report.nextSteps.map((step, idx) => (
                  <li key={idx} className="flex items-start gap-3">
                    <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-medium text-primary-foreground">
                      {idx + 1}
                    </span>
                    <p className="text-foreground mt-0.5 text-sm">{step}</p>
                  </li>
                ))}
              </ol>
            </CardContent>
          </Card>
        </div>
      </DialogContent>
    </Dialog>
  );
}

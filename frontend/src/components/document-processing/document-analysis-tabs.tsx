"use client";

import {
  FileText,
  FileCheck,
  Image as ImageIcon,
  Shield,
  Info,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "~/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "~/components/ui/tabs";
import { Badge } from "~/components/ui/badge";
import { FormatValidationPanel } from "./format-validation-panel";
import { ImageAnalysisPanel } from "./image-analysis-panel";
import { RiskScoringCard } from "./risk-scoring-card";
import type { DocumentAnalysis } from "~/types/document-processing";

interface DocumentAnalysisTabsProps {
  analysis: DocumentAnalysis;
}

export function DocumentAnalysisTabs({ analysis }: DocumentAnalysisTabsProps) {
  const hasImage = !!analysis.imageAnalysis;
  const hasValidation = !!analysis.formatValidation;
  const hasRisk = !!analysis.riskScore;

  const getStatusBadge = (status: DocumentAnalysis["status"]) => {
    const variants: Record<
      DocumentAnalysis["status"],
      { variant: "default" | "secondary" | "destructive"; text: string }
    > = {
      pending: { variant: "secondary", text: "Pending" },
      uploading: { variant: "secondary", text: "Uploading" },
      processing: { variant: "secondary", text: "Processing" },
      completed: { variant: "default", text: "Completed" },
      failed: { variant: "destructive", text: "Failed" },
    };

    return (
      <Badge variant={variants[status].variant}>{variants[status].text}</Badge>
    );
  };

  return (
    <div className="space-y-6">
      {/* Document Info Header */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <FileText className="size-8 text-muted-foreground" />
              <div>
                <CardTitle>{analysis.metadata.filename}</CardTitle>
                <div className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
                  <span>{analysis.documentType.replace("_", " ")}</span>
                  <span>•</span>
                  <span>
                    {(analysis.metadata.fileSize / 1024 / 1024).toFixed(2)} MB
                  </span>
                  {analysis.metadata.pageCount && (
                    <>
                      <span>•</span>
                      <span>{analysis.metadata.pageCount} pages</span>
                    </>
                  )}
                </div>
              </div>
            </div>
            {getStatusBadge(analysis.status)}
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-lg border border-border p-3">
              <p className="text-muted-foreground mb-1 text-xs font-medium">
                UPLOADED BY
              </p>
              <p className="text-foreground text-sm font-medium">
                {analysis.metadata.uploadedBy}
              </p>
            </div>
            <div className="rounded-lg border border-border p-3">
              <p className="text-muted-foreground mb-1 text-xs font-medium">
                UPLOADED ON
              </p>
              <p className="text-foreground text-sm font-medium">
                {new Date(analysis.metadata.uploadedAt).toLocaleDateString()}
              </p>
            </div>
            {analysis.processingTime && (
              <div className="rounded-lg border border-border p-3">
                <p className="text-muted-foreground mb-1 text-xs font-medium">
                  PROCESSING TIME
                </p>
                <p className="text-foreground text-sm font-medium">
                  {(analysis.processingTime / 1000).toFixed(2)}s
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Analysis Tabs */}
      {analysis.status === "completed" && (
        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview">
              <Info className="mr-2 size-4" />
              Overview
            </TabsTrigger>
            {hasValidation && (
              <TabsTrigger value="validation">
                <FileCheck className="mr-2 size-4" />
                Validation
              </TabsTrigger>
            )}
            {hasImage && (
              <TabsTrigger value="image">
                <ImageIcon className="mr-2 size-4" />
                Image Analysis
              </TabsTrigger>
            )}
            {hasRisk && (
              <TabsTrigger value="risk">
                <Shield className="mr-2 size-4" />
                Risk Score
              </TabsTrigger>
            )}
            <TabsTrigger value="content">
              <FileText className="mr-2 size-4" />
              Content
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Analysis Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {hasValidation && analysis.formatValidation && (
                  <div className="rounded-lg border border-border bg-background p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-foreground mb-1 text-sm font-medium">
                          Format Validation
                        </p>
                        <p className="text-muted-foreground text-xs">
                          Document formatting and structure check
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-foreground text-2xl font-bold">
                          {analysis.formatValidation.score}
                        </p>
                        <p className="text-muted-foreground text-xs">Score</p>
                      </div>
                    </div>
                  </div>
                )}

                {hasImage && analysis.imageAnalysis && (
                  <div className="rounded-lg border border-border bg-background p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-foreground mb-1 text-sm font-medium">
                          Image Analysis
                        </p>
                        <p className="text-muted-foreground text-xs">
                          Authenticity, AI detection, and tampering
                        </p>
                      </div>
                      <Badge
                        className={
                          analysis.imageAnalysis.overallRisk === "low"
                            ? "bg-emerald-100 text-emerald-700"
                            : analysis.imageAnalysis.overallRisk === "medium"
                              ? "bg-amber-100 text-amber-700"
                              : "bg-destructive/10 text-destructive"
                        }
                      >
                        {analysis.imageAnalysis.overallRisk.toUpperCase()}
                      </Badge>
                    </div>
                  </div>
                )}

                {hasRisk && analysis.riskScore && (
                  <div className="rounded-lg border border-border bg-background p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-foreground mb-1 text-sm font-medium">
                          Overall Risk Score
                        </p>
                        <p className="text-muted-foreground text-xs">
                          Comprehensive risk assessment
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-foreground text-2xl font-bold">
                          {analysis.riskScore.overall}
                        </p>
                        <Badge
                          className={
                            analysis.riskScore.level === "low"
                              ? "bg-emerald-100 text-emerald-700"
                              : analysis.riskScore.level === "medium"
                                ? "bg-amber-100 text-amber-700"
                                : "bg-destructive/10 text-destructive"
                          }
                        >
                          {analysis.riskScore.level.toUpperCase()}
                        </Badge>
                      </div>
                    </div>
                  </div>
                )}

                {analysis.error && (
                  <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-4">
                    <p className="text-destructive text-sm font-medium">
                      Error: {analysis.error}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Audit Trail */}
            {analysis.auditTrail.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Audit Trail</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {analysis.auditTrail.map((entry, index) => (
                      <div
                        key={index}
                        className="flex items-start gap-3 border-l-2 border-border pl-4"
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <p className="text-foreground text-sm font-medium">
                              {entry.action}
                            </p>
                            <span className="text-muted-foreground text-xs">
                              by {entry.user}
                            </span>
                          </div>
                          <p className="text-muted-foreground mt-1 text-xs">
                            {entry.details}
                          </p>
                          <p className="text-muted-foreground mt-1 text-xs">
                            {new Date(entry.timestamp).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Format Validation Tab */}
          {hasValidation && analysis.formatValidation && (
            <TabsContent value="validation">
              <FormatValidationPanel validation={analysis.formatValidation} />
            </TabsContent>
          )}

          {/* Image Analysis Tab */}
          {hasImage && analysis.imageAnalysis && (
            <TabsContent value="image">
              <ImageAnalysisPanel analysis={analysis.imageAnalysis} />
            </TabsContent>
          )}

          {/* Risk Score Tab */}
          {hasRisk && analysis.riskScore && (
            <TabsContent value="risk">
              <RiskScoringCard riskScore={analysis.riskScore} />
            </TabsContent>
          )}

          {/* Content Tab */}
          <TabsContent value="content">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Extracted Content</CardTitle>
              </CardHeader>
              <CardContent>
                {analysis.contentExtraction ? (
                  <div className="space-y-4">
                    <div className="max-h-96 overflow-auto rounded-lg border border-border bg-background p-4">
                      <pre className="text-foreground whitespace-pre-wrap text-sm">
                        {analysis.contentExtraction.text}
                      </pre>
                    </div>

                    {analysis.contentExtraction.entities &&
                      analysis.contentExtraction.entities.length > 0 && (
                        <div>
                          <p className="text-foreground mb-2 text-sm font-medium">
                            Extracted Entities
                          </p>
                          <div className="flex flex-wrap gap-2">
                            {analysis.contentExtraction.entities.map(
                              (entity, idx) => (
                                <Badge key={idx} variant="outline">
                                  {entity.type}: {entity.value} (
                                  {(entity.confidence * 100).toFixed(0)}%)
                                </Badge>
                              ),
                            )}
                          </div>
                        </div>
                      )}
                  </div>
                ) : (
                  <p className="text-muted-foreground text-center text-sm">
                    No content extracted from this document
                  </p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}

      {/* Processing/Error State */}
      {analysis.status !== "completed" && (
        <Card>
          <CardContent className="flex min-h-64 items-center justify-center py-12">
            <div className="text-center">
              {analysis.status === "failed" ? (
                <>
                  <FileText className="text-destructive/30 mx-auto mb-4 size-12" />
                  <p className="text-foreground mb-2 font-medium">
                    Analysis Failed
                  </p>
                  <p className="text-muted-foreground text-sm">
                    {analysis.error || "An error occurred during analysis"}
                  </p>
                </>
              ) : (
                <>
                  <FileText className="text-muted-foreground/30 mx-auto mb-4 size-12 animate-pulse" />
                  <p className="text-foreground mb-2 font-medium">
                    {analysis.status === "uploading"
                      ? "Uploading document..."
                      : "Processing document..."}
                  </p>
                  <p className="text-muted-foreground text-sm">
                    Please wait while we analyze your document
                  </p>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

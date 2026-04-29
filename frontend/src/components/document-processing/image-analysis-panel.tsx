"use client";

import {
  AlertTriangle,
  Calendar,
  Camera,
  CheckCircle2,
  Cpu,
  Image as ImageIcon,
  Info,
  Search,
  Shield,
  ShieldAlert,
  Sparkles,
  XCircle,
} from "lucide-react";
import { Badge } from "~/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "~/components/ui/card";
import { Progress } from "~/components/ui/progress";
import type {
  ImageAnalysisResult,
  RiskLevel,
} from "~/types/document-processing";

interface ImageAnalysisPanelProps {
  analysis: ImageAnalysisResult;
}

export function ImageAnalysisPanel({ analysis }: ImageAnalysisPanelProps) {
  const getRiskColor = (risk: RiskLevel) => {
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

  const getRiskIcon = (risk: RiskLevel) => {
    switch (risk) {
      case "low":
        return <Shield className="size-5 text-emerald-500" />;
      case "medium":
        return <ShieldAlert className="size-5 text-amber-500" />;
      case "high":
        return <AlertTriangle className="size-5 text-orange-500" />;
      case "critical":
        return <XCircle className="text-destructive size-5" />;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return "bg-emerald-500";
    if (confidence >= 0.6) return "bg-amber-500";
    return "bg-destructive";
  };

  return (
    <div className="space-y-4">
      {/* Overall Risk Card */}
      <Card
        className={`border-2 ${
          analysis.overallRisk === "low"
            ? "border-emerald-200 bg-emerald-50 dark:border-emerald-900/30 dark:bg-emerald-900/10"
            : analysis.overallRisk === "medium"
              ? "border-amber-200 bg-amber-50 dark:border-amber-900/30 dark:bg-amber-900/10"
              : "border-destructive/20 bg-destructive/5"
        }`}
      >
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {getRiskIcon(analysis.overallRisk)}
              <div>
                <h3 className="text-foreground text-lg font-semibold">
                  Image Analysis
                </h3>
                <p className="text-muted-foreground text-sm">
                  Overall risk assessment
                </p>
              </div>
            </div>
            <Badge className={`text-sm ${getRiskColor(analysis.overallRisk)}`}>
              {analysis.overallRisk.toUpperCase()} RISK
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Authenticity Check */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Search className="size-5" />
            Authenticity Verification
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {analysis.authenticity.isAuthentic ? (
                <CheckCircle2 className="size-5 text-emerald-500" />
              ) : (
                <XCircle className="text-destructive size-5" />
              )}
              <span className="text-foreground text-sm font-medium">
                {analysis.authenticity.isAuthentic
                  ? "Image appears authentic"
                  : "Image authenticity questionable"}
              </span>
            </div>
            <Badge
              variant={
                analysis.authenticity.isAuthentic ? "default" : "destructive"
              }
            >
              {(analysis.authenticity.confidence * 100).toFixed(0)}% confident
            </Badge>
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Confidence Level</span>
              <span className="text-foreground font-medium">
                {(analysis.authenticity.confidence * 100).toFixed(1)}%
              </span>
            </div>
            <Progress
              value={analysis.authenticity.confidence * 100}
              className="h-2"
              // @ts-expect-error - custom color prop
              indicatorClassName={getConfidenceColor(
                analysis.authenticity.confidence,
              )}
            />
          </div>

          <div className="border-border bg-background rounded-lg border p-3">
            <div className="flex items-center gap-2 text-sm">
              <Info className="text-muted-foreground size-4" />
              <span className="text-muted-foreground">
                Reverse image search results:
              </span>
              <span className="text-foreground font-medium">
                {analysis.authenticity.reverseImageSearchResults} matches found
              </span>
            </div>
            {analysis.authenticity.matchingSources &&
              analysis.authenticity.matchingSources.length > 0 && (
                <div className="mt-2 space-y-1">
                  <p className="text-muted-foreground text-xs font-medium">
                    Matching sources:
                  </p>
                  {analysis.authenticity.matchingSources.map((source, idx) => (
                    <p
                      key={idx}
                      className="text-xs text-blue-600 dark:text-blue-400"
                    >
                      • {source}
                    </p>
                  ))}
                </div>
              )}
          </div>
        </CardContent>
      </Card>

      {/* AI Detection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Sparkles className="size-5" />
            AI-Generated Detection
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {analysis.aiDetection.isAIGenerated ? (
                <AlertTriangle className="size-5 text-amber-500" />
              ) : (
                <CheckCircle2 className="size-5 text-emerald-500" />
              )}
              <span className="text-foreground text-sm font-medium">
                {analysis.aiDetection.isAIGenerated
                  ? "Likely AI-generated"
                  : "Appears to be authentic photo"}
              </span>
            </div>
            <Badge
              variant={
                analysis.aiDetection.isAIGenerated ? "destructive" : "default"
              }
            >
              {(analysis.aiDetection.confidence * 100).toFixed(0)}% confident
            </Badge>
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between text-sm">
              <span className="text-muted-foreground">
                Detection Confidence
              </span>
              <span className="text-foreground font-medium">
                {(analysis.aiDetection.confidence * 100).toFixed(1)}%
              </span>
            </div>
            <Progress
              value={analysis.aiDetection.confidence * 100}
              className="h-2"
              // @ts-expect-error - custom color prop
              indicatorClassName={getConfidenceColor(
                analysis.aiDetection.confidence,
              )}
            />
          </div>

          {analysis.aiDetection.indicators.length > 0 && (
            <div className="space-y-2">
              <p className="text-muted-foreground text-sm font-medium">
                AI Indicators Detected:
              </p>
              {analysis.aiDetection.indicators.map((indicator, idx) => (
                <div
                  key={idx}
                  className="border-border bg-background flex items-start gap-2 rounded-lg border p-2"
                >
                  <AlertTriangle className="mt-0.5 size-4 text-amber-500" />
                  <p className="text-foreground text-xs">{indicator}</p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Tampering Detection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Camera className="size-5" />
            Tampering Detection
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {analysis.tampering.isTampered ? (
                <XCircle className="text-destructive size-5" />
              ) : (
                <CheckCircle2 className="size-5 text-emerald-500" />
              )}
              <span className="text-foreground text-sm font-medium">
                {analysis.tampering.isTampered
                  ? "Tampering detected"
                  : "No tampering detected"}
              </span>
            </div>
            <Badge
              variant={
                analysis.tampering.isTampered ? "destructive" : "default"
              }
            >
              {(analysis.tampering.confidence * 100).toFixed(0)}% confident
            </Badge>
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Analysis Confidence</span>
              <span className="text-foreground font-medium">
                {(analysis.tampering.confidence * 100).toFixed(1)}%
              </span>
            </div>
            <Progress
              value={analysis.tampering.confidence * 100}
              className="h-2"
              // @ts-expect-error - custom color prop
              indicatorClassName={getConfidenceColor(
                analysis.tampering.confidence,
              )}
            />
          </div>

          {analysis.tampering.anomalies.length > 0 && (
            <div className="space-y-2">
              <p className="text-muted-foreground text-sm font-medium">
                Anomalies Detected ({analysis.tampering.anomalies.length}):
              </p>
              {analysis.tampering.anomalies.map((anomaly, idx) => (
                <div
                  key={idx}
                  className="border-border bg-background rounded-lg border p-3"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <p className="text-foreground mb-1 text-sm font-medium">
                        {anomaly.type.charAt(0).toUpperCase() +
                          anomaly.type.slice(1)}{" "}
                        Anomaly
                      </p>
                      <p className="text-muted-foreground text-xs">
                        {anomaly.description}
                      </p>
                    </div>
                    <Badge
                      className={`text-xs ${getRiskColor(anomaly.severity)}`}
                    >
                      {anomaly.severity}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Forensic Analysis */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <ImageIcon className="size-5" />
            Forensic Analysis
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* File Metadata */}
          <div>
            <p className="text-muted-foreground mb-2 text-sm font-medium">
              File Metadata
            </p>
            <div className="border-border bg-background grid gap-2 rounded-lg border p-3 md:grid-cols-2">
              {analysis.forensic.fileMetadata.createdDate && (
                <div className="flex items-center gap-2">
                  <Calendar className="text-muted-foreground size-4" />
                  <div className="text-xs">
                    <span className="text-muted-foreground">Created: </span>
                    <span className="text-foreground">
                      {new Date(
                        analysis.forensic.fileMetadata.createdDate,
                      ).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              )}
              {analysis.forensic.fileMetadata.modifiedDate && (
                <div className="flex items-center gap-2">
                  <Calendar className="text-muted-foreground size-4" />
                  <div className="text-xs">
                    <span className="text-muted-foreground">Modified: </span>
                    <span className="text-foreground">
                      {new Date(
                        analysis.forensic.fileMetadata.modifiedDate,
                      ).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              )}
              {analysis.forensic.fileMetadata.software && (
                <div className="flex items-center gap-2">
                  <Cpu className="text-muted-foreground size-4" />
                  <div className="text-xs">
                    <span className="text-muted-foreground">Software: </span>
                    <span className="text-foreground">
                      {analysis.forensic.fileMetadata.software}
                    </span>
                  </div>
                </div>
              )}
              {analysis.forensic.fileMetadata.device && (
                <div className="flex items-center gap-2">
                  <Camera className="text-muted-foreground size-4" />
                  <div className="text-xs">
                    <span className="text-muted-foreground">Device: </span>
                    <span className="text-foreground">
                      {analysis.forensic.fileMetadata.device}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Pixel Analysis */}
          <div>
            <p className="text-muted-foreground mb-2 text-sm font-medium">
              Pixel Analysis
            </p>
            <div className="border-border bg-background rounded-lg border p-3">
              <div className="mb-2 flex items-center justify-between text-sm">
                <span className="text-muted-foreground">
                  Inconsistencies Found
                </span>
                <span className="text-foreground font-medium">
                  {analysis.forensic.pixelAnalysis.inconsistencies}
                </span>
              </div>
              {analysis.forensic.pixelAnalysis.suspiciousRegions.length > 0 && (
                <div className="mt-2">
                  <p className="text-muted-foreground text-xs font-medium">
                    Suspicious regions:
                  </p>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {analysis.forensic.pixelAnalysis.suspiciousRegions.map(
                      (region, idx) => (
                        <Badge key={idx} variant="outline" className="text-xs">
                          {region}
                        </Badge>
                      ),
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Compression Analysis */}
          <div>
            <p className="text-muted-foreground mb-2 text-sm font-medium">
              Compression Analysis
            </p>
            <div className="border-border bg-background rounded-lg border p-3">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-foreground text-sm">
                  Multiple Compression Detected
                </span>
                {analysis.forensic.compressionAnalysis.multipleCompression ? (
                  <AlertTriangle className="size-4 text-amber-500" />
                ) : (
                  <CheckCircle2 className="size-4 text-emerald-500" />
                )}
              </div>
              {analysis.forensic.compressionAnalysis.artifacts.length > 0 && (
                <div className="mt-2">
                  <p className="text-muted-foreground text-xs font-medium">
                    Artifacts:
                  </p>
                  <ul className="mt-1 space-y-1">
                    {analysis.forensic.compressionAnalysis.artifacts.map(
                      (artifact, idx) => (
                        <li key={idx} className="text-foreground text-xs">
                          • {artifact}
                        </li>
                      ),
                    )}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

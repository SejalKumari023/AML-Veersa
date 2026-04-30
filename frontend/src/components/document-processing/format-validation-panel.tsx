"use client";

import {
  AlertTriangle,
  AlignLeft,
  CheckCircle2,
  FileCheck,
  FileText,
  Heading,
  List,
  Type,
  XCircle,
} from "lucide-react";
import { Badge } from "~/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "~/components/ui/card";
import { Progress } from "~/components/ui/progress";
import type {
  FormatIssue,
  FormatValidationResult,
  ValidationStatus,
} from "~/types/document-processing";

interface FormatValidationPanelProps {
  validation: FormatValidationResult;
}

export function FormatValidationPanel({
  validation,
}: FormatValidationPanelProps) {
  const getStatusIcon = (status: ValidationStatus) => {
    switch (status) {
      case "pass":
        return <CheckCircle2 className="size-5 text-emerald-500" />;
      case "warning":
        return <AlertTriangle className="size-5 text-amber-500" />;
      case "fail":
        return <XCircle className="text-destructive size-5" />;
    }
  };

  const getStatusColor = (status: ValidationStatus) => {
    switch (status) {
      case "pass":
        return "text-emerald-600 bg-emerald-100 dark:bg-emerald-900/20";
      case "warning":
        return "text-amber-600 bg-amber-100 dark:bg-amber-900/20";
      case "fail":
        return "text-destructive bg-destructive/10";
    }
  };

  const getSeverityBadge = (severity: FormatIssue["severity"]) => {
    const variants: Record<
      FormatIssue["severity"],
      { variant: "default" | "secondary" | "destructive"; className: string }
    > = {
      low: {
        variant: "secondary",
        className: "bg-blue-100 text-blue-700 dark:bg-blue-900/20",
      },
      medium: {
        variant: "secondary",
        className: "bg-amber-100 text-amber-700 dark:bg-amber-900/20",
      },
      high: { variant: "destructive", className: "" },
    };

    return (
      <Badge
        variant={variants[severity].variant}
        className={`text-xs ${variants[severity].className}`}
      >
        {severity}
      </Badge>
    );
  };

  const getIssueIcon = (type: FormatIssue["type"]) => {
    const icons = {
      spacing: AlignLeft,
      font: Type,
      indentation: AlignLeft,
      spelling: FileText,
      header: Heading,
      section: List,
    };
    const Icon = icons[type] || FileText;
    return <Icon className="text-muted-foreground size-4" />;
  };

  const getCheckIcon = (passed: boolean) => {
    return passed ? (
      <CheckCircle2 className="size-4 text-emerald-500" />
    ) : (
      <XCircle className="text-destructive size-4" />
    );
  };

  return (
    <div className="space-y-4">
      {/* Overall Status Card */}
      <Card
        className={`border-2 ${validation.status === "pass" ? "border-emerald-200 bg-emerald-50 dark:border-emerald-900/30 dark:bg-emerald-900/10" : validation.status === "warning" ? "border-amber-200 bg-amber-50 dark:border-amber-900/30 dark:bg-amber-900/10" : "border-destructive/20 bg-destructive/5"}`}
      >
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {getStatusIcon(validation.status)}
              <div>
                <h3 className="text-foreground text-lg font-semibold">
                  Format Validation
                </h3>
                <p className="text-muted-foreground text-sm">
                  {validation.status === "pass"
                    ? "All checks passed"
                    : validation.status === "warning"
                      ? "Some issues detected"
                      : "Critical issues found"}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-foreground text-3xl font-bold">
                {validation.score}
              </p>
              <p className="text-muted-foreground text-xs">Score</p>
            </div>
          </div>
          <Progress
            value={validation.score}
            className="mt-4 h-2"
            // @ts-expect-error - custom color prop
            indicatorClassName={
              validation.score >= 80
                ? "bg-emerald-500"
                : validation.score >= 60
                  ? "bg-amber-500"
                  : "bg-destructive"
            }
          />
        </CardContent>
      </Card>

      {/* Validation Checks */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <FileCheck className="size-5" />
            Validation Checks
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="grid gap-2 md:grid-cols-2">
            <div className="border-border flex items-center justify-between rounded-lg border p-3">
              <div className="flex items-center gap-2">
                {getCheckIcon(validation.checks.spacing)}
                <span className="text-foreground text-sm">Spacing</span>
              </div>
              <Badge
                variant={validation.checks.spacing ? "default" : "destructive"}
                className="text-xs"
              >
                {validation.checks.spacing ? "Pass" : "Fail"}
              </Badge>
            </div>

            <div className="border-border flex items-center justify-between rounded-lg border p-3">
              <div className="flex items-center gap-2">
                {getCheckIcon(validation.checks.fonts)}
                <span className="text-foreground text-sm">Fonts</span>
              </div>
              <Badge
                variant={validation.checks.fonts ? "default" : "destructive"}
                className="text-xs"
              >
                {validation.checks.fonts ? "Pass" : "Fail"}
              </Badge>
            </div>

            <div className="border-border flex items-center justify-between rounded-lg border p-3">
              <div className="flex items-center gap-2">
                {getCheckIcon(validation.checks.indentation)}
                <span className="text-foreground text-sm">Indentation</span>
              </div>
              <Badge
                variant={
                  validation.checks.indentation ? "default" : "destructive"
                }
                className="text-xs"
              >
                {validation.checks.indentation ? "Pass" : "Fail"}
              </Badge>
            </div>

            <div className="border-border flex items-center justify-between rounded-lg border p-3">
              <div className="flex items-center gap-2">
                {getCheckIcon(validation.checks.spelling)}
                <span className="text-foreground text-sm">Spelling</span>
              </div>
              <Badge
                variant={validation.checks.spelling ? "default" : "destructive"}
                className="text-xs"
              >
                {validation.checks.spelling ? "Pass" : "Fail"}
              </Badge>
            </div>

            <div className="border-border flex items-center justify-between rounded-lg border p-3">
              <div className="flex items-center gap-2">
                {getCheckIcon(validation.checks.headers)}
                <span className="text-foreground text-sm">Headers</span>
              </div>
              <Badge
                variant={validation.checks.headers ? "default" : "destructive"}
                className="text-xs"
              >
                {validation.checks.headers ? "Pass" : "Fail"}
              </Badge>
            </div>

            <div className="border-border flex items-center justify-between rounded-lg border p-3">
              <div className="flex items-center gap-2">
                {getCheckIcon(validation.checks.completeness)}
                <span className="text-foreground text-sm">Completeness</span>
              </div>
              <Badge
                variant={
                  validation.checks.completeness ? "default" : "destructive"
                }
                className="text-xs"
              >
                {validation.checks.completeness ? "Pass" : "Fail"}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Issues List */}
      {validation.issues.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Issues Found ({validation.issues.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {validation.issues.map((issue, index) => (
              <div
                key={index}
                className="border-border bg-background rounded-lg border p-3"
              >
                <div className="flex items-start gap-3">
                  {getIssueIcon(issue.type)}
                  <div className="flex-1 space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-foreground text-sm font-medium">
                          {issue.type.charAt(0).toUpperCase() +
                            issue.type.slice(1)}{" "}
                          Issue
                        </p>
                        <p className="text-muted-foreground mt-1 text-xs">
                          {issue.description}
                        </p>
                      </div>
                      {getSeverityBadge(issue.severity)}
                    </div>
                    <div className="text-muted-foreground flex items-center gap-4 text-xs">
                      <span>Location: {issue.location}</span>
                    </div>
                    {issue.suggestion && (
                      <div className="rounded-md bg-blue-50 p-2 dark:bg-blue-900/10">
                        <p className="text-xs text-blue-700 dark:text-blue-300">
                          <strong>Suggestion:</strong> {issue.suggestion}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {validation.issues.length === 0 && validation.status === "pass" && (
        <Card className="border-emerald-200 bg-emerald-50 dark:border-emerald-900/30 dark:bg-emerald-900/10">
          <CardContent className="py-8 text-center">
            <CheckCircle2 className="mx-auto mb-3 size-12 text-emerald-500" />
            <p className="text-foreground font-medium">
              No issues detected in this document
            </p>
            <p className="text-muted-foreground mt-1 text-sm">
              The document passes all format validation checks
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

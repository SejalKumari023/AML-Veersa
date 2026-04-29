"use client";

import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Shield,
  TrendingDown,
  TrendingUp,
  XCircle,
} from "lucide-react";
import { Badge } from "~/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "~/components/ui/card";
import { Progress } from "~/components/ui/progress";
import type {
  RiskLevel,
  RiskScore,
  ValidationStatus,
} from "~/types/document-processing";

interface RiskScoringCardProps {
  riskScore: RiskScore;
  showRecommendations?: boolean;
}

export function RiskScoringCard({
  riskScore,
  showRecommendations = true,
}: RiskScoringCardProps) {
  const getRiskColor = (level: RiskLevel) => {
    switch (level) {
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

  const getRiskIcon = (level: RiskLevel) => {
    switch (level) {
      case "low":
        return <CheckCircle2 className="size-8 text-emerald-500" />;
      case "medium":
        return <AlertTriangle className="size-8 text-amber-500" />;
      case "high":
        return <AlertCircle className="size-8 text-orange-500" />;
      case "critical":
        return <XCircle className="text-destructive size-8" />;
    }
  };

  const getScoreColor = (score: number) => {
    if (score <= 30) return "bg-emerald-500";
    if (score <= 60) return "bg-amber-500";
    if (score <= 80) return "bg-orange-500";
    return "bg-destructive";
  };

  const getStatusIcon = (status: ValidationStatus) => {
    switch (status) {
      case "pass":
        return <CheckCircle2 className="size-4 text-emerald-500" />;
      case "warning":
        return <AlertTriangle className="size-4 text-amber-500" />;
      case "fail":
        return <XCircle className="text-destructive size-4" />;
    }
  };

  const getTrendIcon = (score: number) => {
    if (score <= 30) {
      return <TrendingDown className="size-5 text-emerald-500" />;
    }
    return <TrendingUp className="text-destructive size-5" />;
  };

  return (
    <div className="space-y-4">
      {/* Overall Risk Score */}
      <Card
        className={`border-2 ${
          riskScore.level === "low"
            ? "border-emerald-200 bg-emerald-50 dark:border-emerald-900/30 dark:bg-emerald-900/10"
            : riskScore.level === "medium"
              ? "border-amber-200 bg-amber-50 dark:border-amber-900/30 dark:bg-amber-900/10"
              : "border-destructive/20 bg-destructive/5"
        }`}
      >
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {getRiskIcon(riskScore.level)}
              <div>
                <h3 className="text-foreground mb-1 text-2xl font-bold">
                  Risk Score: {riskScore.overall}
                </h3>
                <Badge className={`${getRiskColor(riskScore.level)}`}>
                  {riskScore.level.toUpperCase()} RISK
                </Badge>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {getTrendIcon(riskScore.overall)}
              <Shield className="text-muted-foreground/20 size-12" />
            </div>
          </div>

          <div className="mt-6">
            <div className="mb-2 flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Risk Level</span>
              <span className="text-foreground font-medium">
                {riskScore.overall}/100
              </span>
            </div>
            <Progress
              value={riskScore.overall}
              className="h-3"
              // @ts-expect-error - custom color prop
              indicatorClassName={getScoreColor(riskScore.overall)}
            />
          </div>

          {riskScore.requiresReview && (
            <div className="mt-4 flex items-center gap-2 rounded-lg border border-amber-300 bg-amber-50 p-3 dark:border-amber-900/30 dark:bg-amber-900/10">
              <AlertTriangle className="size-5 text-amber-600" />
              <p className="text-sm font-medium text-amber-900 dark:text-amber-200">
                Manual review required
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Risk Factors Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Risk Factors Breakdown</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {riskScore.factors.map((factor, index) => (
            <div key={index} className="space-y-2">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  {getStatusIcon(factor.status)}
                  <div>
                    <p className="text-foreground text-sm font-medium">
                      {factor.category}
                    </p>
                    <p className="text-muted-foreground text-xs">
                      {factor.description}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge
                    variant={
                      factor.status === "pass"
                        ? "default"
                        : factor.status === "warning"
                          ? "secondary"
                          : "destructive"
                    }
                    className="text-xs"
                  >
                    {factor.score}/100
                  </Badge>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Progress
                  value={factor.score}
                  className="h-2 flex-1"
                  // @ts-expect-error - custom color prop
                  indicatorClassName={getScoreColor(factor.score)}
                />
                <span className="text-muted-foreground text-xs">
                  Weight: {(factor.weight * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Recommendation */}
      {showRecommendations && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recommendation</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="border-border bg-background rounded-lg border p-4">
              <p className="text-foreground text-sm leading-relaxed">
                {riskScore.recommendation}
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

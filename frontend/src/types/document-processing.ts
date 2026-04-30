// Type definitions for document processing system

export type DocumentType =
  | "passport"
  | "utility_bill"
  | "company_registration"
  | "bank_statement"
  | "contract"
  | "regulatory_notice"
  | "policy_document"
  | "other";

export type ProcessingStatus =
  | "pending"
  | "uploading"
  | "processing"
  | "completed"
  | "failed";

export type RiskLevel = "low" | "medium" | "high" | "critical";

export type ValidationStatus = "pass" | "warning" | "fail";

// Format Validation Types
export interface FormatIssue {
  type: "spacing" | "font" | "indentation" | "spelling" | "header" | "section";
  severity: "low" | "medium" | "high";
  description: string;
  location: string;
  suggestion?: string;
}

export interface FormatValidationResult {
  status: ValidationStatus;
  score: number; // 0-100
  issues: FormatIssue[];
  checks: {
    spacing: boolean;
    fonts: boolean;
    indentation: boolean;
    spelling: boolean;
    headers: boolean;
    completeness: boolean;
  };
}

// Image Analysis Types
export interface ImageAuthenticityResult {
  isAuthentic: boolean;
  confidence: number; // 0-1
  reverseImageSearchResults: number;
  matchingSources?: string[];
}

export interface AIGeneratedDetection {
  isAIGenerated: boolean;
  confidence: number; // 0-1
  indicators: string[];
}

export interface TamperingDetection {
  isTampered: boolean;
  confidence: number; // 0-1
  anomalies: {
    type: "metadata" | "pixel" | "compression" | "lighting";
    description: string;
    severity: RiskLevel;
  }[];
}

export interface ForensicAnalysis {
  fileMetadata: {
    createdDate?: string;
    modifiedDate?: string;
    software?: string;
    device?: string;
  };
  pixelAnalysis: {
    inconsistencies: number;
    suspiciousRegions: string[];
  };
  compressionAnalysis: {
    multipleCompression: boolean;
    artifacts: string[];
  };
}

export interface ImageAnalysisResult {
  authenticity: ImageAuthenticityResult;
  aiDetection: AIGeneratedDetection;
  tampering: TamperingDetection;
  forensic: ForensicAnalysis;
  overallRisk: RiskLevel;
}

// Risk Scoring Types
export interface RiskFactor {
  category: string;
  score: number; // 0-100
  weight: number; // 0-1
  description: string;
  status: ValidationStatus;
}

export interface RiskScore {
  overall: number; // 0-100
  level: RiskLevel;
  factors: RiskFactor[];
  recommendation: string;
  requiresReview: boolean;
}

// Document Analysis Types
export interface DocumentMetadata {
  filename: string;
  fileSize: number;
  fileType: string;
  mimeType: string;
  uploadedAt: string;
  uploadedBy: string;
  pageCount?: number;
}

export interface ContentExtraction {
  text: string;
  structuredData?: Record<string, unknown>;
  entities?: {
    type: "person" | "organization" | "date" | "amount" | "location";
    value: string;
    confidence: number;
  }[];
}

export interface DocumentAnalysis {
  id: string;
  documentType: DocumentType;
  status: ProcessingStatus;
  metadata: DocumentMetadata;
  contentExtraction?: ContentExtraction;
  formatValidation?: FormatValidationResult;
  imageAnalysis?: ImageAnalysisResult;
  riskScore?: RiskScore;
  processingTime?: number; // milliseconds
  error?: string;
  auditTrail: AuditEntry[];
}

// Audit Trail Types
export interface AuditEntry {
  timestamp: string;
  action: string;
  user: string;
  details: string;
}

// Upload Types
export interface UploadProgress {
  fileId: string;
  filename: string;
  progress: number; // 0-100
  status: ProcessingStatus;
  error?: string;
}

// Analysis Report Types
export interface AnalysisReport {
  documentId: string;
  generatedAt: string;
  summary: {
    overallStatus: ValidationStatus;
    riskLevel: RiskLevel;
    keyFindings: string[];
    recommendations: string[];
  };
  sections: {
    documentInfo: DocumentMetadata;
    formatValidation: FormatValidationResult;
    imageAnalysis?: ImageAnalysisResult;
    riskAssessment: RiskScore;
  };
  nextSteps: string[];
}

"use client"

import { useState, useEffect, useCallback } from "react"
import {
    Upload,
    FileText,
    AlertCircle,
    CheckCircle2,
    Clock,
    Download,
    Trash2,
    Eye,
    RefreshCw,
    User,
    Shield,
    AlertTriangle
} from "lucide-react"
import { useRouter } from "next/navigation"
import { getUser, getUserTypeLabel } from "~/lib/auth"
import {
    Card,
    CardHeader,
    CardTitle,
    CardDescription,
    CardContent,
} from "~/components/ui/card"
import { Button } from "~/components/ui/button"
import { env } from "~/env"

const BACKEND_2_API_URL = env.NEXT_PUBLIC_API_URL_2 || "http://localhost:5002/api"

interface DocumentAnalysis {
    id: string
    filename: string
    file_type: string
    upload_timestamp: string
    analysis_status: "queued" | "processing" | "completed" | "failed"
    risk_score?: number
    findings?: Finding[]
    metadata?: {
        total_pages?: number
        total_issues?: number
        errors?: number
        warnings?: number
    }
    error_message?: string
}

interface Finding {
    category: string
    severity: "error" | "warning" | "info"
    type: string
    description: string
    location?: any
    suggestions?: string[]
}

export default function DocumentsPage() {
    const router = useRouter()
    const [currentUser, setCurrentUser] = useState<{ name: string; email: string; userType: string } | null>(null)
    const [documents, setDocuments] = useState<DocumentAnalysis[]>([])
    const [selectedDocument, setSelectedDocument] = useState<DocumentAnalysis | null>(null)
    const [isUploading, setIsUploading] = useState(false)
    const [uploadError, setUploadError] = useState<string | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [uploadedDocId, setUploadedDocId] = useState<string | null>(null)

    useEffect(() => {
        const user = getUser()
        if (!user) {
            router.replace("/auth/login")
        } else {
            setCurrentUser({
                name: user.name,
                email: user.email,
                userType: getUserTypeLabel(user.userType)
            })
        }
    }, [router])

    const fetchDocuments = useCallback(async () => {
        try {
            const response = await fetch(`${BACKEND_2_API_URL}/documents/analysis`)
            if (!response.ok) {
                throw new Error(`Failed to fetch documents: ${response.statusText}`)
            }
            const data = await response.json()
            setDocuments(data)
        } catch (err) {
            console.error("Error fetching documents:", err)
        } finally {
            setIsLoading(false)
        }
    }, [])

    useEffect(() => {
        void fetchDocuments()
        const interval = setInterval(fetchDocuments, 5000)
        return () => clearInterval(interval)
    }, [fetchDocuments])

    const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0]
        if (!file) return

        setIsUploading(true)
        setUploadError(null)

        try {
            const formData = new FormData()
            formData.append("file", file)

            console.log("Uploading file:", file.name, "Size:", file.size, "Type:", file.type)
            console.log("Uploading to:", `${BACKEND_2_API_URL}/documents/upload`)

            const response = await fetch(`${BACKEND_2_API_URL}/documents/upload`, {
                method: "POST",
                body: formData,
                // Note: Do NOT set Content-Type header - browser will set it automatically with boundary
            })

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: response.statusText }))
                throw new Error(errorData.detail || `Upload failed: ${response.statusText}`)
            }

            const result = await response.json()
            console.log("Upload successful:", result)

            // Get the document_id from the response and store it
            const documentId = result.document_id
            if (documentId) {
                setUploadedDocId(documentId)

                // Fetch the specific document details and select it
                try {
                    const docResponse = await fetch(`${BACKEND_2_API_URL}/documents/analysis/${documentId}`)
                    if (docResponse.ok) {
                        const docData = await docResponse.json()
                        setSelectedDocument(docData)
                        console.log("Document details fetched:", docData)
                    }
                } catch (error) {
                    console.error("Error fetching document details:", error)
                }
            }
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : "Unknown error occurred"
            setUploadError(errorMessage)
            console.error("Error uploading file:", err)
        } finally {
            setIsUploading(false)
            // Reset the input
            event.target.value = ""
        }
    }

    const handleDeleteDocument = async (documentId: string) => {
        if (!confirm("Are you sure you want to delete this document?")) return

        try {
            const response = await fetch(`${BACKEND_2_API_URL}/documents/analysis/${documentId}`, {
                method: "DELETE",
            })

            if (!response.ok) {
                throw new Error(`Failed to delete document: ${response.statusText}`)
            }

            // Remove from local state
            setDocuments(documents.filter(doc => doc.id !== documentId))
            if (selectedDocument?.id === documentId) {
                setSelectedDocument(null)
            }
        } catch (err) {
            console.error("Error deleting document:", err)
            alert("Failed to delete document")
        }
    }

    const handleDownload = async (documentId: string, format: "markdown" | "json") => {
        try {
            const response = await fetch(`${BACKEND_2_API_URL}/documents/download/${documentId}/${format}`)

            if (response.status === 202) {
                alert("Document is still being processed. Please wait and try again.")
                return
            }

            if (!response.ok) {
                throw new Error(`Failed to download: ${response.statusText}`)
            }

            // Get the blob
            const blob = await response.blob()

            // Create download link
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement("a")
            a.href = url

            // Get filename from Content-Disposition header or use default
            const contentDisposition = response.headers.get("Content-Disposition")
            const filenameMatch = contentDisposition?.match(/filename="(.+)"/)
            const filename = filenameMatch?.[1] || `document.${format}`

            a.download = filename
            document.body.appendChild(a)
            a.click()
            window.URL.revokeObjectURL(url)
            document.body.removeChild(a)
        } catch (err) {
            console.error("Error downloading file:", err)
            alert("Failed to download file")
        }
    }

    const getStatusIcon = (status: DocumentAnalysis["analysis_status"]) => {
        switch (status) {
            case "completed":
                return <CheckCircle2 className="size-4 text-emerald-500" />
            case "failed":
                return <AlertCircle className="size-4 text-destructive" />
            case "processing":
            case "queued":
                return <Clock className="size-4 text-amber-500 animate-pulse" />
            default:
                return <Clock className="size-4 text-muted-foreground" />
        }
    }

    const getRiskColor = (riskScore: number) => {
        if (riskScore < 0.3) return "text-emerald-600 bg-emerald-100 dark:bg-emerald-900/20"
        if (riskScore < 0.7) return "text-amber-600 bg-amber-100 dark:bg-amber-900/20"
        return "text-destructive bg-destructive/10"
    }

    const getRiskLabel = (riskScore: number) => {
        if (riskScore < 0.3) return "Low Risk"
        if (riskScore < 0.7) return "Medium Risk"
        return "High Risk"
    }

    const getSeverityIcon = (severity: Finding["severity"]) => {
        switch (severity) {
            case "error":
                return <AlertCircle className="size-4 text-destructive" />
            case "warning":
                return <AlertTriangle className="size-4 text-amber-500" />
            case "info":
                return <Shield className="size-4 text-blue-500" />
        }
    }

    const totalDocuments = documents.length
    const completedDocuments = documents.filter(d => d.analysis_status === "completed").length
    const processingDocuments = documents.filter(d =>
        d.analysis_status === "processing" || d.analysis_status === "queued"
    ).length
    const failedDocuments = documents.filter(d => d.analysis_status === "failed").length

    return (
        <div className="flex min-h-screen flex-col bg-background">
            {/* Header */}
            <div className="border-b border-border bg-card px-6 py-4">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight text-foreground">
                            Document Validation
                        </h1>
                        <p className="mt-1 text-sm text-muted-foreground">
                            Upload and validate documents for authenticity and compliance
                        </p>
                    </div>
                    {currentUser && (
                        <div className="flex items-center gap-3 rounded-lg border border-border bg-background px-4 py-2">
                            <User className="size-5 text-muted-foreground" />
                            <div className="text-right">
                                <p className="text-sm font-medium text-foreground">{currentUser.name}</p>
                                <p className="text-xs text-muted-foreground">{currentUser.userType}</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-auto p-6">
                <div className="space-y-6">
                    {/* Stats Cards */}
                    <div className="grid gap-4 md:grid-cols-4">
                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-muted-foreground">Total Documents</p>
                                        <p className="mt-2 text-3xl font-bold">{totalDocuments}</p>
                                    </div>
                                    <FileText className="size-8 text-muted-foreground" />
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-muted-foreground">Completed</p>
                                        <p className="mt-2 text-3xl font-bold">{completedDocuments}</p>
                                    </div>
                                    <CheckCircle2 className="size-8 text-emerald-500" />
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-muted-foreground">Processing</p>
                                        <p className="mt-2 text-3xl font-bold">{processingDocuments}</p>
                                    </div>
                                    <Clock className="size-8 text-amber-500" />
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-muted-foreground">Failed</p>
                                        <p className="mt-2 text-3xl font-bold">{failedDocuments}</p>
                                    </div>
                                    <AlertCircle className="size-8 text-destructive" />
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Upload Section */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Upload Document</CardTitle>
                            <CardDescription>
                                Upload PDF, DOC, or DOCX files for validation
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <div className="flex items-center gap-4">
                                    <label htmlFor="file-upload" className="cursor-pointer">
                                        <div className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90">
                                            <Upload className="size-4" />
                                            {isUploading ? "Uploading..." : "Choose File"}
                                        </div>
                                        <input
                                            id="file-upload"
                                            type="file"
                                            accept=".pdf,.doc,.docx"
                                            onChange={handleFileUpload}
                                            disabled={isUploading}
                                            className="hidden"
                                        />
                                    </label>
                                    <p className="text-sm text-muted-foreground">
                                        Supported formats: PDF, DOC, DOCX
                                    </p>
                                </div>
                                {uploadError && (
                                    <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                                        {uploadError}
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Documents List */}
                    <div className="flex flex-col gap-6">
                        <div className="flex items-center justify-between">
                            <h2 className="text-lg font-semibold text-foreground">
                                Documents ({documents.length})
                            </h2>
                            <Button
                                variant="outline"
                                size="sm"
                                // onClick={fetchDocuments}
                                disabled={isLoading}
                            >
                                <RefreshCw className={`mr-2 size-4 ${isLoading ? "animate-spin" : ""}`} />
                                Refresh
                            </Button>
                        </div>

                        <div className="flex gap-4">
                            {/* Documents Sidebar */}
                            <div className="flex flex-col flex-none gap-4 w-80">
                                {/* Recently Uploaded Document Card */}
                                {uploadedDocId && (
                                    <Card
                                        className={`cursor-pointer transition-colors hover:bg-accent/50 border-2 border-blue-400 ${selectedDocument?.id === uploadedDocId
                                            ? "border-primary ring-2 ring-primary/20"
                                            : ""
                                            }`}
                                        onClick={async () => {
                                            try {
                                                const response = await fetch(`${BACKEND_2_API_URL}/documents/analysis/${uploadedDocId}`)
                                                if (response.ok) {
                                                    const data = await response.json()
                                                    setSelectedDocument(data)
                                                    console.log("Fetched uploaded document:", data)
                                                } else {
                                                    console.error("Failed to fetch uploaded document")
                                                }
                                            } catch (error) {
                                                console.error("Error fetching uploaded document:", error)
                                            }
                                        }}
                                    >
                                        <CardContent className="pt-4">
                                            <div className="space-y-2">
                                                <div className="flex items-start justify-between gap-2">
                                                    <h3 className="text-sm font-semibold text-foreground line-clamp-2">
                                                        📄 Recently Uploaded (ID: {uploadedDocId})
                                                    </h3>
                                                    <Clock className="size-4 text-amber-500 animate-pulse" />
                                                </div>
                                                <p className="text-xs text-muted-foreground">
                                                    Click to refresh and view details
                                                </p>
                                                <div className="flex flex-wrap gap-1 pt-1">
                                                    <span className="inline-block rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800 dark:bg-blue-900/20 dark:text-blue-300">
                                                        Just Uploaded
                                                    </span>
                                                </div>
                                            </div>
                                        </CardContent>
                                    </Card>
                                )}

                                {documents.length === 0 && !isLoading && !uploadedDocId && (
                                    <Card>
                                        <CardContent className="pt-6">
                                            <p className="text-center text-sm text-muted-foreground">
                                                No documents uploaded yet
                                            </p>
                                        </CardContent>
                                    </Card>
                                )}
                                {documents.map((doc) => (
                                    <Card
                                        key={doc.id}
                                        className={`cursor-pointer transition-colors hover:bg-accent/50 ${selectedDocument?.id === doc.id
                                            ? "border-primary ring-2 ring-primary/20"
                                            : ""
                                            }`}
                                        onClick={() => setSelectedDocument(doc)}
                                    >
                                        <CardContent className="pt-4">
                                            <div className="space-y-2">
                                                <div className="flex items-start justify-between gap-2">
                                                    <h3 className="text-sm font-semibold text-foreground line-clamp-2">
                                                        {doc.filename}
                                                    </h3>
                                                    {getStatusIcon(doc.analysis_status)}
                                                </div>
                                                <p className="text-xs text-muted-foreground">
                                                    {new Date(doc.upload_timestamp).toLocaleString()}
                                                </p>
                                                <div className="flex flex-wrap gap-1 pt-1">
                                                    <span className="inline-block rounded bg-muted px-2 py-0.5 text-xs font-medium">
                                                        {doc.file_type}
                                                    </span>
                                                    <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium capitalize`}>
                                                        {doc.analysis_status}
                                                    </span>
                                                    {doc.risk_score !== undefined && (
                                                        <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${getRiskColor(doc.risk_score)}`}>
                                                            {getRiskLabel(doc.risk_score)}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>

                            {/* Document Details */}
                            <div className="w-full">
                                {selectedDocument ? (
                                    <div className="flex flex-col gap-4">
                                        {/* Document Info */}
                                        <Card>
                                            <CardHeader>
                                                <div className="flex items-start justify-between">
                                                    <div>
                                                        <CardTitle>{selectedDocument.filename}</CardTitle>
                                                        <CardDescription className="mt-2">
                                                            Uploaded {new Date(selectedDocument.upload_timestamp).toLocaleString()}
                                                        </CardDescription>
                                                    </div>
                                                    {getStatusIcon(selectedDocument.analysis_status)}
                                                </div>
                                            </CardHeader>
                                            <CardContent>
                                                <div className="flex gap-2">
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() => handleDownload(selectedDocument.id, "markdown")}
                                                    >
                                                        <Download className="mr-2 size-4" />
                                                        Download Markdown
                                                    </Button>
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() => handleDownload(selectedDocument.id, "json")}
                                                    >
                                                        <Download className="mr-2 size-4" />
                                                        Download JSON
                                                    </Button>
                                                    <Button
                                                        variant="destructive"
                                                        size="sm"
                                                        onClick={() => handleDeleteDocument(selectedDocument.id)}
                                                    >
                                                        <Trash2 className="mr-2 size-4" />
                                                        Delete
                                                    </Button>
                                                </div>
                                                {selectedDocument.analysis_status !== "completed" && (
                                                    <p className="mt-2 text-xs text-muted-foreground">
                                                        Note: Downloads are available once processing is complete. Current status: {selectedDocument.analysis_status}
                                                    </p>
                                                )}
                                            </CardContent>
                                        </Card>

                                        {/* Metadata */}
                                        {selectedDocument.metadata && selectedDocument.analysis_status === "completed" && (
                                            <Card>
                                                <CardHeader>
                                                    <CardTitle className="text-base">Document Metadata</CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="grid grid-cols-2 gap-4">
                                                        <div>
                                                            <p className="text-xs font-medium text-muted-foreground">Total Pages</p>
                                                            <p className="mt-1 text-sm font-semibold text-foreground">
                                                                {selectedDocument.metadata.total_pages || "N/A"}
                                                            </p>
                                                        </div>
                                                        <div>
                                                            <p className="text-xs font-medium text-muted-foreground">Total Issues</p>
                                                            <p className="mt-1 text-sm font-semibold text-foreground">
                                                                {selectedDocument.metadata.total_issues || 0}
                                                            </p>
                                                        </div>
                                                        <div>
                                                            <p className="text-xs font-medium text-muted-foreground">Errors</p>
                                                            <p className="mt-1 text-sm font-semibold text-destructive">
                                                                {selectedDocument.metadata.errors || 0}
                                                            </p>
                                                        </div>
                                                        <div>
                                                            <p className="text-xs font-medium text-muted-foreground">Warnings</p>
                                                            <p className="mt-1 text-sm font-semibold text-amber-600">
                                                                {selectedDocument.metadata.warnings || 0}
                                                            </p>
                                                        </div>
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        )}

                                        {/* Risk Score */}
                                        {selectedDocument.risk_score !== undefined && (
                                            <Card>
                                                <CardHeader>
                                                    <CardTitle className="text-base">Risk Assessment</CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="flex items-center justify-between">
                                                        <div>
                                                            <p className="text-sm font-medium text-muted-foreground">Risk Score</p>
                                                            <p className="mt-2 text-3xl font-bold">
                                                                {(selectedDocument.risk_score * 100).toFixed(1)}%
                                                            </p>
                                                        </div>
                                                        <span className={`rounded-full px-4 py-2 text-sm font-medium ${getRiskColor(selectedDocument.risk_score)}`}>
                                                            {getRiskLabel(selectedDocument.risk_score)}
                                                        </span>
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        )}

                                        {/* Findings */}
                                        {selectedDocument.findings && selectedDocument.findings.length > 0 && (
                                            <Card>
                                                <CardHeader>
                                                    <CardTitle className="text-base">Validation Findings</CardTitle>
                                                    <CardDescription>
                                                        {selectedDocument.findings.length} issue(s) found
                                                    </CardDescription>
                                                </CardHeader>
                                                <CardContent>
                                                    <div className="space-y-3 max-h-96 overflow-y-auto">
                                                        {selectedDocument.findings.map((finding, index) => (
                                                            <div
                                                                key={index}
                                                                className="rounded-lg border border-border p-3 space-y-2"
                                                            >
                                                                <div className="flex items-start gap-2">
                                                                    {getSeverityIcon(finding.severity)}
                                                                    <div className="flex-1">
                                                                        <div className="flex items-center gap-2">
                                                                            <span className="text-sm font-semibold text-foreground">
                                                                                {finding.type}
                                                                            </span>
                                                                            <span className="text-xs text-muted-foreground">
                                                                                {finding.category}
                                                                            </span>
                                                                        </div>
                                                                        <p className="mt-1 text-sm text-foreground">
                                                                            {finding.description}
                                                                        </p>
                                                                        {finding.suggestions && finding.suggestions.length > 0 && (
                                                                            <div className="mt-2">
                                                                                <p className="text-xs font-medium text-muted-foreground">
                                                                                    Suggestions:
                                                                                </p>
                                                                                <ul className="mt-1 list-disc list-inside text-xs text-foreground">
                                                                                    {finding.suggestions.map((suggestion, i) => (
                                                                                        <li key={i}>{suggestion}</li>
                                                                                    ))}
                                                                                </ul>
                                                                            </div>
                                                                        )}
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        )}

                                        {/* Error Message */}
                                        {selectedDocument.error_message && (
                                            <Card className="border-destructive">
                                                <CardHeader>
                                                    <CardTitle className="text-base text-destructive">
                                                        Processing Error
                                                    </CardTitle>
                                                </CardHeader>
                                                <CardContent>
                                                    <p className="text-sm text-foreground">
                                                        {selectedDocument.error_message}
                                                    </p>
                                                </CardContent>
                                            </Card>
                                        )}

                                        {/* Processing Status */}
                                        {(selectedDocument.analysis_status === "queued" ||
                                            selectedDocument.analysis_status === "processing") && (
                                                <Card className="border-amber-200 bg-amber-50 dark:border-amber-900/30 dark:bg-amber-900/10">
                                                    <CardContent className="pt-6">
                                                        <div className="flex items-center gap-3">
                                                            <Clock className="size-5 text-amber-500 animate-pulse" />
                                                            <div>
                                                                <p className="text-sm font-medium text-foreground">
                                                                    Document is being processed...
                                                                </p>
                                                                <p className="text-xs text-muted-foreground">
                                                                    This may take a few moments
                                                                </p>
                                                            </div>
                                                        </div>
                                                    </CardContent>
                                                </Card>
                                            )}
                                    </div>
                                ) : (
                                    <Card>
                                        <CardContent className="flex min-h-96 items-center justify-center pt-6">
                                            <div className="text-center">
                                                <FileText className="mx-auto size-12 text-muted-foreground/30" />
                                                <p className="mt-4 text-sm text-muted-foreground">
                                                    Select a document to view details
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
        </div>
    )
}

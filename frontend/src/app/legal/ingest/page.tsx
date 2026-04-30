"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { getUser } from "~/lib/auth"
import { Upload, FileText, CheckCircle2 } from "lucide-react"
import {
    Card,
    CardHeader,
    CardTitle,
    CardDescription,
    CardContent,
} from "~/components/ui/card"
import { Button } from "~/components/ui/button"

interface UploadedFile {
    id: string
    fileName: string
    fileSize: string
    uploadTime: string
    status: "uploading" | "processing" | "completed" | "error"
}

export default function IngestPage() {
    const router = useRouter()
    useEffect(() => { if (!getUser()) router.replace("/auth/login") }, [router])

    const [dragActive, setDragActive] = useState(false)
    const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([
        {
            id: "1",
            fileName: "FCA_AML_Update_2025.pdf",
            fileSize: "2.4 MB",
            uploadTime: "2025-11-01 10:30 AM",
            status: "completed",
        },
        {
            id: "2",
            fileName: "ICO_Data_Protection_Notice.pdf",
            fileSize: "1.8 MB",
            uploadTime: "2025-10-28 2:15 PM",
            status: "completed",
        },
    ])

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true)
        } else if (e.type === "dragleave") {
            setDragActive(false)
        }
    }

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        setDragActive(false)

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            const file = e.dataTransfer.files[0]
            addFile(file)
        }
    }

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0]
            addFile(file)
        }
    }

    const addFile = (file: File) => {
        const newFile: UploadedFile = {
            id: Date.now().toString(),
            fileName: file.name,
            fileSize: `${(file.size / (1024 * 1024)).toFixed(2)} MB`,
            uploadTime: new Date().toLocaleString(),
            status: "uploading",
        }

        setUploadedFiles((prev) => [newFile, ...prev])

        // Simulate upload progress
        setTimeout(() => {
            setUploadedFiles((prev) =>
                prev.map((f) =>
                    f.id === newFile.id ? { ...f, status: "processing" } : f
                )
            )
        }, 1500)

        setTimeout(() => {
            setUploadedFiles((prev) =>
                prev.map((f) =>
                    f.id === newFile.id ? { ...f, status: "completed" } : f
                )
            )
        }, 3000)
    }

    const getStatusDisplay = (status: UploadedFile["status"]) => {
        switch (status) {
            case "uploading":
                return (
                    <div className="flex items-center gap-2">
                        <div className="size-2 rounded-full bg-amber-500 animate-pulse" />
                        <span className="text-xs text-amber-500 font-medium">Uploading...</span>
                    </div>
                )
            case "processing":
                return (
                    <div className="flex items-center gap-2">
                        <div className="size-2 rounded-full bg-blue-500 animate-pulse" />
                        <span className="text-xs text-blue-500 font-medium">Processing...</span>
                    </div>
                )
            case "completed":
                return (
                    <div className="flex items-center gap-2">
                        <CheckCircle2 className="size-4 text-emerald-500" />
                        <span className="text-xs text-emerald-500 font-medium">Completed</span>
                    </div>
                )
            case "error":
                return (
                    <div className="flex items-center gap-2">
                        <span className="text-xs text-destructive font-medium">Error</span>
                    </div>
                )
        }
    }

    return (
        <div className="flex min-h-screen flex-col bg-background">
            {/* Header */}
            <div className="border-b border-border bg-card px-6 py-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-foreground">
                        Document Ingestion
                    </h1>
                    <p className="mt-1 text-sm text-muted-foreground">
                        Upload and process regulatory notices from financial regulators
                    </p>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-auto p-6">
                <div className="space-y-6 max-w-4xl">
                    {/* Upload Section */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Upload New Documents</CardTitle>
                            <CardDescription>
                                Drag and drop or click to select regulatory notice documents to ingest
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div
                                className={`rounded-lg border-2 border-dashed p-12 text-center transition-colors ${dragActive
                                        ? "border-primary bg-primary/5"
                                        : "border-border hover:border-primary/50"
                                    }`}
                                onDragEnter={handleDrag}
                                onDragLeave={handleDrag}
                                onDragOver={handleDrag}
                                onDrop={handleDrop}
                            >
                                <Upload className="mx-auto size-8 text-muted-foreground" />
                                <p className="mt-2 text-sm font-medium text-foreground">
                                    Drag and drop your document files here
                                </p>
                                <p className="mt-1 text-xs text-muted-foreground">
                                    Supported formats: PDF, DOC, DOCX • Maximum file size: 10 MB
                                </p>
                                <label className="mt-4 inline-block">
                                    <Button variant="outline" asChild>
                                        <span>Browse Files</span>
                                    </Button>
                                    <input
                                        type="file"
                                        multiple
                                        accept=".pdf,.doc,.docx"
                                        onChange={handleChange}
                                        className="hidden"
                                    />
                                </label>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Upload History */}
                    <div>
                        <h2 className="mb-4 text-lg font-semibold text-foreground">
                            Upload History
                        </h2>

                        <div className="space-y-2">
                            {uploadedFiles.length > 0 ? (
                                uploadedFiles.map((file) => (
                                    <Card key={file.id}>
                                        <CardContent className="pt-6">
                                            <div className="flex items-center justify-between gap-4">
                                                <div className="flex flex-1 items-center gap-3 min-w-0">
                                                    <FileText className="size-5 shrink-0 text-muted-foreground" />
                                                    <div className="flex-1 min-w-0">
                                                        <p className="text-sm font-medium text-foreground truncate">
                                                            {file.fileName}
                                                        </p>
                                                        <p className="mt-1 text-xs text-muted-foreground">
                                                            {file.fileSize} • {file.uploadTime}
                                                        </p>
                                                    </div>
                                                </div>
                                                <div className="shrink-0">
                                                    {getStatusDisplay(file.status)}
                                                </div>
                                            </div>
                                        </CardContent>
                                    </Card>
                                ))
                            ) : (
                                <Card>
                                    <CardContent className="pt-6">
                                        <p className="text-center text-sm text-muted-foreground">
                                            No documents uploaded yet
                                        </p>
                                    </CardContent>
                                </Card>
                            )}
                        </div>
                    </div>

                    {/* Info Section */}
                    <Card className="bg-blue-50 border-blue-200 dark:bg-blue-950/30 dark:border-blue-900">
                        <CardContent className="pt-6">
                            <div className="space-y-2">
                                <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-100">
                                    Processing Information
                                </h3>
                                <ul className="text-xs text-blue-800 dark:text-blue-200 space-y-1 list-disc list-inside">
                                    <li>Documents are automatically parsed and analyzed</li>
                                    <li>Regulatory metadata is extracted and structured</li>
                                    <li>Notices are queued for legal team review</li>
                                    <li>Processing typically takes 2-5 minutes per document</li>
                                </ul>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    )
}

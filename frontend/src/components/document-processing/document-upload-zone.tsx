"use client";

import { Upload, File, X, CheckCircle2, AlertCircle } from "lucide-react";
import { useState, useCallback } from "react";
import { Card, CardContent } from "~/components/ui/card";
import { Progress } from "~/components/ui/progress";
import { Button } from "~/components/ui/button";
import { Badge } from "~/components/ui/badge";
import type { UploadProgress, DocumentType } from "~/types/document-processing";

interface DocumentUploadZoneProps {
  acceptedTypes?: string[];
  maxSizeMB?: number;
  onUpload?: (files: File[]) => void;
  allowMultiple?: boolean;
  documentType?: DocumentType;
}

export function DocumentUploadZone({
  acceptedTypes = [".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png"],
  maxSizeMB = 10,
  onUpload,
  allowMultiple = false,
  documentType,
}: DocumentUploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploads, setUploads] = useState<UploadProgress[]>([]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      const files = Array.from(e.dataTransfer.files);
      processFiles(files);
    },
    [allowMultiple, maxSizeMB],
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files ? Array.from(e.target.files) : [];
      processFiles(files);
    },
    [allowMultiple, maxSizeMB],
  );

  const processFiles = (files: File[]) => {
    const validFiles = files.filter((file) => {
      const maxSize = maxSizeMB * 1024 * 1024;
      if (file.size > maxSize) {
        console.error(`File ${file.name} exceeds ${maxSizeMB}MB limit`);
        return false;
      }
      return true;
    });

    if (!allowMultiple && validFiles.length > 0) {
      validFiles.splice(1);
    }

    if (onUpload) {
      onUpload(validFiles);
    }

    // Simulate upload progress
    const newUploads: UploadProgress[] = validFiles.map((file) => ({
      fileId: Math.random().toString(36).substr(2, 9),
      filename: file.name,
      progress: 0,
      status: "uploading",
    }));

    setUploads((prev) => [...prev, ...newUploads]);

    // Simulate progress
    newUploads.forEach((upload) => {
      simulateUpload(upload.fileId);
    });
  };

  const simulateUpload = (fileId: string) => {
    const interval = setInterval(() => {
      setUploads((prev) =>
        prev.map((upload) => {
          if (upload.fileId === fileId) {
            const newProgress = Math.min(upload.progress + 10, 100);
            if (newProgress === 100) {
              clearInterval(interval);
              setTimeout(() => {
                setUploads((p) =>
                  p.map((u) =>
                    u.fileId === fileId
                      ? { ...u, status: "completed", progress: 100 }
                      : u,
                  ),
                );
              }, 500);
              return { ...upload, status: "processing", progress: 100 };
            }
            return { ...upload, progress: newProgress };
          }
          return upload;
        }),
      );
    }, 300);
  };

  const removeUpload = (fileId: string) => {
    setUploads((prev) => prev.filter((upload) => upload.fileId !== fileId));
  };

  const getStatusIcon = (status: UploadProgress["status"]) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="size-5 text-emerald-500" />;
      case "failed":
        return <AlertCircle className="size-5 text-destructive" />;
      default:
        return <File className="size-5 text-muted-foreground" />;
    }
  };

  const getStatusBadge = (status: UploadProgress["status"]) => {
    const variants: Record<
      UploadProgress["status"],
      "default" | "secondary" | "destructive" | "outline"
    > = {
      pending: "outline",
      uploading: "secondary",
      processing: "secondary",
      completed: "default",
      failed: "destructive",
    };

    return (
      <Badge variant={variants[status]} className="text-xs">
        {status}
      </Badge>
    );
  };

  return (
    <div className="space-y-4">
      <Card
        className={`border-2 border-dashed transition-colors ${
          isDragging
            ? "border-primary bg-primary/5"
            : "border-border hover:border-primary/50"
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <CardContent className="flex min-h-64 flex-col items-center justify-center p-6">
          <Upload
            className={`mb-4 size-12 ${isDragging ? "text-primary" : "text-muted-foreground"}`}
          />
          <h3 className="text-foreground mb-2 text-lg font-semibold">
            Upload Documents
          </h3>
          <p className="text-muted-foreground mb-4 text-center text-sm">
            Drag and drop your files here, or click to browse
          </p>
          <input
            type="file"
            id="file-upload"
            className="hidden"
            accept={acceptedTypes.join(",")}
            multiple={allowMultiple}
            onChange={handleFileInput}
          />
          <Button asChild>
            <label htmlFor="file-upload" className="cursor-pointer">
              Browse Files
            </label>
          </Button>
          <p className="text-muted-foreground mt-4 text-xs">
            Accepted: {acceptedTypes.join(", ")} • Max {maxSizeMB}MB
          </p>
          {documentType && (
            <Badge variant="outline" className="mt-2">
              Type: {documentType.replace("_", " ")}
            </Badge>
          )}
        </CardContent>
      </Card>

      {uploads.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-foreground text-sm font-medium">
            Upload Progress
          </h4>
          {uploads.map((upload) => (
            <Card key={upload.fileId}>
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  {getStatusIcon(upload.status)}
                  <div className="flex-1 space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-foreground text-sm font-medium">
                          {upload.filename}
                        </p>
                        {upload.error && (
                          <p className="text-destructive text-xs">
                            {upload.error}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        {getStatusBadge(upload.status)}
                        <Button
                          variant="ghost"
                          size="icon"
                          className="size-6"
                          onClick={() => removeUpload(upload.fileId)}
                        >
                          <X className="size-4" />
                        </Button>
                      </div>
                    </div>
                    {upload.status !== "completed" &&
                      upload.status !== "failed" && (
                        <Progress value={upload.progress} className="h-2" />
                      )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

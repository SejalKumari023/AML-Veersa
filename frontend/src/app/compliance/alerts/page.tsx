"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getUser } from "~/lib/auth";
import { Card } from "~/components/ui/card";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "~/components/ui/table";
import { format } from "date-fns";

interface Alert {
    id: string;
    transaction_id: string;
    alert_type: string;
    severity: string;
    message: string;
    timestamp: string;
    status: string;
    assigned_to: string | null;
}

// Hardcoded sample alert data
const SAMPLE_ALERTS: Alert[] = [
    {
        id: "1",
        transaction_id: "TXN-2024-001234",
        alert_type: "Large Transaction",
        severity: "high",
        message: "Unusual large transaction detected exceeding $500,000 threshold",
        timestamp: "2024-11-02T10:30:00Z",
        status: "open",
        assigned_to: "John Smith"
    },
    {
        id: "2",
        transaction_id: "TXN-2024-001235",
        alert_type: "Suspicious Pattern",
        severity: "medium",
        message: "Multiple small transactions detected within short timeframe",
        timestamp: "2024-11-02T09:15:00Z",
        status: "investigating",
        assigned_to: "Jane Doe"
    },
    {
        id: "3",
        transaction_id: "TXN-2024-001236",
        alert_type: "Geographic Risk",
        severity: "high",
        message: "Transaction to high-risk jurisdiction flagged",
        timestamp: "2024-11-02T08:45:00Z",
        status: "open",
        assigned_to: null
    },
    {
        id: "4",
        transaction_id: "TXN-2024-001237",
        alert_type: "Velocity Check",
        severity: "low",
        message: "Increased transaction velocity compared to historical pattern",
        timestamp: "2024-11-01T16:20:00Z",
        status: "resolved",
        assigned_to: "Mike Johnson"
    },
    {
        id: "5",
        transaction_id: "TXN-2024-001238",
        alert_type: "Sanctions Screening",
        severity: "high",
        message: "Potential sanctions list match requires verification",
        timestamp: "2024-11-01T14:10:00Z",
        status: "escalated",
        assigned_to: "Sarah Williams"
    },
    {
        id: "6",
        transaction_id: "TXN-2024-001239",
        alert_type: "Structuring",
        severity: "medium",
        message: "Possible structuring activity detected across multiple accounts",
        timestamp: "2024-11-01T11:05:00Z",
        status: "investigating",
        assigned_to: "John Smith"
    },
    {
        id: "7",
        transaction_id: "TXN-2024-001240",
        alert_type: "Customer Due Diligence",
        severity: "low",
        message: "Customer due diligence update required",
        timestamp: "2024-11-01T09:30:00Z",
        status: "open",
        assigned_to: null
    },
    {
        id: "8",
        transaction_id: "TXN-2024-001241",
        alert_type: "Beneficial Ownership",
        severity: "medium",
        message: "Unclear beneficial ownership structure requires review",
        timestamp: "2024-10-31T15:45:00Z",
        status: "open",
        assigned_to: "Jane Doe"
    }
];

export default function AlertsPage() {
    const router = useRouter();
    useEffect(() => { if (!getUser()) router.replace("/auth/login"); }, [router]);
    const alerts = SAMPLE_ALERTS;

    const getSeverityColor = (severity: string) => {
        switch (severity.toLowerCase()) {
            case "high":
                return "text-red-600";
            case "medium":
                return "text-yellow-600";
            case "low":
                return "text-blue-600";
            default:
                return "text-gray-600";
        }
    };

    return (
        <div className="p-6">
            <h1 className="text-2xl font-semibold mb-6">Alerts</h1>
            <Card>
                <div className="overflow-x-auto">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Timestamp</TableHead>
                                <TableHead>Alert Type</TableHead>
                                <TableHead>Severity</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead>Transaction ID</TableHead>
                                <TableHead>Message</TableHead>
                                <TableHead>Assigned To</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {alerts.map((alert) => (
                                <TableRow key={alert.id}>
                                    <TableCell className="whitespace-nowrap">
                                        {format(new Date(alert.timestamp), "MMM d, yyyy HH:mm:ss")}
                                    </TableCell>
                                    <TableCell className="whitespace-nowrap">
                                        {alert.alert_type}
                                    </TableCell>
                                    <TableCell
                                        className={`whitespace-nowrap font-medium ${getSeverityColor(
                                            alert.severity
                                        )}`}
                                    >
                                        {alert.severity.toUpperCase()}
                                    </TableCell>
                                    <TableCell className="whitespace-nowrap">{alert.status}</TableCell>
                                    <TableCell className="whitespace-nowrap font-mono text-sm">
                                        {alert.transaction_id}
                                    </TableCell>
                                    <TableCell className="max-w-md truncate">
                                        {alert.message}
                                    </TableCell>
                                    <TableCell className="whitespace-nowrap">
                                        {alert.assigned_to || "-"}
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </div>
            </Card>
        </div>
    );
}
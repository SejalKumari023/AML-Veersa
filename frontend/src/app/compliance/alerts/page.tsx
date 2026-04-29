"use client";

import { useState, useEffect } from "react";
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

export default function AlertsPage() {
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchAlerts = async () => {
            try {
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || "/api"

                const response = await fetch(`${apiUrl}/data/alerts?limit=100`, {
                    method: "GET",
                    headers: {
                        "Content-Type": "application/json",
                    },
                })

                if (!response.ok) {
                    throw new Error("Failed to fetch alerts");
                }
                const data = await response.json();
                setAlerts(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : "An error occurred");
            } finally {
                setLoading(false);
            }
        };

        fetchAlerts();
    }, []);

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

    if (loading) {
        return (
            <div className="p-6">
                <div className="animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
                    <div className="space-y-3">
                        {[...Array(5)].map((_, i) => (
                            <div key={i} className="h-4 bg-gray-200 rounded w-full"></div>
                        ))}
                    </div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-6">
                <Card className="p-4 bg-red-50 text-red-600">
                    <p>{error}</p>
                </Card>
            </div>
        );
    }

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
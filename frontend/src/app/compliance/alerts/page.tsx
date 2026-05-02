"use client";

import { useEffect, useState } from "react";
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
import { env } from "~/env";

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

const API_URL = env.NEXT_PUBLIC_API_URL ?? "/api";

export default function AlertsPage() {
    const router = useRouter();
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!getUser()) { router.replace("/auth/login"); return; }
        fetch(`${API_URL}/data/alerts?limit=100`)
            .then((r) => r.ok ? r.json() : Promise.reject(r.statusText))
            .then((data: Alert[]) => setAlerts(data))
            .catch((err) => console.error("Failed to load alerts:", err))
            .finally(() => setLoading(false));
    }, [router]);

    const getSeverityColor = (severity: string) => {
        switch (severity.toLowerCase()) {
            case "high":   return "text-red-600";
            case "medium": return "text-yellow-600";
            case "low":    return "text-blue-600";
            default:       return "text-gray-600";
        }
    };

    return (
        <div className="p-6">
            <h1 className="text-2xl font-semibold mb-6">Alerts</h1>
            <Card>
                <div className="overflow-x-auto">
                    {loading ? (
                        <div className="p-8 text-center text-muted-foreground">Loading alerts…</div>
                    ) : alerts.length === 0 ? (
                        <div className="p-8 text-center text-muted-foreground">No alerts found.</div>
                    ) : (
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
                                        <TableCell className="whitespace-nowrap" suppressHydrationWarning>
                                            {format(new Date(alert.timestamp), "MMM d, yyyy HH:mm:ss")}
                                        </TableCell>
                                        <TableCell className="whitespace-nowrap">{alert.alert_type}</TableCell>
                                        <TableCell className={`whitespace-nowrap font-medium ${getSeverityColor(alert.severity)}`}>
                                            {alert.severity.toUpperCase()}
                                        </TableCell>
                                        <TableCell className="whitespace-nowrap">{alert.status}</TableCell>
                                        <TableCell className="whitespace-nowrap font-mono text-sm">{alert.transaction_id}</TableCell>
                                        <TableCell className="max-w-md truncate">{alert.message}</TableCell>
                                        <TableCell className="whitespace-nowrap">{alert.assigned_to ?? "-"}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}
                </div>
            </Card>
        </div>
    );
}

"use client"

import { useState } from "react"
import {
    Search,
    Users,
    FileText,
    AlertCircle,
    CheckCircle2,
    TrendingUp,
    Phone,
    Mail,
    MapPin,
    Calendar,
    Shield,
    Eye,
    Edit,
    Download,
    AlertTriangle,
} from "lucide-react"
import {
    Card,
    CardHeader,
    CardTitle,
    CardDescription,
    CardContent,
} from "~/components/ui/card"
import { Button } from "~/components/ui/button"
import { InputGroup, InputGroupAddon, InputGroupInput } from "~/components/ui/input-group"
import { Input } from "~/components/ui/input"

interface Client {
    id: string
    name: string
    type: "individual" | "corporate"
    email: string
    phone: string
    country: string
    status: "active" | "dormant" | "flagged" | "archived"
    riskRating: "low" | "medium" | "high"
    kycStatus: "compliant" | "pending" | "expired"
    kycDate: string
    kycExpiryDate: string
    isPep: boolean
    eddRequired: boolean
    eddCompleted: boolean
    totalTransactions: number
    totalVolume: number
    lastTransaction: string
    industry?: string
    registrationNumber?: string
    complianceScore: number
    flags: string[]
}

export default function FrontOfficePage() {
    const [clients, setClients] = useState<Client[]>([
        {
            id: "c1",
            name: "Acme Corporation",
            type: "corporate",
            email: "info@acmecorp.com",
            phone: "+1-555-0101",
            country: "United States",
            status: "active",
            riskRating: "medium",
            kycStatus: "compliant",
            kycDate: "2024-09-15",
            kycExpiryDate: "2026-09-15",
            isPep: false,
            eddRequired: false,
            eddCompleted: true,
            totalTransactions: 45,
            totalVolume: 2500000,
            lastTransaction: "2025-11-02T14:30:00Z",
            industry: "Manufacturing",
            registrationNumber: "ACM-123456",
            complianceScore: 92,
            flags: [],
        },
        {
            id: "c2",
            name: "Tech Solutions Inc",
            type: "corporate",
            email: "compliance@techsolutions.com",
            phone: "+49-30-555-1234",
            country: "Germany",
            status: "active",
            riskRating: "low",
            kycStatus: "compliant",
            kycDate: "2024-11-01",
            kycExpiryDate: "2026-11-01",
            isPep: false,
            eddRequired: false,
            eddCompleted: true,
            totalTransactions: 32,
            totalVolume: 1200000,
            lastTransaction: "2025-11-02T13:15:00Z",
            industry: "Technology",
            registrationNumber: "TSI-789012",
            complianceScore: 98,
            flags: [],
        },
        {
            id: "c3",
            name: "Import Export Ltd",
            type: "corporate",
            email: "trade@importexport.ae",
            phone: "+971-4-555-5678",
            country: "United Arab Emirates",
            status: "active",
            riskRating: "high",
            kycStatus: "compliant",
            kycDate: "2023-08-20",
            kycExpiryDate: "2025-08-20",
            isPep: false,
            eddRequired: true,
            eddCompleted: true,
            totalTransactions: 78,
            totalVolume: 4500000,
            lastTransaction: "2025-11-02T10:45:00Z",
            industry: "Trade & Logistics",
            registrationNumber: "IEL-345678",
            complianceScore: 75,
            flags: ["high_risk_jurisdiction", "edd_required"],
        },
        {
            id: "c4",
            name: "John Prestigious",
            type: "individual",
            email: "john@prestigious.com",
            phone: "+44-20-7555-9999",
            country: "United Kingdom",
            status: "flagged",
            riskRating: "high",
            kycStatus: "pending",
            kycDate: "2024-10-01",
            kycExpiryDate: "2026-10-01",
            isPep: true,
            eddRequired: true,
            eddCompleted: false,
            totalTransactions: 15,
            totalVolume: 3200000,
            lastTransaction: "2025-10-28T09:20:00Z",
            complianceScore: 65,
            flags: ["pep_status", "edd_required", "edd_not_completed"],
        },
        {
            id: "c5",
            name: "Global Trading Partners",
            type: "corporate",
            email: "ops@globaltrading.com",
            phone: "+65-6555-1111",
            country: "Singapore",
            status: "active",
            riskRating: "medium",
            kycStatus: "compliant",
            kycDate: "2024-06-10",
            kycExpiryDate: "2026-06-10",
            isPep: false,
            eddRequired: true,
            eddCompleted: true,
            totalTransactions: 56,
            totalVolume: 5800000,
            lastTransaction: "2025-11-01T16:00:00Z",
            industry: "Trading",
            registrationNumber: "GTP-567890",
            complianceScore: 88,
            flags: ["high_volume"],
        },
        {
            id: "c6",
            name: "Finance Investment Corp",
            type: "corporate",
            email: "clients@financeic.com",
            phone: "+1-212-555-7777",
            country: "United States",
            status: "dormant",
            riskRating: "low",
            kycStatus: "expired",
            kycDate: "2023-03-15",
            kycExpiryDate: "2024-03-15",
            isPep: false,
            eddRequired: false,
            eddCompleted: true,
            totalTransactions: 12,
            totalVolume: 450000,
            lastTransaction: "2025-06-15T12:00:00Z",
            industry: "Financial Services",
            registrationNumber: "FIC-901234",
            complianceScore: 45,
            flags: ["kyc_expired"],
        },
    ])

    const [selectedClient, setSelectedClient] = useState<Client | null>(null)
    const [searchTerm, setSearchTerm] = useState("")

    const filteredClients = clients.filter(
        (client) =>
            client.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            client.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
            client.country.toLowerCase().includes(searchTerm.toLowerCase())
    )

    const getStatusColor = (status: Client["status"]) => {
        switch (status) {
            case "active":
                return "text-emerald-600 bg-emerald-100 dark:bg-emerald-900/20"
            case "dormant":
                return "text-blue-600 bg-blue-100 dark:bg-blue-900/20"
            case "flagged":
                return "text-amber-600 bg-amber-100 dark:bg-amber-900/20"
            case "archived":
                return "text-muted-foreground bg-muted"
            default:
                return "text-muted-foreground"
        }
    }

    const getRiskColor = (risk: Client["riskRating"]) => {
        switch (risk) {
            case "high":
                return "text-destructive bg-destructive/10"
            case "medium":
                return "text-amber-600 bg-amber-100 dark:bg-amber-900/20"
            case "low":
                return "text-emerald-600 bg-emerald-100 dark:bg-emerald-900/20"
            default:
                return "text-muted-foreground"
        }
    }

    const getKycColor = (kycStatus: Client["kycStatus"]) => {
        switch (kycStatus) {
            case "compliant":
                return "text-emerald-600 bg-emerald-100 dark:bg-emerald-900/20"
            case "pending":
                return "text-amber-600 bg-amber-100 dark:bg-amber-900/20"
            case "expired":
                return "text-destructive bg-destructive/10"
            default:
                return "text-muted-foreground"
        }
    }

    const getComplianceScoreColor = (score: number) => {
        if (score >= 90) return "text-emerald-600"
        if (score >= 75) return "text-blue-600"
        if (score >= 60) return "text-amber-600"
        return "text-destructive"
    }

    const activeClients = clients.filter((c) => c.status === "active").length
    const kycPendingCount = clients.filter((c) => c.kycStatus === "pending").length
    const flaggedCount = clients.filter((c) => c.status === "flagged").length

    return (
        <div className="flex min-h-screen flex-col bg-background">
            {/* Header */}
            <div className="border-b border-border bg-card px-6 py-4">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight text-foreground">
                            Client Management
                        </h1>
                        <p className="mt-1 text-sm text-muted-foreground">
                            Manage and review client profiles, KYC status, and compliance information
                        </p>
                    </div>
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
                                        <p className="text-sm text-muted-foreground">Total Clients</p>
                                        <p className="mt-2 text-3xl font-bold">{clients.length}</p>
                                    </div>
                                    <Users className="size-8 text-muted-foreground" />
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-muted-foreground">Active</p>
                                        <p className="mt-2 text-3xl font-bold">{activeClients}</p>
                                    </div>
                                    <CheckCircle2 className="size-8 text-emerald-500" />
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-muted-foreground">KYC Pending</p>
                                        <p className="mt-2 text-3xl font-bold">{kycPendingCount}</p>
                                    </div>
                                    <AlertTriangle className="size-8 text-amber-500" />
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent className="pt-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-muted-foreground">Flagged</p>
                                        <p className="mt-2 text-3xl font-bold">{flaggedCount}</p>
                                    </div>
                                    <AlertCircle className="size-8 text-destructive" />
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Main Content Grid */}
                    <div className="flex flex-col gap-6">
                        {/* Clients List */}
                        <h2 className="text-lg font-semibold text-foreground">Clients ({filteredClients.length})</h2>
                        <div className="shrink-0">
                            <div className="mb-4 space-y-3">
                                <InputGroup className="p-2">
                                    <InputGroupAddon align="inline-start">
                                        <Search />
                                    </InputGroupAddon>
                                    <InputGroupInput type="text"
                                        placeholder="Search by name, email, or country..."
                                        value={searchTerm}
                                        onChange={(e) => setSearchTerm(e.target.value)}
                                    />

                                </InputGroup>
                            </div>
                            <div className="flex gap-4">

                                <div className="flex flex-col gap-3 max-h-dvh overflow-y-auto pr-2">
                                    {filteredClients.map((client) => (
                                        <Card
                                            key={client.id}
                                            className={`cursor-pointer transition-colors hover:bg-accent/50 ${selectedClient?.id === client.id
                                                ? "border-primary ring-2 ring-primary/20"
                                                : ""
                                                }`}
                                            onClick={() => setSelectedClient(client)}
                                        >
                                            <CardContent className="pt-4">
                                                <div className="space-y-2">
                                                    <div className="flex items-start justify-between gap-2">
                                                        <div className="flex-1">
                                                            <h3 className="text-sm font-semibold text-foreground">{client.name}</h3>
                                                            <p className="text-xs text-muted-foreground">{client.type}</p>
                                                        </div>
                                                        <span
                                                            className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium shrink-0 ${getStatusColor(
                                                                client.status
                                                            )}`}
                                                        >
                                                            {client.status}
                                                        </span>
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        <span
                                                            className={`inline-block rounded px-1.5 py-0.5 text-xs font-medium ${getRiskColor(
                                                                client.riskRating
                                                            )}`}
                                                        >
                                                            {client.riskRating} risk
                                                        </span>
                                                        <span
                                                            className={`inline-block rounded px-1.5 py-0.5 text-xs font-medium ${getKycColor(
                                                                client.kycStatus
                                                            )}`}
                                                        >
                                                            {client.kycStatus}
                                                        </span>
                                                    </div>
                                                    <p className="text-xs text-muted-foreground">{client.country}</p>
                                                    {client.isPep && (
                                                        <div className="flex items-center gap-1 text-xs font-semibold text-destructive">
                                                            <Shield className="size-3" />
                                                            PEP
                                                        </div>
                                                    )}
                                                </div>
                                            </CardContent>
                                        </Card>
                                    ))}
                                </div>

                                {/* Client Details */}
                                <div className="w-full max-h-dvh overflow-y-auto">
                                    {selectedClient ? (
                                        <div className="flex flex-col gap-4">
                                            {/* Client Header */}
                                            <Card>
                                                <CardHeader>
                                                    <div className="flex items-start justify-between">
                                                        <div>
                                                            <CardTitle className="text-2xl">{selectedClient.name}</CardTitle>
                                                            <CardDescription className="mt-2">
                                                                {selectedClient.type.charAt(0).toUpperCase() + selectedClient.type.slice(1)} •{" "}
                                                                {selectedClient.country}
                                                            </CardDescription>
                                                        </div>
                                                        <div className="flex gap-2">
                                                            <span
                                                                className={`rounded-full px-3 py-1 text-sm font-medium ${getStatusColor(
                                                                    selectedClient.status
                                                                )}`}
                                                            >
                                                                {selectedClient.status}
                                                            </span>
                                                        </div>
                                                    </div>
                                                </CardHeader>
                                            </Card>

                                            {/* Contact Information */}
                                            <Card>
                                                <CardHeader>
                                                    <CardTitle className="text-base">Contact Information</CardTitle>
                                                </CardHeader>
                                                <CardContent className="space-y-3">
                                                    <div className="flex items-center gap-3">
                                                        <Mail className="size-4 text-muted-foreground" />
                                                        <div>
                                                            <p className="text-xs text-muted-foreground">EMAIL</p>
                                                            <p className="text-sm text-foreground">{selectedClient.email}</p>
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center gap-3">
                                                        <Phone className="size-4 text-muted-foreground" />
                                                        <div>
                                                            <p className="text-xs text-muted-foreground">PHONE</p>
                                                            <p className="text-sm text-foreground">{selectedClient.phone}</p>
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center gap-3">
                                                        <MapPin className="size-4 text-muted-foreground" />
                                                        <div>
                                                            <p className="text-xs text-muted-foreground">LOCATION</p>
                                                            <p className="text-sm text-foreground">{selectedClient.country}</p>
                                                        </div>
                                                    </div>
                                                </CardContent>
                                            </Card>

                                            {/* Compliance & Risk Profile */}
                                            <Card>
                                                <CardHeader>
                                                    <CardTitle className="text-base">Compliance & Risk Profile</CardTitle>
                                                </CardHeader>
                                                <CardContent className="space-y-4">
                                                    <div className="grid gap-4 md:grid-cols-2">
                                                        <div>
                                                            <p className="text-xs text-muted-foreground">RISK RATING</p>
                                                            <p
                                                                className={`mt-1 text-sm font-bold capitalize ${selectedClient.riskRating === "high"
                                                                    ? "text-destructive"
                                                                    : selectedClient.riskRating === "medium"
                                                                        ? "text-amber-600"
                                                                        : "text-emerald-600"
                                                                    }`}
                                                            >
                                                                {selectedClient.riskRating}
                                                            </p>
                                                        </div>
                                                        <div>
                                                            <p className="text-xs text-muted-foreground">COMPLIANCE SCORE</p>
                                                            <p
                                                                className={`mt-1 text-sm font-bold ${getComplianceScoreColor(
                                                                    selectedClient.complianceScore
                                                                )}`}
                                                            >
                                                                {selectedClient.complianceScore}%
                                                            </p>
                                                        </div>
                                                        <div>
                                                            <p className="text-xs text-muted-foreground">KYC STATUS</p>
                                                            <p
                                                                className={`mt-1 text-sm font-bold capitalize ${selectedClient.kycStatus === "expired"
                                                                    ? "text-destructive"
                                                                    : selectedClient.kycStatus === "pending"
                                                                        ? "text-amber-600"
                                                                        : "text-emerald-600"
                                                                    }`}
                                                            >
                                                                {selectedClient.kycStatus}
                                                            </p>
                                                        </div>
                                                        <div>
                                                            <p className="text-xs text-muted-foreground">KYC RENEWAL DATE</p>
                                                            <p className="mt-1 text-sm text-foreground">
                                                                {new Date(selectedClient.kycExpiryDate).toLocaleDateString()}
                                                            </p>
                                                        </div>
                                                    </div>

                                                    <div className="border-t pt-4 space-y-2">
                                                        <div className="flex items-center justify-between">
                                                            <p className="text-xs font-medium text-muted-foreground">PEP STATUS</p>
                                                            <p className="text-sm font-semibold">
                                                                {selectedClient.isPep ? (
                                                                    <span className="text-destructive">YES - Requires Enhanced Due Diligence</span>
                                                                ) : (
                                                                    <span className="text-emerald-600">No</span>
                                                                )}
                                                            </p>
                                                        </div>
                                                        <div className="flex items-center justify-between">
                                                            <p className="text-xs font-medium text-muted-foreground">EDD REQUIRED</p>
                                                            <p className="text-sm font-semibold">
                                                                {selectedClient.eddRequired ? (
                                                                    <span className="text-amber-600">Yes</span>
                                                                ) : (
                                                                    <span className="text-emerald-600">No</span>
                                                                )}
                                                            </p>
                                                        </div>
                                                        {selectedClient.eddRequired && (
                                                            <div className="flex items-center justify-between">
                                                                <p className="text-xs font-medium text-muted-foreground">EDD COMPLETED</p>
                                                                <p className="text-sm font-semibold">
                                                                    {selectedClient.eddCompleted ? (
                                                                        <span className="text-emerald-600">Yes</span>
                                                                    ) : (
                                                                        <span className="text-destructive">No - Action Required</span>
                                                                    )}
                                                                </p>
                                                            </div>
                                                        )}
                                                    </div>
                                                </CardContent>
                                            </Card>

                                            {/* Transaction Activity */}
                                            <Card>
                                                <CardHeader>
                                                    <CardTitle className="text-base">Transaction Activity</CardTitle>
                                                </CardHeader>
                                                <CardContent className="space-y-4">
                                                    <div className="grid gap-4 md:grid-cols-3">
                                                        <div>
                                                            <p className="text-xs text-muted-foreground">TOTAL TRANSACTIONS</p>
                                                            <p className="mt-1 text-2xl font-bold text-foreground">
                                                                {selectedClient.totalTransactions}
                                                            </p>
                                                        </div>
                                                        <div>
                                                            <p className="text-xs text-muted-foreground">TOTAL VOLUME</p>
                                                            <p className="mt-1 text-2xl font-bold text-foreground">
                                                                ${(selectedClient.totalVolume / 1000000).toFixed(1)}M
                                                            </p>
                                                        </div>
                                                        <div>
                                                            <p className="text-xs text-muted-foreground">LAST TRANSACTION</p>
                                                            <p className="mt-1 text-sm text-foreground">
                                                                {new Date(selectedClient.lastTransaction).toLocaleDateString()}
                                                            </p>
                                                        </div>
                                                    </div>
                                                </CardContent>
                                            </Card>

                                            {/* Additional Information */}
                                            {selectedClient.type === "corporate" && (
                                                <Card>
                                                    <CardHeader>
                                                        <CardTitle className="text-base">Corporate Information</CardTitle>
                                                    </CardHeader>
                                                    <CardContent className="space-y-3">
                                                        <div>
                                                            <p className="text-xs font-medium text-muted-foreground">INDUSTRY</p>
                                                            <p className="mt-1 text-sm text-foreground">{selectedClient.industry}</p>
                                                        </div>
                                                        <div>
                                                            <p className="text-xs font-medium text-muted-foreground">REGISTRATION NUMBER</p>
                                                            <p className="mt-1 text-sm text-foreground">{selectedClient.registrationNumber}</p>
                                                        </div>
                                                    </CardContent>
                                                </Card>
                                            )}

                                            {/* Flags & Issues */}
                                            {selectedClient.flags.length > 0 && (
                                                <Card className="border-amber-200 bg-amber-50 dark:border-amber-900/30 dark:bg-amber-900/10">
                                                    <CardHeader>
                                                        <CardTitle className="text-base text-amber-900 dark:text-amber-100">
                                                            Active Flags & Issues
                                                        </CardTitle>
                                                    </CardHeader>
                                                    <CardContent>
                                                        <div className="flex flex-wrap gap-2">
                                                            {selectedClient.flags.map((flag) => (
                                                                <span
                                                                    key={flag}
                                                                    className="inline-block rounded bg-amber-200 px-2.5 py-1 text-xs font-medium text-amber-800 dark:bg-amber-900/30 dark:text-amber-300"
                                                                >
                                                                    {flag}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    </CardContent>
                                                </Card>
                                            )}

                                            {/* Action Buttons */}
                                            <div className="flex gap-2">
                                                <Button className="flex-1">
                                                    <Eye className="mr-2 size-4" />
                                                    View Full Profile
                                                </Button>
                                                <Button variant="outline" className="flex-1">
                                                    <Edit className="mr-2 size-4" />
                                                    Edit Information
                                                </Button>
                                                <Button variant="outline">
                                                    <Download className="mr-2 size-4" />
                                                    Export
                                                </Button>
                                            </div>
                                        </div>
                                    ) : (
                                        <Card>
                                            <CardContent className="flex min-h-96 items-center justify-center pt-6">
                                                <div className="text-center">
                                                    <Users className="mx-auto size-12 text-muted-foreground/30" />
                                                    <p className="mt-4 text-sm text-muted-foreground">
                                                        Select a client to view detailed profile and compliance information
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
        </div>
    )
}

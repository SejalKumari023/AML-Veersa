"use client";

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { getUser } from "~/lib/auth"
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
    Loader2,
    Network,
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
import { env } from "~/env"

const BACKEND_1_API_URL = env.NEXT_PUBLIC_API_URL || "http://localhost:5001/api"

interface Client {
  id: string;
  name: string;
  type: "individual" | "corporate";
  email: string;
  phone: string;
  country: string;
  status: "active" | "dormant" | "flagged" | "archived";
  riskRating: "low" | "medium" | "high";
  kycStatus: "compliant" | "pending" | "expired";
  kycDate: string;
  kycExpiryDate: string;
  isPep: boolean;
  eddRequired: boolean;
  eddCompleted: boolean;
  totalTransactions: number;
  totalVolume: number;
  lastTransaction: string;
  industry?: string;
  registrationNumber?: string;
  complianceScore: number;
  flags: string[];
}

interface BackendCustomer {
    id: string
    customer_id: string
    customer_type: string
    customer_risk_rating: string
    customer_is_pep: boolean
    kyc_last_completed: string | null
    kyc_due_date: string | null
    edd_required: boolean
    edd_performed: boolean
    sow_documented: boolean
    client_risk_profile: string
}

interface RelationshipCustomer {
    customer_id: string
    customer_type: string
    risk_rating: string
}

interface LinkingTransaction {
    transaction_id: string
    amount: number
    currency: string | null
    transaction_date: any
    narrative: string
}

interface AccountInvolved {
    account_number: string
    name: string
    country: string
}

interface CustomerRelationship {
    customer1: RelationshipCustomer
    customer2: RelationshipCustomer
    depth: number
    relationship_strength: string
    linking_transactions: LinkingTransaction[]
    accounts_involved: AccountInvolved[]
}

interface RelationshipResponse {
    query_params: {
        customer_id: string | null
        max_depth: number
        limit: number
    }
    total_relationships: number
    relationships: CustomerRelationship[]
}

export default function FrontOfficePage() {
    const router = useRouter()
    useEffect(() => { if (!getUser()) router.replace("/auth/login") }, [router])
    const [clients, setClients] = useState<Client[]>([])
    const [selectedClient, setSelectedClient] = useState<Client | null>(null)
    const [searchTerm, setSearchTerm] = useState("")
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [relationships, setRelationships] = useState<CustomerRelationship[]>([])
    const [loadingRelationships, setLoadingRelationships] = useState(false)
    const [relationshipsError, setRelationshipsError] = useState<string | null>(null)

    // Helper function to map backend customer data to frontend Client interface
    const mapBackendToClient = (backendCustomer: BackendCustomer): Client => {
        // Determine KYC status
        let kycStatus: "compliant" | "pending" | "expired" = "pending"
        if (backendCustomer.kyc_due_date) {
            const dueDate = new Date(backendCustomer.kyc_due_date)
            const now = new Date()
            if (dueDate < now) {
                kycStatus = "expired"
            } else if (backendCustomer.kyc_last_completed) {
                kycStatus = "compliant"
            }
        }

        // Determine status
        let status: "active" | "dormant" | "flagged" | "archived" = "active"
        if (backendCustomer.customer_is_pep || (backendCustomer.edd_required && !backendCustomer.edd_performed)) {
            status = "flagged"
        } else if (kycStatus === "expired") {
            status = "dormant"
        }

        // Determine flags
        const flags: string[] = []
        if (backendCustomer.customer_is_pep) flags.push("pep_status")
        if (backendCustomer.edd_required) flags.push("edd_required")
        if (backendCustomer.edd_required && !backendCustomer.edd_performed) flags.push("edd_not_completed")
        if (kycStatus === "expired") flags.push("kyc_expired")
        if (backendCustomer.customer_risk_rating.toLowerCase() === "high") flags.push("high_risk")

        // Calculate compliance score based on various factors
        let complianceScore = 100
        if (!backendCustomer.kyc_last_completed) complianceScore -= 20
        if (kycStatus === "expired") complianceScore -= 30
        if (backendCustomer.edd_required && !backendCustomer.edd_performed) complianceScore -= 25
        if (backendCustomer.customer_is_pep && !backendCustomer.edd_performed) complianceScore -= 15
        if (!backendCustomer.sow_documented) complianceScore -= 10

        return {
            id: backendCustomer.id,
            name: backendCustomer.customer_id, // Using customer_id as name since we don't have a name field
            type: backendCustomer.customer_type.toLowerCase() as "individual" | "corporate",
            email: `${backendCustomer.customer_id.toLowerCase().replace(/\s+/g, ".")}@example.com`,
            phone: "+1-555-0000", // Placeholder - not in backend data
            country: "Unknown", // Placeholder - not in backend data
            status,
            riskRating: backendCustomer.customer_risk_rating.toLowerCase() as "low" | "medium" | "high",
            kycStatus,
            kycDate: backendCustomer.kyc_last_completed || "",
            kycExpiryDate: backendCustomer.kyc_due_date || "",
            isPep: backendCustomer.customer_is_pep,
            eddRequired: backendCustomer.edd_required,
            eddCompleted: backendCustomer.edd_performed,
            totalTransactions: 0, // Placeholder - would need to fetch from transactions
            totalVolume: 0, // Placeholder - would need to fetch from transactions
            lastTransaction: "", // Placeholder - would need to fetch from transactions
            industry: backendCustomer.client_risk_profile,
            registrationNumber: backendCustomer.customer_id,
            complianceScore: Math.max(0, complianceScore),
            flags,
        }
    }

    // Fetch customers from the backend
    useEffect(() => {
        const fetchCustomers = async () => {
            try {
                setLoading(true)
                setError(null)
                const response = await fetch(`${BACKEND_1_API_URL}/customers/customers`)

                if (!response.ok) {
                    throw new Error(`Failed to fetch customers: ${response.statusText}`)
                }

                const backendCustomers: BackendCustomer[] = await response.json()
                const mappedClients = backendCustomers.map(mapBackendToClient)
                setClients(mappedClients)
            } catch (err) {
                console.error("Error fetching customers:", err)
                setError(err instanceof Error ? err.message : "Failed to fetch customers")
            } finally {
                setLoading(false)
            }
        }

        fetchCustomers()
    }, [])

    // Fetch relationships when a client is selected
    useEffect(() => {
        const fetchRelationships = async () => {
            if (!selectedClient) {
                setRelationships([])
                return
            }

            try {
                setLoadingRelationships(true)
                setRelationshipsError(null)
                const response = await fetch(
                    `${BACKEND_1_API_URL}/customers/customers/graph/relationships?customer_id=${selectedClient.registrationNumber}&limit=100`
                )

                if (!response.ok) {
                    throw new Error(`Failed to fetch relationships: ${response.statusText}`)
                }

                const data: RelationshipResponse = await response.json()
                setRelationships(data.relationships)
            } catch (err) {
                console.error("Error fetching relationships:", err)
                setRelationshipsError(err instanceof Error ? err.message : "Failed to fetch relationships")
            } finally {
                setLoadingRelationships(false)
            }
        }

        fetchRelationships()
    }, [selectedClient])

  const filteredClients = clients.filter(
    (client) =>
      client.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      client.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      client.country.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  const getStatusColor = (status: Client["status"]) => {
    switch (status) {
      case "active":
        return "text-emerald-600 bg-emerald-100 dark:bg-emerald-900/20";
      case "dormant":
        return "text-blue-600 bg-blue-100 dark:bg-blue-900/20";
      case "flagged":
        return "text-amber-600 bg-amber-100 dark:bg-amber-900/20";
      case "archived":
        return "text-muted-foreground bg-muted";
      default:
        return "text-muted-foreground";
    }
  };

  const getRiskColor = (risk: Client["riskRating"]) => {
    switch (risk) {
      case "high":
        return "text-destructive bg-destructive/10";
      case "medium":
        return "text-amber-600 bg-amber-100 dark:bg-amber-900/20";
      case "low":
        return "text-emerald-600 bg-emerald-100 dark:bg-emerald-900/20";
      default:
        return "text-muted-foreground";
    }
  };

  const getKycColor = (kycStatus: Client["kycStatus"]) => {
    switch (kycStatus) {
      case "compliant":
        return "text-emerald-600 bg-emerald-100 dark:bg-emerald-900/20";
      case "pending":
        return "text-amber-600 bg-amber-100 dark:bg-amber-900/20";
      case "expired":
        return "text-destructive bg-destructive/10";
      default:
        return "text-muted-foreground";
    }
  };

  const getComplianceScoreColor = (score: number) => {
    if (score >= 90) return "text-emerald-600";
    if (score >= 75) return "text-blue-600";
    if (score >= 60) return "text-amber-600";
    return "text-destructive";
  };

  const activeClients = clients.filter((c) => c.status === "active").length;
  const kycPendingCount = clients.filter(
    (c) => c.kycStatus === "pending",
  ).length;
  const flaggedCount = clients.filter((c) => c.status === "flagged").length;

  return (
    <div className="bg-background flex min-h-screen flex-col">
      {/* Header */}
      <div className="border-border bg-card border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-foreground text-3xl font-bold tracking-tight">
              Client Management
            </h1>
            <p className="text-muted-foreground mt-1 text-sm">
              Manage and review client profiles, KYC status, and compliance
              information
            </p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-6">
                {loading ? (
                    <div className="flex min-h-[60vh] items-center justify-center">
                        <div className="text-center">
                            <Loader2 className="mx-auto size-12 animate-spin text-primary" />
                            <p className="mt-4 text-sm text-muted-foreground">Loading clients...</p>
                        </div>
                    </div>
                ) : error ? (
                    <div className="flex min-h-[60vh] items-center justify-center">
                        <Card className="max-w-md">
                            <CardContent className="pt-6">
                                <div className="text-center">
                                    <AlertCircle className="mx-auto size-12 text-destructive" />
                                    <h3 className="mt-4 text-lg font-semibold">Error Loading Clients</h3>
                                    <p className="mt-2 text-sm text-muted-foreground">{error}</p>
                                    <Button
                                        className="mt-4"
                                        onClick={() => window.location.reload()}
                                    >
                                        Retry
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                ) : (
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

                                    <div className="flex w-1/3 min-w-[300px] flex-col gap-3 max-h-dvh overflow-y-auto pr-2">
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
                                                            <div className="flex-1 min-w-0">
                                                                <h3 className="text-sm font-semibold text-foreground truncate" title={client.name}>{client.name}</h3>
                                                                <p className="text-xs text-muted-foreground truncate capitalize">{client.type.replace(/_/g, " ")}</p>
                                                            </div>
                                                            <span
                                                                className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium shrink-0 ${getStatusColor(
                                                                    client.status
                                                                )}`}
                                                            >
                                                                {client.status}
                                                            </span>
                                                        </div>
                                                        <div className="flex flex-wrap items-center gap-2">
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
                                    <div className="flex-1 max-h-dvh overflow-y-auto">
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

                                                {/* Related Customers */}
                                                <Card>
                                                    <CardHeader>
                                                        <div className="flex items-center gap-2">
                                                            <Network className="size-4 text-primary" />
                                                            <CardTitle className="text-base">Related Customers</CardTitle>
                                                        </div>
                                                        <CardDescription>
                                                            Customers connected through shared transactions
                                                        </CardDescription>
                                                    </CardHeader>
                                                    <CardContent>
                                                        {loadingRelationships ? (
                                                            <div className="flex items-center justify-center py-8">
                                                                <Loader2 className="size-6 animate-spin text-muted-foreground" />
                                                                <span className="ml-2 text-sm text-muted-foreground">
                                                                    Loading relationships...
                                                                </span>
                                                            </div>
                                                        ) : relationshipsError ? (
                                                            <div className="rounded-md border border-destructive/20 bg-destructive/10 p-4">
                                                                <div className="flex items-start gap-2">
                                                                    <AlertCircle className="size-5 text-destructive" />
                                                                    <div>
                                                                        <p className="text-sm font-medium text-destructive">
                                                                            Error loading relationships
                                                                        </p>
                                                                        <p className="mt-1 text-xs text-destructive/80">
                                                                            {relationshipsError}
                                                                        </p>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        ) : relationships.length === 0 ? (
                                                            <div className="py-8 text-center">
                                                                <Users className="mx-auto size-8 text-muted-foreground/50" />
                                                                <p className="mt-2 text-sm text-muted-foreground">
                                                                    No related customers found
                                                                </p>
                                                            </div>
                                                        ) : (
                                                            <div className="space-y-4">
                                                                <p className="text-sm text-muted-foreground">
                                                                    Found {relationships.length} related customer
                                                                    {relationships.length !== 1 ? "s" : ""}
                                                                </p>
                                                                <div className="space-y-3">
                                                                    {relationships.map((rel, idx) => (
                                                                        <Card key={idx} className="border-l-4 border-l-primary/50">
                                                                            <CardContent className="pt-4">
                                                                                <div className="space-y-3">
                                                                                    {/* Related Customer Info */}
                                                                                    <div className="flex items-start justify-between">
                                                                                        <div>
                                                                                            <p className="font-semibold text-foreground">
                                                                                                {rel.customer2.customer_id}
                                                                                            </p>
                                                                                            <div className="mt-1 flex items-center gap-2">
                                                                                                <span className="text-xs text-muted-foreground capitalize">
                                                                                                    {rel.customer2.customer_type.replace(/_/g, " ")}
                                                                                                </span>
                                                                                                <span
                                                                                                    className={`inline-block rounded px-1.5 py-0.5 text-xs font-medium ${getRiskColor(
                                                                                                        rel.customer2.risk_rating.toLowerCase() as "low" | "medium" | "high"
                                                                                                    )}`}
                                                                                                >
                                                                                                    {rel.customer2.risk_rating} Risk
                                                                                                </span>
                                                                                            </div>
                                                                                        </div>
                                                                                        <span className="rounded-full bg-primary/10 px-2 py-1 text-xs font-medium text-primary">
                                                                                            {rel.relationship_strength}
                                                                                        </span>
                                                                                    </div>

                                                                                    {/* Linking Transactions */}
                                                                                    <div>
                                                                                        <p className="text-xs font-medium text-muted-foreground">
                                                                                            LINKING TRANSACTIONS ({rel.linking_transactions.length})
                                                                                        </p>
                                                                                        <div className="mt-2 space-y-2">
                                                                                            {rel.linking_transactions.map((txn, txnIdx) => (
                                                                                                <div
                                                                                                    key={txnIdx}
                                                                                                    className="rounded-md bg-muted/50 p-2 text-xs"
                                                                                                >
                                                                                                    <div className="flex items-center justify-between">
                                                                                                        <span className="font-mono text-muted-foreground">
                                                                                                            {txn.transaction_id}
                                                                                                        </span>
                                                                                                        <span className="font-semibold text-foreground">
                                                                                                            ${txn.amount.toLocaleString()}
                                                                                                        </span>
                                                                                                    </div>
                                                                                                    {txn.narrative && (
                                                                                                        <p className="mt-1 text-muted-foreground line-clamp-1">
                                                                                                            {txn.narrative}
                                                                                                        </p>
                                                                                                    )}
                                                                                                </div>
                                                                                            ))}
                                                                                        </div>
                                                                                    </div>

                                                                                    {/* Accounts Involved */}
                                                                                    {rel.accounts_involved.length > 0 && (
                                                                                        <div>
                                                                                            <p className="text-xs font-medium text-muted-foreground">
                                                                                                ACCOUNTS INVOLVED ({rel.accounts_involved.length})
                                                                                            </p>
                                                                                            <div className="mt-2 space-y-1">
                                                                                                {rel.accounts_involved.map((acc, accIdx) => (
                                                                                                    <div
                                                                                                        key={accIdx}
                                                                                                        className="flex items-center justify-between text-xs"
                                                                                                    >
                                                                                                        <div>
                                                                                                            <span className="font-medium text-foreground">
                                                                                                                {acc.name}
                                                                                                            </span>
                                                                                                            <span className="ml-2 text-muted-foreground">
                                                                                                                {acc.country}
                                                                                                            </span>
                                                                                                        </div>
                                                                                                        <span className="font-mono text-muted-foreground">
                                                                                                            {acc.account_number}
                                                                                                        </span>
                                                                                                    </div>
                                                                                                ))}
                                                                                            </div>
                                                                                        </div>
                                                                                    )}
                                                                                </div>
                                                                            </CardContent>
                                                                        </Card>
                                                                    ))}
                                                                </div>
                                                            </div>
                                                        )}
                                                    </CardContent>
                                                </Card>

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
                )}
            </div>
    </div>
  );
}

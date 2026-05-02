"use client"
import * as React from "react"
import { useEffect, useState } from "react"
import { usePathname } from "next/navigation"
import {
    BookOpen,
    Bot,
    Command,
    Frame,
    LifeBuoy,
    Map,
    PieChart,
    Send,
    Settings2,
    SquareTerminal,
    FileText,
    CheckSquare,
    Users,
} from "lucide-react"

import { NavMain } from "~/components/nav-main"
import { NavProjects } from "~/components/nav-projects"
import { NavSecondary } from "~/components/nav-secondary"
import { NavUser } from "~/components/nav-user"
import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
} from "~/components/ui/sidebar"
import { getUser, type User, type UserType } from "~/lib/auth"

const getMenuItemsForUserType = (userType: UserType) => {
    const baseItems: any[] = [
        {
            title: "AI Agent",
            url: "/agent",
            icon: Bot,
            items: [
                { title: "Chat", url: "/agent" },
                { title: "Prompt Editor", url: "/agent?tab=prompts" },
            ],
        },
    ]

    const userTypeItems: Record<UserType, typeof baseItems> = {
        legal: [
            {
                title: "Documents",
                url: "/legal",
                icon: FileText,
                items: [
                    {
                        title: "Regulatory Notices",
                        url: "/legal",
                    },
                    {
                        title: "Document Ingest",
                        url: "/legal/ingest",
                    },
                ],
            },
            ...baseItems,
        ],
        compliance: [
            {
                title: "Compliance Rules",
                url: "/compliance",
                icon: CheckSquare,
                items: [
                    {
                        title: "Rule Management",
                        url: "/compliance",
                    },
                    {
                        title: "Transactions",
                        url: "/compliance/transactions",
                    },
                    {
                        title: "Alerts",
                        url: "/compliance/alerts",
                    },
                    {
                        title: "Documents",
                        url: "/compliance/documents",
                    },
                ],
            },
            ...baseItems,
        ],
        frontoffice: [
            {
                title: "Dashboard",
                url: "/frontoffice",
                icon: PieChart,
                items: [
                    {
                        title: "Overview",
                        url: "/frontoffice",
                    },
                    {
                        title: "Client Verification",
                        url: "/frontoffice/client-verification",
                    },
                ],
            },
            ...baseItems,
        ],
    }

    return userTypeItems[userType] || baseItems
}

const defaultData = {
    user: {
        name: "User",
        email: "user@example.com",
        avatar: "/avatars/default.jpg",
    },
    navMain: [],
    navSecondary: [
        /*
        {
            title: "Support",
            url: "#",
            icon: LifeBuoy,
        },
        {
            title: "Feedback",
            url: "#",
            icon: Send,
        },
        */
    ],
    projects: [],
}

interface AppSidebarState {
    user: User | null
    navMain: Array<{ title: string; url: string; icon: any; items?: Array<{ title: string; url: string }> }>
}

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
    const pathname = usePathname()
    const [state, setState] = useState<AppSidebarState>({
        user: null,
        navMain: [],
    })
    const [loading, setLoading] = useState(true)

    const refreshAuth = () => {
        const authenticatedUser = getUser()
        if (authenticatedUser) {
            setState({
                user: authenticatedUser,
                navMain: getMenuItemsForUserType(authenticatedUser.userType),
            })
        } else {
            setState({ user: null, navMain: [] })
        }
        setLoading(false)
    }

    useEffect(() => {
        refreshAuth()
        window.addEventListener("authChange", refreshAuth)
        return () => window.removeEventListener("authChange", refreshAuth)
    }, [])

    const isPublicPage = pathname === "/" || pathname.startsWith("/auth")

    if (isPublicPage) {
        return (
            <Sidebar {...props}>
                <SidebarHeader>
                    <SidebarMenu>
                        <SidebarMenuItem>
                            <SidebarMenuButton size="lg" asChild>
                                <a href="/">
                                    <div className="grid flex-1 text-left leading-tight">
                                        <span className="text-primary text-2xl font-extrabold tracking-tight">AML</span>
                                    </div>
                                </a>
                            </SidebarMenuButton>
                        </SidebarMenuItem>
                    </SidebarMenu>
                </SidebarHeader>
                <SidebarContent>
                    <div className="text-muted-foreground mt-auto px-4 pb-6 text-xs">
                        <p className="font-medium">Welcome</p>
                        <p className="mt-1">Sign in to access AML & KYC tools</p>
                    </div>
                </SidebarContent>
            </Sidebar>
        )
    }

    if (loading) {
        return (
            <Sidebar {...props}>
                <SidebarContent>
                    <div className="flex items-center justify-center p-4">
                        <p className="text-sm text-muted-foreground">Loading...</p>
                    </div>
                </SidebarContent>
            </Sidebar>
        )
    }

    const displayUser = state.user
        ? {
            name: state.user.name,
            email: state.user.email,
            avatar: "/avatars/default.jpg",
        }
        : defaultData.user
    const navMain = state.navMain

    return (
        <Sidebar {...props}>
            <SidebarHeader>
                <SidebarMenu>
                    <SidebarMenuItem>
                        <SidebarMenuButton size="lg" asChild>
                            <a href="/">
                                <div className="grid flex-1 text-left leading-tight">
                                    <span className="text-primary text-2xl font-extrabold tracking-tight">AML</span>
                                </div>
                            </a>
                        </SidebarMenuButton>
                    </SidebarMenuItem>
                </SidebarMenu>
            </SidebarHeader>
            <SidebarContent>
                {navMain.length > 0 && <NavMain items={navMain} />}
                {defaultData.navSecondary.length > 0 && <NavSecondary items={defaultData.navSecondary} className="mt-auto" />}
            </SidebarContent>
            <SidebarFooter>
                <NavUser user={displayUser} />
            </SidebarFooter>
        </Sidebar>
    )
}

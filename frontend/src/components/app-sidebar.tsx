"use client"
import * as React from "react"
import { useEffect, useState } from "react"
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
    const baseItems = [
        {
            title: "Settings",
            url: "#",
            icon: Settings2,
            items: [
                {
                    title: "General",
                    url: "#",
                },
                {
                    title: "Team",
                    url: "#",
                },
                {
                    title: "Billing",
                    url: "#",
                },
                {
                    title: "Limits",
                    url: "#",
                },
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
                        title: "Contracts",
                        url: "/legal",
                    },
                    {
                        title: "Policies",
                        url: "#",
                    },
                    {
                        title: "Archive",
                        url: "#",
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
                        title: "Users",
                        url: "#",
                    },
                    {
                        title: "Reports",
                        url: "#",
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
    ],
    projects: [],
}

interface AppSidebarState {
    user: User | null
    navMain: Array<{ title: string; url: string; icon: any; items?: Array<{ title: string; url: string }> }>
}

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
    const [state, setState] = useState<AppSidebarState>({
        user: null,
        navMain: [],
    })
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        // Get authenticated user from localStorage
        const authenticatedUser = getUser()

        if (authenticatedUser) {
            const navMain = getMenuItemsForUserType(authenticatedUser.userType)
            setState({
                user: authenticatedUser,
                navMain: navMain,
            })
        } else {
            // Use default data if no user is authenticated
            setState({
                user: null,
                navMain: defaultData.navMain,
            })
        }
        setLoading(false)
    }, [])

    if (loading) {
        return (
            <Sidebar variant="inset" {...props}>
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
        <Sidebar variant="inset" {...props}>
            <SidebarHeader>
                <SidebarMenu>
                    <SidebarMenuItem>
                        <SidebarMenuButton size="lg" asChild>
                            <a href="/">
                                <div className="grid flex-1 text-left text-sm leading-tight">
                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 283.7 55.8" className="text-primary" fill="currentColor">
                                        <path d="M49.07 42.07V13.73H38.51v1.86h4v15.69a13.34 13.34 0 0 1-2.11 7.55 7.39 7.39 0 0 1-6.27 3.32 4.35 4.35 0 0 1-3.21-1.08c-1.3-1.3-1.47-3.58-1.47-5.41V13.73h-9.84v1.86h3.29v20.32c0 3 .7 5.12 2.13 6.56s3.78 2.21 7 2.21c4.82 0 8.53-2.21 10.51-6.21v5.47h10.88v-1.87ZM68.71 42.09V.01H58.44v1.85h3.72v40.23h-3.72v1.85h14.6v-1.85h-4.33zM88.6 42.09V13.73H78.33v1.85h3.72v26.51h-3.72v1.85h14.6v-1.85H88.6zM126.65 42.07V13.73h-10.58v1.86h4v15.69a13.34 13.34 0 0 1-2.11 7.55 7.36 7.36 0 0 1-6.26 3.32 4.35 4.35 0 0 1-3.21-1.08c-1.31-1.3-1.47-3.58-1.47-5.41V13.73h-9.85v1.86h3.3v20.32c0 3 .69 5.12 2.13 6.56s3.78 2.21 7 2.21c4.82 0 8.53-2.21 10.5-6.21v5.47h10.88v-1.87ZM217.07 32.07c0 3.8-.94 6.59-2.88 8.54-2.28 2.27-5.87 3.33-11.31 3.33h-20v-1.87h4.2V1.86h-4.2V.01h19.49c4.15 0 7.08.91 9 2.78 1.64 1.65 2.44 4 2.44 7.33 0 5.15-3 8.46-9 9.85 6.18.82 12.26 3.01 12.26 12.1Zm-10.19-9a7.81 7.81 0 0 0-5.81-2h-6.66v21h5.66c8.24 0 9.35-5.31 9.35-10.51.04-3.96-.8-6.73-2.51-8.44ZM204.11 3.3a5.66 5.66 0 0 0-4.22-1.49h-5.5v17h5c4.94 0 6.78-2.17 6.78-8-.01-2.31-.22-5.64-2.03-7.46ZM282.07 19.39a15.7 15.7 0 0 0-5.48-.23c-5.47.69-8.16 6.61-8.16 12.38v10.53h4v1.85h-14.54v-1.85h4V15.54h-4.33v-1.85h10.88v10.3c3.19-6.82 6.81-10.49 10.51-10.43a15.53 15.53 0 0 1 4.56.73ZM242.33 26.13v5.64c0 4.13-1.91 10.69-7 10.69a3.08 3.08 0 0 1-2.3-.87c-1-1-1.5-2.92-1.5-6 0-5.34 1.17-6.59 4.7-7.65Zm7.13 15.23c-.61-.61-.88-1.79-.88-3.8V22.07c0-3-.67-5-2.09-6.43-1.78-1.78-4.8-2.64-9.24-2.64-3.29 0-11 .73-11 7.54a2.31 2.31 0 0 0 .6 1.72 3.2 3.2 0 0 0 2.37.7 3.26 3.26 0 0 0 2.44-.74 3.49 3.49 0 0 0 .77-2.59 5 5 0 0 1 1.13-3.65c.78-.78 2-1.13 3.83-1.13a4.25 4.25 0 0 1 3.18 1.07c1.25 1.24 1.42 3.59 1.42 5.72v2.43a70.79 70.79 0 0 1-6.59 1.91l-3.66.86c-5.51 1.31-7.87 4-7.87 8.82 0 3.27.68 5.48 2.15 6.94s3.47 2.07 6.37 2.07c4.44 0 7.16-1.32 9.33-4.5 1.07 3.48 3.52 3.76 6.83 3.76h4.8v-1.86c-2.09 0-3.19 0-3.89-.71ZM155.68 21.78v-6.85c-3.7-1.19-5.92-1.93-9-1.93-4.94 0-9.92 2.86-9.92 9.25 0 5.73 4.85 7.53 9.14 9.12 3.7 1.38 7.2 2.68 7.2 6.25 0 3.38-3.34 5.2-6.48 5.2-4.59 0-7.72-2.88-8.4-8.08h-2.31v8a30.37 30.37 0 0 0 10.59 1.94 13.22 13.22 0 0 0 9.23-3.45 8.2 8.2 0 0 0 2.46-6c0-7.15-5.32-9-10-10.53-3.59-1.21-6.69-2.26-6.69-5.45a3.67 3.67 0 0 1 1-2.72 5.4 5.4 0 0 1 3.86-1.32 7 7 0 0 1 4.54 1.41 9.66 9.66 0 0 1 2.73 5.15ZM85.33 8.23a3.85 3.85 0 1 0-3.86-3.85 3.85 3.85 0 0 0 3.86 3.85ZM231.73 8.23a3.85 3.85 0 1 0-3.85-3.85 3.85 3.85 0 0 0 3.85 3.85ZM243.93 8.23a3.85 3.85 0 1 0-3.86-3.85 3.85 3.85 0 0 0 3.86 3.85ZM.68 0v1.86h4v42.12c-.19 5.55-.88 8.93-3.84 9.78l-.82.21v1.76a16.39 16.39 0 0 0 3.61-.28c5.26-1.08 8.21-5.09 8.33-11.32V0Z" />
                                    </svg>
                                </div>
                            </a>
                        </SidebarMenuButton>
                    </SidebarMenuItem>
                </SidebarMenu>
            </SidebarHeader>
            <SidebarContent>
                {navMain.length > 0 && <NavMain items={navMain} />}
                <NavSecondary items={defaultData.navSecondary} className="mt-auto" />
            </SidebarContent>
            <SidebarFooter>
                <NavUser user={displayUser} />
            </SidebarFooter>
        </Sidebar>
    )
}

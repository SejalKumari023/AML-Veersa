import "~/styles/globals.css";

import { type Metadata } from "next";
import { SidebarProvider } from "~/components/ui/sidebar";
import { AppSidebar } from "~/components/app-sidebar";


export const metadata: Metadata = {
    title: "Baerly Awake AML/KYC",
    description: "Created by Baerly Awake",
    icons: [{ rel: "icon", url: "/favicon.ico" }],
};

export default function RootLayout({
    children,
}: Readonly<{ children: React.ReactNode }>) {
    return (
        <html lang="en">
            <body style={{ margin: 0, padding: 0 }}>
                <SidebarProvider>
                    <div style={{ display: "flex", minHeight: "100vh", width: "100vw" }}>
                        <AppSidebar />
                        <div style={{ flex: 1, minWidth: 0, height: "100vh", overflow: "auto" }}>
                            {children}
                        </div>
                    </div>
                </SidebarProvider>
            </body>
        </html>
    );
}

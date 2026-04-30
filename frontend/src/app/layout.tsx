import "~/styles/globals.css";

import { type Metadata } from "next";
import { SidebarProvider } from "~/components/ui/sidebar";
import { AppSidebar } from "~/components/app-sidebar";


export const metadata: Metadata = {
    title: "AML",
    description: "AML & KYC monitoring platform",
    icons: [{ rel: "icon", url: "/favicon.ico" }],
};

export default function RootLayout({
    children,
}: Readonly<{ children: React.ReactNode }>) {
    return (
        <html lang="en">
            <body style={{ margin: 0, padding: 0 }}>
                <SidebarProvider defaultOpen={true}>
                    <AppSidebar />
                    <main style={{ flex: 1, minWidth: 0, height: "100vh", overflow: "auto" }}>
                        {children}
                    </main>
                </SidebarProvider>
            </body>
        </html>
    );
}

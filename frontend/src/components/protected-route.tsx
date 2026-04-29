"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { getUser, type UserType } from "~/lib/auth";

interface ProtectedRouteProps {
    children: ReactNode;
    allowedUserTypes?: UserType[];
    redirectTo?: string;
}

/**
 * Component to protect routes and restrict access based on user type
 * 
 * @example
 * ```tsx
 * // Only allow compliance users
 * <ProtectedRoute allowedUserTypes={["compliance"]}>
 *   <ComplianceDashboard />
 * </ProtectedRoute>
 * 
 * // Allow multiple user types
 * <ProtectedRoute allowedUserTypes={["legal", "compliance"]}>
 *   <SharedFeature />
 * </ProtectedRoute>
 * 
 * // Just check if user is authenticated
 * <ProtectedRoute>
 *   <AnyAuthenticatedUserPage />
 * </ProtectedRoute>
 * ```
 */
export function ProtectedRoute({
    children,
    allowedUserTypes,
    redirectTo = "/auth/login",
}: ProtectedRouteProps) {
    const router = useRouter();

    useEffect(() => {
        const user = getUser();

        // Check if user is authenticated
        if (!user) {
            router.push(redirectTo);
            return;
        }

        // Check if user type is allowed (if specified)
        if (allowedUserTypes && !allowedUserTypes.includes(user.userType)) {
            // Redirect to their appropriate dashboard
            const userDashboards: Record<UserType, string> = {
                legal: "/legal",
                compliance: "/compliance",
                frontoffice: "/frontoffice",
            };
            router.push(userDashboards[user.userType]);
        }
    }, [router, allowedUserTypes, redirectTo]);

    return <>{children}</>;
}

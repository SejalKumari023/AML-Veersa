"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "~/components/ui/button";
import { Input } from "~/components/ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "~/components/ui/card";
import { setUser, type UserType } from "~/lib/auth";

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setError("");
        setIsLoading(true);

        try {
            // TODO: Replace with actual API call to backend
            // For now, this is a mock implementation

            // Simulate API delay
            await new Promise(resolve => setTimeout(resolve, 500));

            // Mock validation - in production, this should be done by the backend
            if (!email || !password) {
                throw new Error("Please enter both email and password");
            }

            // Mock user data - in production, this would come from the backend
            // You can mock different users based on email for testing:
            // legal@example.com -> legal user
            // compliance@example.com -> compliance user
            // frontoffice@example.com -> frontoffice user
            let userType: UserType = "compliance";
            if (email.includes("legal")) {
                userType = "legal";
            } else if (email.includes("frontoffice")) {
                userType = "frontoffice";
            }

            const user = {
                id: Math.random().toString(36).substring(7),
                email: email,
                name: email.split("@")[0] || "User",
                userType: userType,
            };

            // Save user to localStorage
            setUser(user);

            // Redirect based on user type
            switch (userType) {
                case "legal":
                    router.push("/legal");
                    break;
                case "compliance":
                    router.push("/compliance");
                    break;
                case "frontoffice":
                    router.push("/frontoffice");
                    break;
                default:
                    router.push("/");
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to login");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-background p-4">
            <Card className="w-full max-w-md">
                <form onSubmit={handleSubmit}>
                    <CardHeader>
                        <CardTitle className="text-2xl">Login</CardTitle>
                        <CardDescription>
                            Enter your credentials to access your account
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {error && (
                            <div className="bg-destructive/10 border-destructive text-destructive rounded-md border p-3 text-sm">
                                {error}
                            </div>
                        )}
                        <div className="space-y-2">
                            <label htmlFor="email" className="text-sm font-medium">
                                Email
                            </label>
                            <Input
                                id="email"
                                type="email"
                                placeholder="your.email@example.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                disabled={isLoading}
                            />
                        </div>
                        <div className="space-y-2">
                            <label htmlFor="password" className="text-sm font-medium">
                                Password
                            </label>
                            <Input
                                id="password"
                                type="password"
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                disabled={isLoading}
                            />
                        </div>
                        <div className="text-muted-foreground text-xs">
                            <p className="mb-1">For testing, use email patterns:</p>
                            <ul className="list-inside list-disc space-y-0.5">
                                <li>legal@example.com → Legal user</li>
                                <li>compliance@example.com → Compliance user</li>
                                <li>frontoffice@example.com → Front Office user</li>
                            </ul>
                        </div>
                    </CardContent>
                    <CardFooter className="flex flex-col gap-4">
                        <Button type="submit" className="w-full" disabled={isLoading}>
                            {isLoading ? "Logging in..." : "Login"}
                        </Button>
                        <p className="text-muted-foreground text-center text-sm">
                            Don&apos;t have an account?{" "}
                            <Link href="/auth/register" className="text-primary hover:underline">
                                Register
                            </Link>
                        </p>
                    </CardFooter>
                </form>
            </Card>
        </div>
    );
}

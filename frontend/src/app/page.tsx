"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getUser } from "~/lib/auth";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    const user = getUser();
    if (user) {
      switch (user.userType) {
        case "legal": router.replace("/legal"); break;
        case "compliance": router.replace("/compliance"); break;
        case "frontoffice": router.replace("/frontoffice"); break;
      }
    }
  }, [router]);

  return (
    <div className="flex min-h-screen w-full flex-col items-center justify-center">
      <div className="container flex flex-col items-center justify-center gap-12 px-4 py-16">
        <p className="text-primary text-9xl font-extrabold tracking-tight">
          AML
        </p>
        <p className="text-primary text-4xl font-bold tracking-tight">
          Agentic AML and KYC system
        </p>
        <Link
          href="/auth/login"
          className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-md px-8 py-3 text-lg font-semibold transition-colors"
        >
          Login
        </Link>
      </div>
    </div>
  );
}

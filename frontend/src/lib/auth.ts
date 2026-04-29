/**
 * Authentication utility for managing user sessions in the browser
 */

export type UserType = "legal" | "compliance" | "frontoffice";

export interface User {
  id: string;
  email: string;
  name: string;
  userType: UserType;
}

const AUTH_STORAGE_KEY = "baerly_awake_user";

/**
 * Save user data to localStorage
 */
export function setUser(user: User): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(user));
  }
}

/**
 * Get user data from localStorage
 */
export function getUser(): User | null {
  if (typeof window !== "undefined") {
    const stored = localStorage.getItem(AUTH_STORAGE_KEY);
    if (stored) {
      try {
        return JSON.parse(stored) as User;
      } catch (error) {
        console.error("Failed to parse user data:", error);
        return null;
      }
    }
  }
  return null;
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return getUser() !== null;
}

/**
 * Remove user data from localStorage (logout)
 */
export function clearUser(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(AUTH_STORAGE_KEY);
  }
}

/**
 * Get the user type label
 */
export function getUserTypeLabel(userType: UserType): string {
  const labels: Record<UserType, string> = {
    legal: "Legal",
    compliance: "Compliance",
    frontoffice: "Front Office",
  };
  return labels[userType];
}

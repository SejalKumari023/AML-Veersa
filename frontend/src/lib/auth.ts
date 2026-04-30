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

interface StoredUser extends User {
  password: string;
}

const AUTH_STORAGE_KEY = "aml_user";
const USERS_REGISTRY_KEY = "aml_users";

/**
 * Get all registered users from localStorage
 */
function getAllUsers(): StoredUser[] {
  if (typeof window === "undefined") return [];
  try {
    const stored = localStorage.getItem(USERS_REGISTRY_KEY);
    return stored ? (JSON.parse(stored) as StoredUser[]) : [];
  } catch {
    return [];
  }
}

/**
 * Find a registered user by email
 */
export function findUserByEmail(email: string): StoredUser | null {
  return getAllUsers().find((u) => u.email.toLowerCase() === email.toLowerCase()) ?? null;
}

/**
 * Register a new user. Returns an error string if email already exists.
 */
export function registerUser(
  userData: Omit<User, "id">,
  password: string
): { user: User } | { error: string } {
  if (findUserByEmail(userData.email)) {
    return { error: "An account with this email already exists" };
  }
  const user: User = {
    id: Math.random().toString(36).substring(2, 10),
    ...userData,
  };
  const storedUser: StoredUser = { ...user, password };
  const users = getAllUsers();
  users.push(storedUser);
  localStorage.setItem(USERS_REGISTRY_KEY, JSON.stringify(users));
  setUser(user);
  dispatchAuthChange();
  return { user };
}

/**
 * Log in a user by email and password. Returns an error string on failure.
 */
export function loginUser(
  email: string,
  password: string
): { user: User } | { error: string } {
  const storedUser = findUserByEmail(email);
  if (!storedUser) {
    return { error: "No account found with this email" };
  }
  if (storedUser.password !== password) {
    return { error: "Incorrect password" };
  }
  const { password: _pw, ...user } = storedUser;
  setUser(user as User);
  dispatchAuthChange();
  return { user: user as User };
}

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
      } catch {
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
    dispatchAuthChange();
  }
}

/**
 * Dispatch a custom event so components can react to auth state changes
 */
export function dispatchAuthChange(): void {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event("authChange"));
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

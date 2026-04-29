"use client";

import { useState, useEffect } from "react";
import { getUser, setUser as saveUser, clearUser, isAuthenticated, type User } from "~/lib/auth";

/**
 * Hook to manage user authentication state
 * 
 * @example
 * ```tsx
 * const { user, isLoggedIn, logout, updateUser } = useAuth();
 * 
 * if (!isLoggedIn) {
 *   return <div>Please login</div>;
 * }
 * 
 * return <div>Welcome {user.name}! You are a {user.userType} user.</div>;
 * ```
 */
export function useAuth() {
  const [user, setUserState] = useState<User | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    // Initialize user from localStorage on mount
    const storedUser = getUser();
    if (storedUser) {
      setUserState(storedUser);
      setIsLoggedIn(true);
    }
  }, []);

  const logout = () => {
    clearUser();
    setUserState(null);
    setIsLoggedIn(false);
  };

  const updateUser = (newUser: User) => {
    saveUser(newUser);
    setUserState(newUser);
    setIsLoggedIn(true);
  };

  return {
    user,
    isLoggedIn,
    logout,
    updateUser,
  };
}

'use client';  // Add this line to mark the component as a Client Component

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001").replace(/\/$/, "");
const TOKEN_KEY = "peekori_admin_token";

const LandingPage = () => {
  const [status, setStatus] = useState<"checking" | "redirecting" | "idle">("checking");
  const router = useRouter();

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem(TOKEN_KEY);
      if (!token) {
        setStatus("redirecting");
        router.replace('/login');
        return;
      }

      try {
        const response = await fetch(`${API_BASE}/api/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setStatus("redirecting");
        if (response.ok) {
          router.replace('/dashboard');
        } else {
          localStorage.removeItem(TOKEN_KEY);
          router.replace('/login');
        }
      } catch {
        localStorage.removeItem(TOKEN_KEY);
        setStatus("redirecting");
        router.replace('/login');
      }
    };
    checkAuth();
  }, [router]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
      <h1>{status === "redirecting" ? "Redirecting..." : "Checking session..."}</h1>
      <p style={{ marginTop: 8, fontSize: 14, color: "#6b7280" }}>
        If you are not redirected, open <a href="/login">/login</a>.
      </p>
    </div>
  );
};

export default LandingPage;

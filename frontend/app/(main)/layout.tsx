"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { HiMenu, HiX } from "react-icons/hi";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001").replace(/\/$/, "");
const TOKEN_KEY = "peekori_admin_token";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [authorized, setAuthorized] = useState<boolean | null>(null); // Check if the user is authorized
  const router = useRouter(); // Access the Next.js router

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem(TOKEN_KEY);
        if (!token) {
          router.replace("/login");
          return;
        }

        const res = await fetch(`${API_BASE}/api/auth/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!res.ok) {
          localStorage.removeItem(TOKEN_KEY);
          router.replace("/login");
          return;
        }

        setAuthorized(true);
      } catch (err) {
        localStorage.removeItem(TOKEN_KEY);
        router.replace("/login");
      }
    };

    checkAuth();
  }, [router]);


  // Do not render anything until the auth check is complete
  if (authorized === null) {
    return <div>Loading...</div>; // You can show a loading spinner or something
  }

  if (!authorized) {
    return <div>Unauthorized. Redirecting...</div>;
  }

  return (
    <div>
      {/* Mobile header */}
      <div className="md:hidden flex justify-between items-center bg-gray-900 text-white p-4">
        <h1 className="text-lg font-medium">Peekori Admin</h1>
        <button onClick={() => setSidebarOpen(!sidebarOpen)}>
          {sidebarOpen ? <HiX className="h-6 w-6" /> : <HiMenu className="h-6 w-6" />}
        </button>
      </div>

      <div className="flex min-h-screen">
        {/* Sidebar */}
        <aside
          className={`bg-white text-gray-800 w-52 min-h-screen p-6 fixed top-0 left-0 z-50 transform md:translate-x-0 transition-transform duration-200 ease-in-out
            ${sidebarOpen ? "translate-x-0" : "-translate-x-full"} md:relative md:block shadow-lg`}
        >
          <div className="mb-8 pt-4">
            <h2 className="text-xl font-medium mb-2">Peekori Admin</h2>
          </div>

          <nav>
            <ul className="text-sm">
                <li>
                  <Link href="/dashboard" className="block px-3 py-2 rounded hover:bg-gray-800 hover:text-blue-300 font-medium">Dashboard</Link>
                </li>
                <li>
                  <Link href="/orders" className="block px-3 py-2 rounded hover:bg-gray-800 hover:text-blue-300 font-medium">Orders</Link>
                </li>
                <li>
                  <Link href="/jobs" className="block px-3 py-2 rounded hover:bg-gray-800 hover:text-blue-300 font-medium">Jobs</Link>
                </li>
                <li>
                  <Link href="/test" className="block px-3 py-2 rounded hover:bg-gray-800 hover:text-blue-300 font-medium">Test Orders</Link>
                </li>
                <li>
                  <Link href="/rejected-orders" className="block px-3 py-2 rounded hover:bg-gray-800 hover:text-blue-300 font-medium">Rejected Orders</Link>
                </li>
                <li>
                  <Link href="/export" className="block px-3 py-2 rounded hover:bg-gray-800 hover:text-blue-300 font-medium">Export</Link>
                </li>
                <li>
                  <Link href="/razorpay_analysis" className="block px-3 py-2 rounded hover:bg-gray-800 hover:text-blue-300 font-medium">Razorpay Analysis</Link>
                </li>
                <li>
                  <Link href="/Shipment_status" className="block px-3 py-2 rounded hover:bg-gray-800 hover:text-blue-300 font-medium">Shipment Status</Link>
                </li>
                <li>
                  <Link href="/Order_status" className="block px-3 py-2 rounded hover:bg-gray-800 hover:text-blue-300 font-medium">Order Status</Link>
                </li>
                <li>
                  <Link href="/Shipment_orders" className="block px-3 py-2 rounded hover:bg-gray-800 hover:text-blue-300 font-medium">Shipment Orders</Link>
                </li>
                <li>
                  <Link href="/Shipment_KPI" className="block px-3 py-2 rounded hover:bg-gray-800 hover:text-blue-300 font-medium">Fulfillment KPIs</Link>
                </li>
                <li>
                  <Link href="/Bulk_orders" className="block px-3 py-2 rounded hover:bg-gray-800 hover:text-blue-300 font-medium">Bulk Orders</Link>
                </li>
                <li className="mt-3 border-t border-gray-200 pt-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Marketing
                </li>
                <li>
                  <Link href="/campaigns" className="block px-3 py-2 rounded hover:bg-gray-800 hover:text-blue-300 font-medium">Campaigns</Link>
                </li>
                <li>
                  <Link href="/creators" className="block px-3 py-2 rounded hover:bg-gray-800 hover:text-blue-300 font-medium">Creators</Link>
                </li>
                <li>
                  <Link href="/landing-pages" className="block px-3 py-2 rounded hover:bg-gray-800 hover:text-blue-300 font-medium">Landing Pages</Link>
                </li>
                <li>
                  <Link href="/book-manager" className="block px-3 py-2 rounded hover:bg-gray-800 hover:text-blue-300 font-medium">Book Manager</Link>
                </li>
                <li>
                  <Link href="/non-story-manager" className="block px-3 py-2 rounded hover:bg-gray-800 hover:text-blue-300 font-medium">Frame & Sticker Manager</Link>
                </li>
                <li>
                  <Link href="/discount-manager" className="block px-3 py-2 rounded hover:bg-gray-800 hover:text-blue-300 font-medium">Discount Manager</Link>
                </li>
                <li>
                  <Link href="/products" className="block px-3 py-2 rounded hover:bg-gray-800 hover:text-blue-300 font-medium">JSON Config</Link>
                </li>
                <li>
                  <Link href="/commissions" className="block px-3 py-2 rounded hover:bg-gray-800 hover:text-blue-300 font-medium">Commissions</Link>
                </li>
                <li>
                  <Link href="/payouts" className="block px-3 py-2 rounded hover:bg-gray-800 hover:text-blue-300 font-medium">Payouts</Link>
                </li>
              </ul>
          </nav>
        </aside>

        {/* Main content */}
        <main className="flex-1 bg-gray-50 overflow-y-auto p-4 md:p-2 min-h-screen">
          {children}
        </main>
      </div>
    </div>
  );
}

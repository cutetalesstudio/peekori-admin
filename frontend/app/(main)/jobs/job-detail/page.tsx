import { Suspense } from "react";
import JobDetailClient from "./JobDetailClient";

export default function Page() {
  return (
    <Suspense fallback={<div className="p-4">Loading…</div>}>
      <JobDetailClient />
    </Suspense>
  );
}

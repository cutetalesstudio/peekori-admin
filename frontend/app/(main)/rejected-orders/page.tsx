import { Suspense } from "react";

import RejectedOrdersClient from "./RejectedOrdersClient";

export default function Page() {
  return (
    <Suspense fallback={<div className="p-4">Loading…</div>}>
      <RejectedOrdersClient />
    </Suspense>
  );
}

import { Suspense } from "react";

import ShipmentOrdersClient from "./ShipmentOrdersClient";

export default function Page() {
  return (
    <Suspense fallback={<div className="p-4">Loading…</div>}>
      <ShipmentOrdersClient />
    </Suspense>
  );
}

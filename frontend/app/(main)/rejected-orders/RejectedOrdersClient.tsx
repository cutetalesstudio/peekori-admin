"use client";
import OrdersView from "../components/OrdersView";

export default function RejectedOrdersClient() {
  return (
    <OrdersView
      title="Rejected Orders"
      defaultDiscountCode="REJECTED"
      hideDiscountFilter={true}
    />
  );
}

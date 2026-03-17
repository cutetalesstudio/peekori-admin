import OrdersView from "../components/OrdersView";

export default function TestOrdersPage() {
  return <OrdersView
    title="Test Orders"
    defaultDiscountCode="TINA"
    hideDiscountFilter={true}
  />;
}
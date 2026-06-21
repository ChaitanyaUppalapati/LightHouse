import { Outlet } from "react-router-dom";

// App shell. Pages render through <Outlet />. Kept thin so each web task owns its own page.
export default function App() {
  return (
    <div className="min-h-screen">
      <Outlet />
    </div>
  );
}

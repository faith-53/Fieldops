import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext.jsx";
import Layout from "./components/Layout.jsx";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Jobs from "./pages/Jobs.jsx";
import JobDetail from "./pages/JobDetail.jsx";
import Customers from "./pages/Customers.jsx";
import Expenses from "./pages/Expenses.jsx";
import Reports from "./pages/Reports.jsx";
import Users from "./pages/Users.jsx";
import Notifications from "./pages/Notifications.jsx";

function Guard({ children, managerOnly }) {
  const { user, ready, isManager } = useAuth();
  if (!ready) return <div className="p-10 text-forest">Loading FieldOps…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (managerOnly && !isManager) return <Navigate to="/jobs" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <Guard>
            <Layout />
          </Guard>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="jobs" element={<Jobs />} />
        <Route path="jobs/new" element={<Jobs />} />
        <Route path="jobs/:id" element={<JobDetail />} />
        <Route
          path="customers"
          element={
            <Guard managerOnly>
              <Customers />
            </Guard>
          }
        />
        <Route path="expenses" element={<Expenses />} />
        <Route
          path="reports"
          element={
            <Guard managerOnly>
              <Reports />
            </Guard>
          }
        />
        <Route
          path="users"
          element={
            <Guard managerOnly>
              <Users />
            </Guard>
          }
        />
        <Route path="notifications" element={<Notifications />} />
      </Route>
    </Routes>
  );
}

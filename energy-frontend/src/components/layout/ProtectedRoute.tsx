import { Navigate, useLocation } from "react-router-dom";
import { ReactNode } from "react";

interface ProtectedRouteProps {
  children: ReactNode;
}

const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
  const token = localStorage.getItem("token");
  const location = useLocation();

  if (!token) {
    return <Navigate to="/unauthorized" replace state={{ from: location }} />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;

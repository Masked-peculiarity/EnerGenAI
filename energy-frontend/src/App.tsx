import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import ProtectedRoute from "@/components/layout/ProtectedRoute";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { lazy, Suspense } from "react";
import { AuthProvider } from "@/contexts/AuthContext";
const Index = lazy(() => import("./pages/Index"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const NotFound = lazy(() => import("./pages/NotFound"));
const Login = lazy(() => import("./pages/Login"));
const Signup = lazy(() => import("./pages/Signup"));
const Unauthorized = lazy(() => import("./pages/Unauthorized"));
const Forecast = lazy(() => import("./pages/Forecast"));
const Predictor = lazy(() => import("./pages/Predictor"));
const Anomalies = lazy(() => import("./pages/Anomalies"));
const Copilot = lazy(() => import("./pages/Copilot"));
const BillAnalysis = lazy(() => import("./pages/BillAnalysis"));

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <AuthProvider><BrowserRouter>
        <Suspense fallback={<p role="status" className="p-8">Loading workspace...</p>}><Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/index" element={<ProtectedRoute><Index /></ProtectedRoute>} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/unauthorized" element={<Unauthorized />} />
          <Route path="/predict" element={<ProtectedRoute><Predictor /></ProtectedRoute>} />
          <Route path="/forecast" element={<ProtectedRoute><Forecast /></ProtectedRoute>} />
          <Route path="/anomalies" element={<ProtectedRoute><Anomalies /></ProtectedRoute>} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/chatbot" element={<Navigate to="/copilot" replace />} />
          <Route path="/copilot" element={<ProtectedRoute><Copilot /></ProtectedRoute>} />
          <Route path="/bills" element={<ProtectedRoute><BillAnalysis /></ProtectedRoute>} />
          <Route path="/queries" element={<Navigate to="/copilot" replace />} />
          
          <Route path="*" element={<NotFound />} />
        </Routes></Suspense>
      </BrowserRouter></AuthProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;

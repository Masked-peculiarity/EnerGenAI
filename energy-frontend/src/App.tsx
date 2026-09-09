import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import ProtectedRoute from "@/components/layout/ProtectedRoute";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Index from "./pages/Index";
import Predict from "./pages/Predict";
import Dashboard from "./pages/Dashboard";
import Chatbot from "./pages/Chatbot";
import NotFound from "./pages/NotFound";
import Login from "./pages/Login";
import Signup from "./pages/Signup"
import Unauthorized from "./pages/Unauthorized";
import Queries from "./pages/Queries";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={ <Navigate to="/index" replace /> }/>
          <Route path="/index" element={<Index />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/unauthorized" element={<Unauthorized />} />
          <Route path="/predict" element={<ProtectedRoute> <Predict /></ProtectedRoute>} />
          <Route path="/dashboard" element={<ProtectedRoute> <Dashboard /> </ProtectedRoute>} />
          <Route path="/chatbot" element={<ProtectedRoute> <Chatbot /> </ProtectedRoute>} />
          <Route path="/queries" element={<ProtectedRoute> <Queries /> </ProtectedRoute>} />
          
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;

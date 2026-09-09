import PageLayout from "@/components/layout/PageLayout";
import { Button } from "@/components/ui/button";
import { Lock } from "lucide-react";
import { useNavigate } from "react-router-dom";

const Unauthorized = () => {
  const navigate = useNavigate();

  return (
    <PageLayout>
      <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="glass p-10 rounded-2xl text-center max-w-md">
        <Lock className="mx-auto mb-4 text-primary" size={40} />
        <h2 className="text-2xl font-bold mb-2">Login Required</h2>
        <p className="text-muted-foreground mb-6">
          Please login to access features.
        </p>
        <Button onClick={() => navigate("/login")}>
          Go to Login
        </Button>
      </div>
    </div>
    </PageLayout>
  );
};

export default Unauthorized;

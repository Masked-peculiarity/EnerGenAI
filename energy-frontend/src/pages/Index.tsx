import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import PageLayout from "@/components/layout/PageLayout";
import { motion } from "framer-motion";
import {
  Zap,
  BarChart3,
  Brain,
  Leaf,
  ArrowRight,
  ThermometerSun,
  Users,
  Home as HomeIcon,
  Sun
} from "lucide-react";
import { useState, useEffect } from "react";

const features = [
  {
    icon: Brain,
    title: "ML-Powered Predictions",
    description: "Advanced machine learning models analyze your home's energy patterns for accurate consumption forecasts.",
  },
  {
    icon: BarChart3,
    title: "Real-time Analytics",
    description: "Interactive dashboards showing daily, weekly consumption trends and peak usage insights.",
  },
  {
    icon: Leaf,
    title: "Sustainability Focus",
    description: "Track renewable energy usage and get personalized tips to reduce your carbon footprint.",
  },
  {
    icon: Zap,
    title: "Instant Results",
    description: "Get energy predictions in seconds based on temperature, occupancy, and usage patterns.",
  },
];

const inputFeatures = [
  { icon: ThermometerSun, label: "Temperature & Humidity" },
  { icon: Users, label: "Occupancy" },
  { icon: HomeIcon, label: "Square Footage" },
  { icon: Sun, label: "HVAC & Lighting" },
];


const Index = () => {
  const navigate = useNavigate();

  const [isAuthenticated, setIsAuthenticated] = useState(
    !!localStorage.getItem("token"));

  useEffect(() => {
    const syncAuth = () => {
      setIsAuthenticated(!!localStorage.getItem("token"));
    };

    window.addEventListener("storage", syncAuth);
    return () => window.removeEventListener("storage", syncAuth);
  }, []);

  const handleAuthClick = () => {
    if (isAuthenticated) {
      // Logout
      localStorage.removeItem("token");
      setIsAuthenticated(false);
      navigate("/index");
    } else {
      // Login
      navigate("/login");
    }
  };

  return (
    <PageLayout>
      {/* Hero Section */}
      <section className="relative min-h-[80vh] flex items-center justify-center overflow-hidden">
        {/* Background Elements */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-20 left-10 w-72 h-72 bg-primary/10 rounded-full blur-3xl animate-pulse-slow" />
          <div className="absolute bottom-20 right-10 w-96 h-96 bg-accent/10 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: "2s" }} />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-energy-lime/5 rounded-full blur-3xl" />
        </div>

        <div className="text-center max-w-4xl mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium mb-6">
              <Zap className="h-4 w-4" />
              Smart Energy Prediction
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold mb-6 leading-tight"
          >
            Predict Your Home's{" "}
            <span className="gradient-text">Energy Usage</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-sm sm:text-xl text-muted-foreground mb-8 max-w-2xl mx-auto"
          >
            Use machine learning to forecast your energy consumption based on temperature,
            occupancy, and usage patterns. Make smarter decisions for a sustainable future.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            <Link to="/predict">
              <Button variant="hero" size="xl" className="group">
                Predict Energy
                <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
            <Link to="/dashboard">
              <Button variant="outline" size="xl">
                View Dashboard
              </Button>
            </Link>
          </motion.div>
          
          <motion.div className="py-4" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.3 }}>
            <Button variant="outline" size="xl" onClick={handleAuthClick}>
              {isAuthenticated ? "Logout" : "Login"}
            </Button>
          </motion.div>


          {/* Input Features Pills */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="flex flex-wrap gap-3 justify-center mt-12"
          >
            {inputFeatures.map((feature, index) => (
              <div
                key={index}
                className="flex items-center gap-2 px-4 py-2 rounded-full bg-card shadow-soft border border-border/50"
              >
                <feature.icon className="h-4 w-4 text-primary" />
                <span className="text-sm text-muted-foreground">{feature.label}</span>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            Powerful <span className="gradient-text">Capabilities</span>
          </h2>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="group"
            >
              <div className="glass rounded-2xl p-6 h-full hover:shadow-card hover:-translate-y-1 transition-all duration-300">
                <div className="gradient-bg w-12 h-12 rounded-xl flex items-center justify-center mb-4 group-hover:shadow-glow transition-all duration-300">
                  <feature.icon className="h-6 w-6 text-primary-foreground" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-muted-foreground text-sm">{feature.description}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="gradient-bg rounded-3xl p-8 sm:p-12 text-center shadow-glow"
        >
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-primary-foreground mb-4">
            Ready to Predict Your Energy Usage?
          </h2>
          <p className="text-primary-foreground/80 mb-8 max-w-xl mx-auto">
            Enter your home's parameters and get instant predictions by machine learning.
          </p>
          <Link to="/predict">
            <Button variant="glass" size="xl" className="bg-primary-background/50 border-primary-foreground/30">
              Start Predicting
              <ArrowRight className="h-5 w-5" />
            </Button>
          </Link>
        </motion.div>
      </section>
    </PageLayout>
  );
};

export default Index;

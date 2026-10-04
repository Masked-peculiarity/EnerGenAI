import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Zap, BarChart3, MessageCircle, Home, Menu, X, BotMessageSquare } from "lucide-react";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ProfileMenu from "./ProfileMenu";

const navItems = [
  { path: "/index", label: "Home", icon: Home },
  { path: "/forecast", label: "Forecast", icon: Zap },
  { path: "/predict", label: "Predict", icon: Zap },
  { path: "/dashboard", label: "Dashboard", icon: BarChart3 },
  { path: "/anomalies", label: "Unusual usage", icon: BarChart3 },
  { path: "/copilot", label: "Copilot", icon: BotMessageSquare },
  { path: "/bills", label: "Bills", icon: MessageCircle },
];

const Navbar = () => {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 px-4 py-3">
      <nav className="mx-auto max-w-7xl">
        <div className="glass rounded-2xl px-6 py-3 shadow-soft">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link to="/index" className="flex items-center gap-2 group">
              <div className="gradient-bg p-2 rounded-xl group-hover:shadow-glow transition-all duration-300">
                <Zap className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-bold gradient-text hidden sm:block">
                EnerGenAI
              </span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden lg:flex items-center gap-1">
              {navItems.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <Link key={item.path} to={item.path}>
                    <Button
                      variant={isActive ? "default" : "ghost"}
                      size="sm"
                      className={`gap-2 ${isActive ? "" : "text-muted-foreground"}`}
                    >
                      <item.icon className="h-4 w-4" />
                      {item.label}
                    </Button>
                  </Link>
                );
              })}
            </div>

            <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              aria-label="Toggle navigation"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X /> : <Menu />}
            </Button>
            <ProfileMenu />
            </div>
          </div>
        </div>

        {/* Mobile Menu */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="glass rounded-2xl mt-2 p-4 lg:hidden shadow-soft"
            >
              <div className="flex flex-col gap-2">
                {navItems.map((item) => {
                  const isActive = location.pathname === item.path;
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      <Button
                        variant={isActive ? "default" : "ghost"}
                        className="w-full justify-start gap-2"
                      >
                        <item.icon className="h-4 w-4" />
                        {item.label}
                      </Button>
                    </Link>
                  );
                })}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </nav>
    </header>
  );
};

export default Navbar;

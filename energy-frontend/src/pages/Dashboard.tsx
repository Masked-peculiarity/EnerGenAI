import PageLayout from "@/components/layout/PageLayout";
import { motion } from "framer-motion";
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell,
} from "recharts";
import { Zap, TrendingUp, TrendingDown, Activity, Lightbulb, Leaf, Clock, } from "lucide-react";
import { useState, useEffect } from "react";

const API_BASE = import.meta.env.VITE_API_URL;

const Dashboard = () => {

  const [dashboardData, setDashboardData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/dashboard`, {
          method: "GET",
          headers: {
            "Content-type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        });
        const data = await res.json();
        setDashboardData(data);

      } catch (err) {
        console.error("Dashboard fetch failed", err);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, []);

  if (loading || !dashboardData) {
    return (
      <PageLayout>
        <div className="text-center py-20 text-muted-foreground">
          Loading dashboard...
        </div>
      </PageLayout>
    );
  }

  const kpis = [
    {
      title: "Avg Consumption",
      value: dashboardData.kpis.avg_consumption,
      unit: "kWh/day",
      icon: Activity,
    },
    {
      title: "Peak Usage",
      value: dashboardData.kpis.peak_usage,
      unit: "kWh",
      icon: TrendingUp,
    },
    {
      title: "Min Usage",
      value: dashboardData.kpis.min_usage,
      unit: "kWh",
      icon: TrendingDown,
    },
    {
      title: "Renewable Share",
      value: dashboardData.kpis.renewable_share,
      unit: "%",
      icon: Leaf,
    },
  ];

  const dailyData = dashboardData.daily_consumption;

  const baseline =
    dailyData.reduce((sum: number, d: any) => sum + d.value, 0) /
    dailyData.length;

  const trendData = dailyData.map((d: any) => ({
    day: d.day,
    predicted: d.value,
    baseline,
  }));

  const energySourceData = [
    {
      name: "Grid",
      value: Math.max(0, 100 - dashboardData.kpis.renewable_share),
      color: "hsl(210, 90%, 55%)",
    },
    {
      name: "Renewable",
      value: dashboardData.kpis.renewable_share,
      color: "hsl(158, 64%, 40%)",
    },
  ];

  const savingsTips = [
    {
      icon: Lightbulb,
      tip: "Switch to LED bulbs to reduce lighting costs by up to 75%",
    },
    {
      icon: Clock,
      tip: "Off appliances during peak hours",
    },
    {
      icon: Leaf,
      tip: "Consider adding solar panels - average payback is 6-8 years",
    },
  ];

  return (
    <PageLayout>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl sm:text-4xl font-bold mb-2">
          Energy <span className="gradient-text">Dashboard</span>
        </h1>
        <p className="text-muted-foreground">
          Predicted energy usage insights and trends
        </p>
      </motion.div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {kpis.map((kpi, index) => (
          <motion.div
            key={kpi.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="glass rounded-2xl p-5 shadow-soft"
          >
            <div className="gradient-bg p-2 rounded-lg w-fit mb-3">
              <kpi.icon className="h-5 w-5 text-primary-foreground" />
            </div>
            <p className="text-2xl font-bold">
              {kpi.value}
              <span className="text-sm font-normal text-muted-foreground ml-1">
                {kpi.unit}
              </span>
            </p>
            <p className="text-sm text-muted-foreground mt-1">{kpi.title}</p>
          </motion.div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Daily Consumption */}
        <motion.div className="glass rounded-2xl p-6 shadow-card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Zap className="h-5 w-5 text-primary" />
            Daily Predicted Consumption
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={dailyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="value"
                stroke="hsl(158, 64%, 40%)"
                fillOpacity={0.3}
                fill="hsl(158, 64%, 40%)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Predicted vs Trend */}
        <motion.div className="glass rounded-2xl p-6 shadow-card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary" />
            Predicted vs Historical Trend
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Line dataKey="predicted" stroke="hsl(158, 64%, 40%)" />
              <Line
                dataKey="baseline"
                stroke="hsl(210, 90%, 55%)"
                strokeDasharray="5 5"
              />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Peak Hours */}
        <motion.div className="glass rounded-2xl p-6 shadow-card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Clock className="h-5 w-5 text-primary" />
            Peak Usage Hours
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={dashboardData.hourly_profile}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="hsl(173, 58%, 39%)" />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Energy Sources */}
        <motion.div className="glass rounded-2xl p-6 shadow-card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Leaf className="h-5 w-5 text-primary" />
            Energy Sources
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={energySourceData}
                dataKey="value"
                innerRadius={60}
                outerRadius={90}
              >
                {energySourceData.map((e, i) => (
                  <Cell key={i} fill={e.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Tips */}
      <motion.div className="glass rounded-2xl p-6 shadow-card">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Lightbulb className="h-5 w-5 text-primary" />
          Energy Saving Tips
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {savingsTips.map((t, i) => (
            <div key={i} className="flex gap-3 p-4 bg-primary/5 rounded-xl">
              <t.icon className="h-4 w-4 text-primary" />
              <p className="text-sm text-foreground">{t.tip}</p>
            </div>
          ))}
        </div>
      </motion.div>
    </PageLayout>
  );
};

export default Dashboard;
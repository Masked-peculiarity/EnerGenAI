import { useState } from "react";
import PageLayout from "@/components/layout/PageLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { motion, AnimatePresence } from "framer-motion";
import { Zap, Loader2, Sparkles, Upload, UploadCloud } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useRef } from "react";

const API_BASE = import.meta.env.VITE_API_URL;

interface FormData {
  temperature: string;
  humidity: string;
  occupancy: string;
  squareFootage: string;
  renewableEnergy: string;
  hvac: string;
  lighting: string;
  holiday: string;
}

const Predict = () => {
  const { toast } = useToast();
  const [formData, setFormData] = useState<FormData>({
    temperature: "",
    humidity: "",
    occupancy: "",
    squareFootage: "",
    renewableEnergy: "",
    hvac: "on",
    lighting: "on",
    holiday: "no",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [showUploadMenu, setShowUploadMenu] = useState(false);
  const [prediction, setPrediction] = useState<number | null>(null);
  const [csvRows, setCsvRows] = useState<any[]>([]);
  const [csvPredictions, setCsvPredictions] = useState<number[]>([]);
  const [isBatchLoading, setIsBatchLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);


  const handleInputChange = (field: keyof FormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handlePDFUpload = async (file: File) => {
    if (!file.name.endsWith(".pdf")) {
      toast({
        title: "Invalid File",
        description: "Please upload a valid PDF file.",
        variant: "destructive",
      });
      return;
    }

    const formDataPayload = new FormData();
    formDataPayload.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/predict-from-pdf`, {
        method: "POST",
        body: formDataPayload,
      });

      if (!res.ok) throw new Error("PDF processing failed");

      const data = await res.json();

      // Populate inputs
      setFormData({
        temperature: String(data.Temperature || ""),
        humidity: String(data.Humidity || ""),
        occupancy: String(data.Occupancy || ""),
        squareFootage: String(data.SquareFootage || ""),
        renewableEnergy: String(data.RenewableEnergy || ""),
        hvac: data.HVAC === 1 ? "on" : "off",
        lighting: data.Lighting === 1 ? "on" : "off",
        holiday: data.Holiday === 1 ? "yes" : "no",
      });

      toast({
        title: "PDF processed",
        description: "Inputs populated from PDF",
      });

    } catch (err) {
      toast({
        title: "Error",
        description: "Could not extract data from PDF",
        variant: "destructive",
      });
    }
  };

  const handleMultirowCSV = (file: File) => {
    if (!file.name.endsWith(".csv")) {
      toast({
        title: "Invalid File",
        description: "Please upload a CSV file",
        variant: "destructive",
      });
      return;
    }

    const reader = new FileReader();

    reader.onload = async (e) => {
      try {
        const text = e.target?.result as string;
        const lines = text.trim().split("\n");

        if (lines.length < 2) {
          throw new Error("CSV must contain header and data rows");
        }

        const headers = lines[0].split(",").map(h => h.trim());

        const requiredColumns = [
          "Temperature",
          "Humidity",
          "Occupancy",
          "SquareFootage",
          "RenewableEnergy",
          "HVAC",
          "Lighting",
          "Holiday",
        ];

        // validate headers
        const missing = requiredColumns.filter(col => !headers.includes(col));
        if (missing.length > 0) {
          throw new Error(`Missing columns: ${missing.join(", ")}`);
        }

        // parse rows
        const rows = lines.slice(1).map(line => {
          const values = line.split(",").map(v => v.trim());
          const row: any = {};
          headers.forEach((h, i) => (row[h] = values[i]));
          return row;
        });

        setCsvRows(rows);
        setCsvPredictions([]);

        toast({
          title: "CSV Loaded",
          description: `${rows.length} rows detected`,
        });

      } catch (err: any) {
        toast({
          title: "CSV Error",
          description: err.message,
          variant: "destructive",
        });
      }
    };

    reader.readAsText(file);
  };

  const predictCSVRows = async () => {
    setIsBatchLoading(true);
    setCsvPredictions([]);

    const results: number[] = [];

    for (const row of csvRows) {
      const payload = {
        Temperature: Number(row.Temperature),
        Humidity: Number(row.Humidity),
        SquareFootage: Number(row.SquareFootage),
        Occupancy: Number(row.Occupancy),
        RenewableEnergy: Number(row.RenewableEnergy),

        HVACUsage: row.HVAC?.toLowerCase() === "on" ? 1 : 0,
        LightingUsage: row.Lighting?.toLowerCase() === "on" ? 1 : 0,
        Holiday: row.Holiday?.toLowerCase() === "yes" ? 1 : 0,
      };

      try {
        const res = await fetch(`${API_BASE}/predict`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (!res.ok) throw new Error("Prediction failed");

        const data = await res.json();
        results.push(data.predicted_energy);
      } catch (err) {
        console.error("Prediction failed for row:", row);
        results.push(NaN);
      }
    }

    setCsvPredictions(results);
    setIsBatchLoading(false);
  };


  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleMultirowCSV(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };


  const handlePredict = async () => {
    if (
      !formData.temperature ||
      !formData.humidity ||
      !formData.occupancy ||
      !formData.squareFootage
    ) {
      toast({
        title: "Missing Information",
        description: "Please fill in all required fields.",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    setPrediction(null);

    try {
      const payload = {
        Temperature: Number(formData.temperature),
        Humidity: Number(formData.humidity),
        SquareFootage: Number(formData.squareFootage),
        Occupancy: Number(formData.occupancy),
        RenewableEnergy: Number(formData.renewableEnergy || 0),
        HVACUsage: formData.hvac === "on" ? 1 : 0,
        LightingUsage: formData.lighting === "on" ? 1 : 0,
        Holiday: formData.holiday === "yes" ? 1 : 0,
      };

      const response = await fetch(`${API_BASE}/predict`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error("Prediction failed");
      }

      const result = await response.json();
      setPrediction(result.predicted_energy);

      toast({
        title: "Prediction Complete!",
        description: "Energy consumption predicted successfully.",
      });
    } catch (error) {
      console.error(error);
      toast({
        title: "Error",
        description: "Failed to get prediction from server.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };


  return (
    <PageLayout>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-10"
        >
          <h1 className="text-3xl sm:text-4xl font-bold mb-3">
            <span className="gradient-text">Energy Consumption Predictor</span>
          </h1>
          <p className="text-muted-foreground">
            Enter your home's parameters to predict energy usage
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Input Form */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="glass rounded-2xl p-6 shadow-card"
          >
            <div className="flex justify-between">
              <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
                <Zap className="h-5 w-5 text-primary" />
                Input Features
              </h2>
              <div className="relative">
                <Upload
                  className="h-5 w-5 text-primary stroke-[3] cursor-pointer"
                  onClick={() => setShowUploadMenu(prev => !prev)}
                />

                {showUploadMenu && (
                  <div className="absolute right-0 top-7 z-20 bg-background border rounded-md shadow-lg w-32">
                    <button
                      className="w-full px-3 py-2 text-left text-sm hover:bg-muted"
                      onClick={() => document.getElementById("pdfUpload")?.click()}
                    >
                      Upload PDF
                    </button>
                  </div>
                )}
              </div>

              <Input
                id="pdfUpload"
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={(e) => {
                  if (e.target.files?.[0]) {
                    handlePDFUpload(e.target.files[0]);
                    setShowUploadMenu(false);
                  }
                }}
              />
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="temperature">Temperature (°C)</Label>
                  <Input
                    id="temperature"
                    type="number"
                    placeholder="25"
                    value={formData.temperature}
                    onChange={(e) => handleInputChange("temperature", e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="humidity">Humidity (%)</Label>
                  <Input
                    id="humidity"
                    type="number"
                    placeholder="60"
                    value={formData.humidity}
                    onChange={(e) => handleInputChange("humidity", e.target.value)}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="occupancy">Occupancy</Label>
                  <Input
                    id="occupancy"
                    type="number"
                    placeholder="4"
                    value={formData.occupancy}
                    onChange={(e) => handleInputChange("occupancy", e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="squareFootage">Square Footage</Label>
                  <Input
                    id="squareFootage"
                    type="number"
                    placeholder="1500"
                    value={formData.squareFootage}
                    onChange={(e) => handleInputChange("squareFootage", e.target.value)}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="renewableEnergy">Renewable Energy (kWh)</Label>
                <Input
                  id="renewableEnergy"
                  type="number"
                  placeholder="0"
                  value={formData.renewableEnergy}
                  onChange={(e) => handleInputChange("renewableEnergy", e.target.value)}
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>HVAC</Label>
                  <Select
                    value={formData.hvac}
                    onValueChange={(value) => handleInputChange("hvac", value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="on">On</SelectItem>
                      <SelectItem value="off">Off</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Lighting</Label>
                  <Select
                    value={formData.lighting}
                    onValueChange={(value) => handleInputChange("lighting", value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="on">On</SelectItem>
                      <SelectItem value="off">Off</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Holiday</Label>
                  <Select
                    value={formData.holiday}
                    onValueChange={(value) => handleInputChange("holiday", value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="no">Not Holiday</SelectItem>
                      <SelectItem value="yes">Holiday</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Button
                variant="hero"
                size="lg"
                className="w-full mt-4"
                onClick={handlePredict}
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    Predicting...
                  </>
                ) : (
                  <>
                    <Zap className="h-5 w-5" />
                    Predict Energy Used
                  </>
                )}
              </Button>
            </div>
          </motion.div>

          {/* Result Card */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="glass rounded-2xl p-6 shadow-card flex flex-col"
          >
            <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              Prediction Result
            </h2>

            <div className="flex-1 flex items-center justify-center">
              <AnimatePresence mode="wait">
                {isLoading ? (
                  <motion.div
                    key="loading"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="text-center"
                  >
                    <div className="gradient-bg w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4 animate-pulse">
                      <Loader2 className="h-10 w-10 text-primary-foreground animate-spin" />
                    </div>
                    <p className="text-muted-foreground">Analyzing your data...</p>
                  </motion.div>
                ) : prediction !== null ? (
                  <motion.div
                    key="result"
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    className="text-center"
                  >
                    <div className="gradient-bg w-32 h-32 rounded-full flex items-center justify-center mx-auto mb-6 shadow-glow">
                      <Zap className="h-16 w-16 text-primary-foreground" />
                    </div>
                    <p className="text-muted-foreground mb-2">Predicted Energy Usage</p>
                    <p className="text-5xl font-bold gradient-text mb-2">
                      {prediction}
                    </p>
                    <p className="text-xl text-muted-foreground">kWh</p>

                    <div className="mt-8 p-4 bg-primary/10 rounded-xl">
                      <p className="text-sm text-muted-foreground">
                        💡 <strong>Tip:</strong> Consider adjusting HVAC settings or using renewable energy
                        to reduce consumption.
                      </p>
                    </div>
                  </motion.div>
                ) : (
                  <motion.div
                    key="empty"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="text-center"
                  >
                    <div className="w-32 h-32 rounded-full bg-muted flex items-center justify-center mx-auto mb-6">
                      <Zap className="h-16 w-16 text-muted-foreground" />
                    </div>
                    <p className="text-muted-foreground">
                      Enter values to get prediction
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>

        </div>

        <div className="space-y-8 mt-6">

          {/* ===================== CSV UPLOAD ===================== */}
          <motion.div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass rounded-2xl p-8 border border-dashed border-primary/40 text-center cursor-pointer hover:bg-primary/5 transition shadow-card"
            onClick={() => fileInputRef.current?.click()}
          >
            <UploadCloud className="mx-auto h-10 w-10 text-primary mb-4" />

            <p className="text-lg font-semibold">
              Drag & drop CSV file here
            </p>

            <p className="text-sm text-muted-foreground">
              or click to browse
            </p>

            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              hidden
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleMultirowCSV(file);
              }}
            />
          </motion.div>

          {/* ===================== CSV PREVIEW + RESULTS ===================== */}
          {csvRows.length > 0 && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="glass rounded-2xl p-6 shadow-card"
            >
              {/* Header */}
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">
                  CSV Prediction Results
                </h3>

                <Button
                  variant="hero"
                  size="sm"
                  onClick={predictCSVRows}
                  disabled={isBatchLoading}
                >
                  {isBatchLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      Predicting...
                    </>
                  ) : (
                    "Predict Energy Consumption"
                  )}
                </Button>
              </div>

              {/* Table */}
              <div className="overflow-x-auto">
                <table className="min-w-full border border-border rounded-lg overflow-hidden">
                  <thead className="bg-muted">
                    <tr>
                      {Object.keys(csvRows[0]).map((col) => (
                        <th
                          key={col}
                          className="px-4 py-3 text-left text-sm font-medium text-muted-foreground"
                        >
                          {col}
                        </th>
                      ))}
                      <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                        Energy Consumption (kWh)
                      </th>
                    </tr>
                  </thead>

                  <tbody className="divide-y divide-border">
                    {csvRows.map((row, idx) => (
                      <tr key={idx} className="hover:bg-muted/50">
                        {Object.values(row).map((val, i) => (
                          <td key={i} className="px-4 py-2 text-sm">
                            {String(val)}
                          </td>
                        ))}
                        <td className="px-4 py-2 text-sm font-semibold">
                          {csvPredictions[idx] !== undefined ? (
                            <span className="text-primary">
                              {csvPredictions[idx].toFixed(2)}
                            </span>
                          ) : (
                            <span className="text-muted-foreground">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </PageLayout>
  );
};

export default Predict;

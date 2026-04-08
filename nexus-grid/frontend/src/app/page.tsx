"use client";

import { useState } from "react";
import { motion, Variants } from "framer-motion";
import {
  Activity,
  AlertCircle,
  CloudLightning,
  Cpu,
  Database,
  Map as MapIcon,
  Pause,
  Play,
  Zap,
} from "lucide-react";
import AssetRoster from "@/components/AssetRoster";
import DistrictMap from "@/components/DistrictMap";
import LedgerTable from "@/components/LedgerTable";
import OperatorDecisionPanel from "@/components/OperatorDecisionPanel";
import OperationsSummary from "@/components/OperationsSummary";
import TelemetryCharts from "@/components/TelemetryCharts";
import { useSimulationWebSocket } from "@/hooks/useSimulationWebSocket";


export default function Home() {
  const {
    data,
    history,
    isConnected,
    isPaused,
    togglePause,
    triggerEmergency,
    triggerForecast,
  } = useSimulationWebSocket();
  const [activeTab, setActiveTab] = useState<"city" | "economy">("city");

  const containerVars = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.08 },
    },
  };

  const itemVars: Variants = {
    hidden: { opacity: 0, y: 18 },
    show: {
      opacity: 1,
      y: 0,
      transition: { type: "spring", stiffness: 280, damping: 24 },
    },
  };

  return (
    <>
      <div className="mesh-bg" />

      <nav className="top-nav">
        <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="brand-text">
          <div
            style={{
              padding: "8px",
              background: "rgba(59, 130, 246, 0.2)",
              borderRadius: "12px",
            }}
          >
            <Zap size={24} color="var(--neon-cyan)" />
          </div>
          NEXUS GRID
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}
        >
          {data?.engine_mode && (
            <div className="status-badge" style={{ color: "var(--neon-cyan)", background: "rgba(6, 182, 212, 0.1)", boxShadow: "none" }}>
              <Cpu size={12} />
              {data.engine_mode.toUpperCase()}
            </div>
          )}

          {data?.controller_mode && (
            <div
              className="status-badge"
              style={{
                color: data.controller_mode === "dqn" ? "var(--neon-blue)" : "var(--neon-amber)",
                background:
                  data.controller_mode === "dqn"
                    ? "rgba(59, 130, 246, 0.12)"
                    : "rgba(245, 158, 11, 0.12)",
                boxShadow: "none",
              }}
            >
              <Cpu size={12} />
              {data.controller_mode === "dqn" ? "DQN" : "RULE"}
            </div>
          )}

          {data?.operating_context_mode && data.operating_context_mode !== "static" && (
            <div
              className="status-badge"
              style={{
                color: data.operating_context_live ? "var(--neon-green)" : "var(--neon-amber)",
                background: data.operating_context_live
                  ? "rgba(16, 185, 129, 0.1)"
                  : "rgba(245, 158, 11, 0.12)",
                boxShadow: "none",
              }}
            >
              <CloudLightning size={12} />
              {data.operating_context_live ? "LIVE CONTEXT" : "ENRICHED CONTEXT"}
            </div>
          )}

          {data?.forecast_scenario && (
            <div
              className="status-badge"
              style={{
                color: "var(--neon-amber)",
                background: "rgba(245, 158, 11, 0.1)",
                boxShadow: "none",
              }}
            >
              <AlertCircle size={12} />
              {data.forecast_scenario.toUpperCase()} +{data.forecast_steps_left}
            </div>
          )}

          <div
            className="status-badge"
            style={{
              color: isConnected ? "var(--neon-green)" : "var(--neon-red)",
              background: isConnected ? "rgba(16, 185, 129, 0.1)" : "rgba(239, 68, 68, 0.1)",
              boxShadow: "none",
            }}
          >
            <Activity size={12} />
            {isConnected ? "SYSTEM LIVE" : "OFFLINE"}
          </div>
        </motion.div>
      </nav>

      <motion.main className="dashboard-grid" variants={containerVars} initial="hidden" animate="show">
        <div className="main-column">
          <motion.div
            variants={itemVars}
            className="glass-panel"
            style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "18px" }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                gap: "16px",
                flexWrap: "wrap",
              }}
            >
              <div>
                <div style={{ color: "var(--text-muted)", fontSize: "0.76rem", letterSpacing: "0.14em", textTransform: "uppercase" }}>
                  Intelligent Control Room
                </div>
                <h1 style={{ fontSize: "1.5rem", marginTop: "6px" }}>
                  {data?.district_name || "Adaptive Grid District"}
                </h1>
                <div style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "720px", lineHeight: 1.5 }}>
                  Clean operator layout for live weather, carbon, tariff, market, and fleet signals. The websocket stays lean; the dashboard does the interpretation.
                </div>
              </div>

              <div style={{ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
                <button className="btn btn-primary" onClick={togglePause} style={{ minWidth: "138px" }}>
                  {isPaused ? (
                    <>
                      <Play size={18} /> RESUME
                    </>
                  ) : (
                    <>
                      <Pause size={18} /> PAUSE
                    </>
                  )}
                </button>
                <button className="btn btn-outline" onClick={() => triggerForecast("heatwave", 6)}>
                  <CloudLightning size={18} color="var(--neon-amber)" /> Forecast Heatwave
                </button>
                <button className="btn btn-danger" onClick={() => triggerEmergency("carbon_spike")}>
                  <AlertCircle size={18} /> Carbon Spike
                </button>
              </div>
            </div>
          </motion.div>

          <motion.div variants={itemVars}>
            <OperationsSummary payload={data} />
          </motion.div>

          <motion.div
            variants={itemVars}
            className="glass-panel"
            style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: "360px" }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: "16px",
                padding: "20px 20px 0 20px",
                flexWrap: "wrap",
              }}
            >
              <div>
                <div style={{ color: "var(--text-muted)", fontSize: "0.72rem", letterSpacing: "0.14em", textTransform: "uppercase" }}>
                  District Twin
                </div>
                <h3 style={{ fontSize: "1.1rem", marginTop: "4px" }}>
                  {activeTab === "city" ? "Asset Theatre" : "Settlement Theatre"}
                </h3>
              </div>
              <div style={{ display: "flex", gap: "12px" }}>
                <button
                  className={`btn ${activeTab === "city" ? "btn-primary" : "btn-outline"}`}
                  onClick={() => setActiveTab("city")}
                  style={{ padding: "8px 16px" }}
                >
                  <MapIcon size={16} /> District Twin
                </button>
                <button
                  className={`btn ${activeTab === "economy" ? "btn-primary" : "btn-outline"}`}
                  onClick={() => setActiveTab("economy")}
                  style={{ padding: "8px 16px" }}
                >
                  <Database size={16} /> Market Ledger
                </button>
              </div>
            </div>

            <div
              style={{
                flex: 1,
                display: "flex",
                overflow: "hidden",
                border: "1px dashed rgba(255,255,255,0.05)",
                borderRadius: "16px",
                background: "rgba(0,0,0,0.12)",
                margin: "20px",
                minHeight: "300px",
              }}
            >
              {activeTab === "city" && data?.buildings ? (
                <DistrictMap buildings={data.buildings} />
              ) : activeTab === "economy" && data?.buildings ? (
                <LedgerTable buildings={data.buildings} />
              ) : (
                <div style={{ margin: "auto", textAlign: "center", opacity: 0.5 }}>
                  <Cpu size={48} style={{ margin: "0 auto 16px auto" }} />
                  Awaiting Telemetry...
                </div>
              )}
            </div>
          </motion.div>

          <motion.div variants={itemVars} className="glass-panel" style={{ padding: 0, overflow: "hidden", minHeight: "290px" }}>
            {history.length > 0 ? (
              <TelemetryCharts history={history} />
            ) : (
              <div
                style={{
                  display: "flex",
                  minHeight: "290px",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "var(--text-secondary)",
                }}
              >
                Collecting data for charts...
              </div>
            )}
          </motion.div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "24px", minHeight: 0 }}>
          <motion.div variants={itemVars} style={{ minHeight: 0 }}>
            <OperatorDecisionPanel payload={data} />
          </motion.div>
          <motion.div variants={itemVars} style={{ minHeight: 0, flex: 1 }}>
            <AssetRoster buildings={data?.buildings || []} />
          </motion.div>
        </div>
      </motion.main>
    </>
  );
}

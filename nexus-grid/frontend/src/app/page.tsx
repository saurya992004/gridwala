"use client";

import { useState } from "react";
import { motion, AnimatePresence, Variants } from "framer-motion";
import { 
  Zap, Play, Pause, Activity, Cpu, 
  Map as MapIcon, Database, AlertCircle, CloudLightning,
  Car
} from "lucide-react";
import { useSimulationWebSocket } from "@/hooks/useSimulationWebSocket";
import DistrictMap from "@/components/DistrictMap";
import LedgerTable from "@/components/LedgerTable";
import TelemetryCharts from "@/components/TelemetryCharts";

export default function Home() {
  const { 
    data, history, isConnected, isPaused, 
    togglePause, triggerEmergency, triggerForecast 
  } = useSimulationWebSocket();
  const [activeTab, setActiveTab] = useState<"city" | "economy">("city");

  // Animation variants
  const containerVars = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const itemVars: Variants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  return (
    <>
      <div className="mesh-bg" />
      
      {/* Top Navigation */}
      <nav className="top-nav">
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="brand-text"
        >
          <div style={{ padding: "8px", background: "rgba(59, 130, 246, 0.2)", borderRadius: "12px" }}>
            <Zap size={24} color="var(--neon-cyan)" />
          </div>
          NEXUS GRID
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ display: "flex", gap: "16px", alignItems: "center" }}
        >
          {data?.engine_mode && (
            <div
              className="status-badge"
              style={{
                color: "var(--neon-cyan)",
                background: "rgba(6, 182, 212, 0.1)",
                boxShadow: "none",
              }}
            >
              <Cpu size={12} />
              {data.engine_mode.toUpperCase()} ENGINE
            </div>
          )}

          {data?.controller_mode && (
            <div
              className="status-badge"
              style={{
                color: data.controller_mode === "dqn" ? "var(--neon-blue)" : "var(--neon-amber)",
                background: data.controller_mode === "dqn"
                  ? "rgba(59, 130, 246, 0.12)"
                  : "rgba(245, 158, 11, 0.12)",
                boxShadow: "none",
              }}
            >
              <Cpu size={12} />
              {data.controller_mode === "dqn" ? "DQN CONTROL" : "RULE CONTROL"}
            </div>
          )}

          {data?.forecast_scenario && (
            <div style={{ color: "var(--neon-amber)", display: "flex", alignItems: "center", gap: "8px", fontWeight: 600, background: "rgba(245, 158, 11, 0.1)", padding: "8px 16px", borderRadius: "100px" }}>
              <AlertCircle size={18} />
              FORECAST: {data.forecast_scenario.toUpperCase()} IN {data.forecast_steps_left} STEPS
            </div>
          )}

          <div 
            className="status-badge" 
            style={{ 
              color: isConnected ? "var(--neon-green)" : "var(--neon-red)",
              background: isConnected ? "rgba(16, 185, 129, 0.1)" : "rgba(239, 68, 68, 0.1)"
            }}
          >
            <Activity size={12} />
            {isConnected ? "SYSTEM LIVE" : "OFFLINE"}
          </div>
        </motion.div>
      </nav>

      {/* Main Grid */}
      <motion.main 
        className="dashboard-grid"
        variants={containerVars}
        initial="hidden"
        animate="show"
      >
        
        {/* Left/Main Content */}
        <div className="main-column">
          
          {/* Controls Deck */}
          <motion.div variants={itemVars} className="glass-panel" style={{ display: "flex", gap: "16px", alignItems: "center" }}>
            <button className="btn btn-primary" onClick={togglePause} style={{ minWidth: "140px" }}>
              {isPaused ? <><Play size={18} /> RESUME</> : <><Pause size={18} /> PAUSE</>}
            </button>
            <div style={{ width: "1px", height: "30px", background: "var(--panel-border)", margin: "0 8px" }} />
            <button className="btn btn-outline" onClick={() => triggerForecast('heatwave', 6)}>
              <CloudLightning size={18} color="var(--neon-amber)" /> Forecast Heatwave
            </button>
            <button className="btn btn-danger" onClick={() => triggerEmergency('carbon_spike')}>
              <AlertCircle size={18} /> Trigger Carbon Spike
            </button>
          </motion.div>

          {/* Central Visualization Area */}
          <motion.div variants={itemVars} className="glass-panel" style={{ flex: 1, display: "flex", flexDirection: "column" }}>
            <div style={{ display: "flex", gap: "16px", marginBottom: "24px" }}>
               <button 
                className={`btn ${activeTab === 'city' ? 'btn-primary' : 'btn-outline'}`}
                onClick={() => setActiveTab('city')}
                style={{ padding: "8px 16px" }}
               >
                 <MapIcon size={16} /> District Twin
               </button>
               <button 
                className={`btn ${activeTab === 'economy' ? 'btn-primary' : 'btn-outline'}`}
                onClick={() => setActiveTab('economy')}
                style={{ padding: "8px 16px" }}
               >
                 <Database size={16} /> P2P Economy
               </button>
            </div>

            <div style={{ flex: 1, display: "flex", overflow: "hidden", border: "1px dashed rgba(255,255,255,0.05)", borderRadius: "12px", background: "rgba(0,0,0,0.1)" }}>
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

          {/* Bottom Metrics & Charts Bar */}
          <motion.div variants={itemVars} style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "24px" }}>
            
            {/* Stats Block */}
            <div style={{ display: "grid", gridTemplateRows: "repeat(3, 1fr)", gap: "12px" }}>
              <div className="glass-panel metric-card" style={{ padding: "12px" }}>
                <div style={{ color: "var(--text-secondary)", fontSize: "0.8rem", marginBottom: "4px", display: "flex", justifyContent: "space-between" }}>
                  <span>Grid Carbon Intensity</span>
                  <CloudLightning size={14} />
                </div>
                <div className="metric-value" style={{ fontSize: "1.5rem" }}>
                  {data?.carbon_intensity ? data.carbon_intensity.toFixed(3) : "—"} <span style={{fontSize: "0.8rem", color: "var(--text-secondary)"}}>kg/kWh</span>
                </div>
              </div>
              
              <div className="glass-panel metric-card" style={{ padding: "12px" }}>
                <div style={{ color: "var(--text-secondary)", fontSize: "0.8rem", marginBottom: "4px", display: "flex", justifyContent: "space-between" }}>
                  <span>District Net Load</span>
                  <Zap size={14} />
                </div>
                <div className="metric-value" style={{ fontSize: "1.5rem" }}>
                  {data?.district_net_consumption ? data.district_net_consumption.toFixed(2) : "—"} <span style={{fontSize: "0.8rem", color: "var(--text-secondary)"}}>kW</span>
                </div>
              </div>

              <div className="glass-panel metric-card" style={{ padding: "12px" }}>
                <div style={{ color: "var(--text-secondary)", fontSize: "0.8rem", marginBottom: "4px", display: "flex", justifyContent: "space-between" }}>
                  <span>P2P Volume (24h)</span>
                  <Database size={14} />
                </div>
                <div className="metric-value" style={{ fontSize: "1.5rem" }}>
                  {data?.p2p_volume_kwh ? data.p2p_volume_kwh.toFixed(2) : "—"} <span style={{fontSize: "0.8rem", color: "var(--text-secondary)"}}>kWh</span>
                </div>
              </div>
            </div>

            {/* Recharts Block */}
            <div className="glass-panel" style={{ padding: 0, overflow: "hidden", minHeight: "250px" }}>
               {history.length > 0 ? (
                 <TelemetryCharts history={history} />
               ) : (
                 <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', opacity: 0.5 }}>
                   Collecting data for charts...
                 </div>
               )}
            </div>

          </motion.div>
        </div>

        {/* Right Column: AI Cortex Stream */}
        <motion.div variants={itemVars} className="glass-panel" style={{ display: "flex", flexDirection: "column" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", paddingBottom: "16px", borderBottom: "1px solid var(--panel-border)" }}>
            <div style={{ padding: "6px", background: "rgba(139, 92, 246, 0.2)", borderRadius: "8px" }}>
              <Cpu size={18} color="var(--neon-purple)" />
            </div>
            <h3 style={{ fontSize: "1.1rem" }}>Cortex AI Stream</h3>
          </div>
          
          <div style={{ flex: 1, overflowY: "auto", overflowX: "hidden", display: "flex", flexDirection: "column", gap: "12px", paddingTop: "16px" }}>
            <AnimatePresence>
              {data?.rationales?.map((rationale, idx) => {
                
                let severity = "normal";
                let icon = <Zap size={14} color="var(--neon-cyan)" style={{ marginTop: "3px", flexShrink: 0 }} />;
                
                if (rationale.includes("PRE-COGNITION")) {
                  severity = "critical";
                  icon = <AlertCircle size={14} color="var(--neon-red)" style={{ marginTop: "3px", flexShrink: 0 }} />;
                } else if (rationale.includes("spiking") || rationale.includes("disconnected")) {
                  severity = "warning";
                  icon = rationale.includes("disconnected") 
                    ? <Car size={14} color="var(--neon-amber)" style={{ marginTop: "3px", flexShrink: 0 }} />
                    : <CloudLightning size={14} color="var(--neon-amber)" style={{ marginTop: "3px", flexShrink: 0 }} />;
                }

                return (
                  <motion.div 
                    key={idx}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    className={`xai-log-entry ${severity}`}
                  >
                    <div style={{ display: "flex", gap: "8px", marginBottom: "4px" }}>
                      {icon}
                      <strong style={{ fontSize: "0.80rem", letterSpacing: "0.05em", color: "var(--text-secondary)", textTransform: "uppercase" }}>
                        Agent {idx + 1}
                      </strong>
                    </div>
                    <div style={{ fontSize: "0.85rem", lineHeight: 1.5, color: "var(--text-primary)", paddingLeft: "22px" }}>
                      {rationale}
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
            
            {!data?.rationales && (
              <div style={{ opacity: 0.5, textAlign: "center", marginTop: "40px" }}>
                <Activity size={24} style={{ margin: "0 auto 12px auto", opacity: 0.5 }} />
                Waiting for telemetry...
              </div>
            )}
          </div>
        </motion.div>

      </motion.main>
    </>
  );
}

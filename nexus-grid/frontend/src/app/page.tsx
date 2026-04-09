"use client";

import { useEffect, useState } from "react";
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
  Radar,
  Zap,
} from "lucide-react";
import AssetRoster from "@/components/AssetRoster";
import CityTwinLaunchPanel from "@/components/CityTwinLaunchPanel";
import ControlEntitiesPanel from "@/components/ControlEntitiesPanel";
import DistrictMap from "@/components/DistrictMap";
import LedgerTable from "@/components/LedgerTable";
import OperatorDecisionPanel from "@/components/OperatorDecisionPanel";
import OperationsSummary from "@/components/OperationsSummary";
import TelemetryCharts from "@/components/TelemetryCharts";
import TwinProvenancePanel from "@/components/TwinProvenancePanel";
import {
  GeoFeaturedLocation,
  useSimulationWebSocket,
} from "@/hooks/useSimulationWebSocket";

const FALLBACK_FEATURED_LOCATIONS: GeoFeaturedLocation[] = [
  {
    query: "London",
    location: { display_name: "London, England, United Kingdom", city: "London", country: "United Kingdom" },
    recommended_district_type: "mixed_use",
  },
  {
    query: "Boston",
    location: { display_name: "Boston, Massachusetts, United States", city: "Boston", country: "United States" },
    recommended_district_type: "campus",
  },
  {
    query: "Mumbai",
    location: { display_name: "Mumbai, Maharashtra, India", city: "Mumbai", country: "India" },
    recommended_district_type: "industrial",
  },
  {
    query: "Singapore",
    location: { display_name: "Singapore", city: "Singapore", country: "Singapore" },
    recommended_district_type: "mixed_use",
  },
];

export default function Home() {
  const {
    data,
    history,
    isConnected,
    isPaused,
    isTwinLoading,
    twinError,
    togglePause,
    triggerEmergency,
    triggerForecast,
    loadCityTwin,
  } = useSimulationWebSocket();
  const [activeTab, setActiveTab] = useState<"city" | "control" | "economy">("city");
  const [featuredLocations, setFeaturedLocations] = useState<GeoFeaturedLocation[]>(
    FALLBACK_FEATURED_LOCATIONS,
  );

  useEffect(() => {
    let cancelled = false;

    const fetchFeaturedLocations = async () => {
      try {
        const response = await fetch("http://127.0.0.1:8000/api/geo/featured?limit=6");
        if (!response.ok) return;

        const payload = (await response.json()) as {
          featured_locations?: GeoFeaturedLocation[];
        };

        if (!cancelled && Array.isArray(payload.featured_locations) && payload.featured_locations.length) {
          setFeaturedLocations(payload.featured_locations);
        }
      } catch {
        // Keep fallback catalog if the backend is not reachable during first paint.
      }
    };

    fetchFeaturedLocations();
    return () => {
      cancelled = true;
    };
  }, []);

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

  const currentLocationLabel =
    data?.geo_context?.display_name || data?.district_name || "Adaptive Grid District";
  const twinModeLabel =
    data?.atlas_context?.mode === "city_to_twin" ? "CITY TWIN LIVE" : "SANDBOX DISTRICT";

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
          <div
            className="status-badge"
            style={{
              color: data?.atlas_context?.mode === "city_to_twin" ? "var(--neon-purple)" : "var(--text-secondary)",
              background:
                data?.atlas_context?.mode === "city_to_twin"
                  ? "rgba(139, 92, 246, 0.12)"
                  : "rgba(148, 163, 184, 0.1)",
              boxShadow: "none",
            }}
          >
            <Radar size={12} />
            {twinModeLabel}
          </div>

          {data?.engine_mode && (
            <div
              className="status-badge"
              style={{ color: "var(--neon-cyan)", background: "rgba(6, 182, 212, 0.1)", boxShadow: "none" }}
            >
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
                <h1 style={{ fontSize: "1.5rem", marginTop: "6px" }}>{currentLocationLabel}</h1>
                <div style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "720px", lineHeight: 1.5 }}>
                  Mission control for city-to-digital-twin operations. Electricity Maps feeds the external reality; NEXUS GRID turns that location into feeders, asset clusters, and eventually RL-owned control surfaces.
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
            <CityTwinLaunchPanel
              featuredLocations={featuredLocations}
              currentLocationLabel={currentLocationLabel}
              isLaunching={isTwinLoading}
              error={twinError}
              onLaunch={loadCityTwin}
            />
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
                  Digital Twin Theater
                </div>
                <h3 style={{ fontSize: "1.1rem", marginTop: "4px" }}>
                  {activeTab === "city"
                    ? "Asset Theatre"
                    : activeTab === "control"
                      ? "Control Entity Theatre"
                      : "Settlement Theatre"}
                </h3>
              </div>
              <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
                <button
                  className={`btn ${activeTab === "city" ? "btn-primary" : "btn-outline"}`}
                  onClick={() => setActiveTab("city")}
                  style={{ padding: "8px 16px" }}
                >
                  <MapIcon size={16} /> District Twin
                </button>
                <button
                  className={`btn ${activeTab === "control" ? "btn-primary" : "btn-outline"}`}
                  onClick={() => setActiveTab("control")}
                  style={{ padding: "8px 16px" }}
                >
                  <Cpu size={16} /> Control Entities
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
              ) : activeTab === "control" ? (
                <ControlEntitiesPanel controlEntities={data?.control_entities || []} />
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
            <TwinProvenancePanel
              geoContext={data?.geo_context}
              twinSummary={data?.twin_summary}
              topologySummary={data?.topology_summary}
              twinProvenance={data?.twin_provenance}
              dataSources={data?.data_sources}
              warnings={data?.enrichment_warnings}
            />
          </motion.div>
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

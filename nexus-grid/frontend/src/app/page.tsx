"use client";

import { useEffect, useState } from "react";
import { motion, Variants } from "framer-motion";
import {
  Activity,
  AlertCircle,
  CloudLightning,
  Cpu,
  Pause,
  Play,
  Radar,
  Waves,
  Zap,
} from "lucide-react";
import AssetRoster from "@/components/AssetRoster";
import CityTwinLaunchPanel from "@/components/CityTwinLaunchPanel";
import LedgerTable from "@/components/LedgerTable";
import OperatorDecisionPanel from "@/components/OperatorDecisionPanel";
import SignalDock from "@/components/SignalDock";
import TelemetryCharts from "@/components/TelemetryCharts";
import TopologyStressPanel from "@/components/TopologyStressPanel";
import TwinMapCanvas from "@/components/TwinMapCanvas";
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

type IntelView = "decisions" | "trace" | "network" | "fleet" | "market" | "signals";

function intelTabLabel(view: IntelView) {
  if (view === "decisions") return "Decisions";
  if (view === "trace") return "Trace";
  if (view === "network") return "Network";
  if (view === "fleet") return "Fleet";
  if (view === "market") return "Market";
  return "Signals";
}

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
    loadCityTwin,
  } = useSimulationWebSocket();
  const [featuredLocations, setFeaturedLocations] = useState<GeoFeaturedLocation[]>(
    FALLBACK_FEATURED_LOCATIONS,
  );
  const [intelView, setIntelView] = useState<IntelView>("decisions");

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
        // Keep the seeded locations if the backend is offline during first paint.
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
      transition: { staggerChildren: 0.06 },
    },
  };

  const itemVars: Variants = {
    hidden: { opacity: 0, y: 18 },
    show: {
      opacity: 1,
      y: 0,
      transition: { type: "spring", stiffness: 260, damping: 24 },
    },
  };

  const currentLocationLabel =
    data?.geo_context?.display_name || data?.district_name || "Adaptive Grid District";
  const currentLocality =
    data?.geo_context?.city || data?.geo_context?.locality || "Global twin";
  const twinModeLabel =
    data?.atlas_context?.mode === "city_to_twin" ? "CITY TWIN LIVE" : "SANDBOX DISTRICT";

  const renderIntelView = () => {
    if (intelView === "trace") {
      return (
        <TwinProvenancePanel
          geoContext={data?.geo_context}
          twinSummary={data?.twin_summary}
          topologySummary={data?.topology_summary}
          twinProvenance={data?.twin_provenance}
          dataSources={data?.data_sources}
          warnings={data?.enrichment_warnings}
        />
      );
    }

    if (intelView === "network") {
      return (
        <TopologyStressPanel
          topologyRuntime={data?.topology_runtime}
          controlEntities={data?.control_entities || []}
        />
      );
    }

    if (intelView === "fleet") {
      return <AssetRoster buildings={data?.buildings || []} />;
    }

    if (intelView === "market") {
      return (
        <div className="glass-panel" style={{ minHeight: "100%", overflow: "hidden" }}>
          <LedgerTable buildings={data?.buildings || []} />
        </div>
      );
    }

    if (intelView === "signals") {
      return history.length > 0 ? (
        <div className="glass-panel" style={{ minHeight: "100%", overflow: "hidden", padding: 0 }}>
          <TelemetryCharts history={history} />
        </div>
      ) : (
        <div className="glass-panel rail-placeholder">Collecting telemetry for signal charts...</div>
      );
    }

    return <OperatorDecisionPanel payload={data} />;
  };

  return (
    <>
      <div className="mesh-bg" />

      <nav className="top-nav terminal-nav">
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
              style={{
                color: "var(--neon-cyan)",
                background: "rgba(6, 182, 212, 0.1)",
                boxShadow: "none",
              }}
            >
              <Cpu size={12} />
              {data.engine_mode.toUpperCase()}
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
            {isConnected ? "TERMINAL ACTIVE" : "OFFLINE"}
          </div>
        </motion.div>
      </nav>

      <motion.main className="terminal-shell" variants={containerVars} initial="hidden" animate="show">
        <motion.aside variants={itemVars} className="terminal-rail left-rail">
          <CityTwinLaunchPanel
            featuredLocations={featuredLocations}
            currentLocationLabel={currentLocationLabel}
            isLaunching={isTwinLoading}
            error={twinError}
            onLaunch={loadCityTwin}
          />
        </motion.aside>

        <motion.section variants={itemVars} className="map-stage-panel">
          <div className="map-stage-toolbar">
            <div>
              <div className="map-stage-eyebrow">Intelligence Terminal</div>
              <h1 className="map-stage-title">{currentLocality}</h1>
              <div className="map-stage-copy">
                Map-first digital twin view with city launch, feeder constraints, outage drills, and live regional operating context layered into the control room.
              </div>
            </div>

            <div className="map-stage-actions">
              <button className="btn btn-primary" onClick={togglePause} style={{ minWidth: "124px" }}>
                {isPaused ? (
                  <>
                    <Play size={18} /> Resume
                  </>
                ) : (
                  <>
                    <Pause size={18} /> Pause
                  </>
                )}
              </button>
              <button className="btn btn-outline" onClick={() => triggerEmergency("congestion_wave")}>
                <CloudLightning size={18} color="var(--neon-amber)" />
                Congestion
              </button>
              <button className="btn btn-danger" onClick={() => triggerEmergency("feeder_fault")}>
                <AlertCircle size={18} />
                Feeder Fault
              </button>
            </div>
          </div>

          <div className="map-stage-frame">
            <TwinMapCanvas
              geoContext={data?.geo_context}
              buildings={data?.buildings || []}
              controlEntities={data?.control_entities || []}
              twinSummary={data?.twin_summary}
              topologyRuntime={data?.topology_runtime}
            />
          </div>
        </motion.section>

        <motion.aside variants={itemVars} className="terminal-rail right-rail">
          <div className="rail-shell glass-panel">
            <div className="rail-header">
              <div>
                <div className="map-stage-eyebrow">Intelligence Rail</div>
                <div className="rail-title">{intelTabLabel(intelView)}</div>
              </div>
              <div className="rail-status">
                <Waves size={14} />
                Live
              </div>
            </div>

            <div className="rail-tabs">
              {(["decisions", "trace", "network", "fleet", "market", "signals"] as IntelView[]).map((view) => (
                <button
                  key={view}
                  type="button"
                  className={`rail-tab ${intelView === view ? "active" : ""}`}
                  onClick={() => setIntelView(view)}
                >
                  {intelTabLabel(view)}
                </button>
              ))}
            </div>

            <div className="rail-content">{renderIntelView()}</div>
          </div>
        </motion.aside>

        <motion.section variants={itemVars} className="terminal-dock glass-panel">
          <SignalDock payload={data} />
        </motion.section>
      </motion.main>
    </>
  );
}

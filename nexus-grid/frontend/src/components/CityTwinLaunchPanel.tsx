"use client";

import { useState } from "react";
import { Globe2, PlayCircle, Radar, Route } from "lucide-react";
import { CityTwinRequest, GeoFeaturedLocation } from "@/hooks/useSimulationWebSocket";

interface CityTwinLaunchPanelProps {
  featuredLocations: GeoFeaturedLocation[];
  currentLocationLabel?: string;
  isLaunching: boolean;
  error?: string | null;
  onLaunch: (request: CityTwinRequest) => Promise<unknown>;
}

export default function CityTwinLaunchPanel({
  featuredLocations,
  currentLocationLabel,
  isLaunching,
  error,
  onLaunch,
}: CityTwinLaunchPanelProps) {
  const [query, setQuery] = useState("London");
  const [districtType, setDistrictType] = useState("auto");
  const [buildingCount, setBuildingCount] = useState("8");

  const launchSpecificTwin = async (
    nextQuery: string,
    nextDistrictType: string,
    nextBuildingCount: string = buildingCount,
  ) => {
    setQuery(nextQuery);
    setDistrictType(nextDistrictType);
    await onLaunch({
      query: nextQuery,
      districtType: nextDistrictType,
      buildingCount: Number.parseInt(nextBuildingCount, 10),
    });
  };

  const launchCityTwin = async () => {
    try {
      await launchSpecificTwin(query, districtType, buildingCount);
    } catch {
      // Error state is handled by the websocket hook.
    }
  };

  return (
    <div
      className="glass-panel"
      style={{
        padding: "20px",
        display: "flex",
        flexDirection: "column",
        gap: "18px",
        height: "100%",
        overflowY: "auto",
      }}
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
          <div
            style={{
              color: "var(--text-muted)",
              fontSize: "0.72rem",
              letterSpacing: "0.14em",
              textTransform: "uppercase",
            }}
          >
            Phase 2B City Launcher
          </div>
          <h3 style={{ fontSize: "1.12rem", marginTop: "4px" }}>City-To-Twin Control Surface</h3>
          <div style={{ color: "var(--text-secondary)", marginTop: "8px", lineHeight: 1.5, maxWidth: "760px" }}>
            Electricity Maps stays the live signal spine. NEXUS GRID generates the feeder-ready digital twin and the control entities that RL will eventually own.
          </div>
        </div>

        <div
          style={{
            padding: "12px 14px",
            borderRadius: "16px",
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.06)",
            minWidth: "220px",
          }}
        >
          <div style={{ color: "var(--text-muted)", fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            Active Twin
          </div>
          <div style={{ marginTop: "6px", fontFamily: "var(--font-display)", fontWeight: 700 }}>
            {isLaunching ? `Launching ${query}...` : currentLocationLabel || "Residential District"}
          </div>
        </div>
      </div>

      <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
        {featuredLocations.map((item) => (
          <button
            key={`${item.query}-${item.location.display_name}`}
            className={`chip-button ${query === item.query ? "active" : ""}`}
            disabled={isLaunching}
            onClick={() => {
              void launchSpecificTwin(
                item.query,
                item.recommended_district_type || "auto",
                buildingCount,
              ).catch(() => undefined);
            }}
            type="button"
          >
            <Globe2 size={14} />
            {item.location.city || item.query}
          </button>
        ))}
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "12px",
          alignItems: "end",
        }}
      >
        <label style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <span style={{ color: "var(--text-muted)", fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            City Or Coordinates
          </span>
          <div className="control-input">
            <Radar size={16} color="var(--neon-cyan)" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Mumbai, Boston, Nairobi, 19.0760,72.8777"
              style={{ background: "transparent", border: "none", color: "white", outline: "none", width: "100%" }}
            />
          </div>
        </label>

        <label style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <span style={{ color: "var(--text-muted)", fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            Twin Archetype
          </span>
          <select className="control-select" value={districtType} onChange={(event) => setDistrictType(event.target.value)}>
            <option value="auto">Auto</option>
            <option value="residential">Residential</option>
            <option value="mixed_use">Mixed Use</option>
            <option value="industrial">Industrial</option>
            <option value="campus">Campus</option>
          </select>
        </label>

        <label style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <span style={{ color: "var(--text-muted)", fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            Asset Scale
          </span>
          <select className="control-select" value={buildingCount} onChange={(event) => setBuildingCount(event.target.value)}>
            <option value="6">6 assets</option>
            <option value="8">8 assets</option>
            <option value="10">10 assets</option>
            <option value="12">12 assets</option>
          </select>
        </label>

        <button className="btn btn-primary" disabled={isLaunching} onClick={launchCityTwin} type="button">
          <PlayCircle size={18} />
          {isLaunching ? "Launching..." : "Launch Custom Twin"}
        </button>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "12px",
        }}
      >
        <div className="metric-card">
          <div style={{ color: "var(--text-muted)", fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            Signal Spine
          </div>
          <div style={{ marginTop: "8px", fontFamily: "var(--font-display)", fontWeight: 700 }}>
            Electricity Maps + Weather + Tariffs
          </div>
        </div>
        <div className="metric-card">
          <div style={{ color: "var(--text-muted)", fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            Agentization
          </div>
          <div style={{ marginTop: "8px", fontFamily: "var(--font-display)", fontWeight: 700 }}>
            Feeder + Asset Cluster RL
          </div>
        </div>
        <div className="metric-card">
          <div style={{ color: "var(--text-muted)", fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            Topology Seed
          </div>
          <div style={{ marginTop: "8px", fontFamily: "var(--font-display)", fontWeight: 700, display: "flex", gap: "6px", alignItems: "center" }}>
            <Route size={16} color="var(--neon-amber)" />
            Radial feeder twin
          </div>
        </div>
      </div>

      {error && (
        <div
          style={{
            padding: "12px 14px",
            borderRadius: "14px",
            border: "1px solid rgba(239, 68, 68, 0.24)",
            background: "rgba(239, 68, 68, 0.08)",
            color: "#fecaca",
          }}
        >
          {error}
        </div>
      )}
    </div>
  );
}

import { MapPin, Orbit, TriangleAlert } from "lucide-react";
import {
  GeoContext,
  TopologySummary,
  TwinProvenance,
  TwinSummary,
} from "@/hooks/useSimulationWebSocket";

interface TwinProvenancePanelProps {
  geoContext?: GeoContext;
  twinSummary?: TwinSummary;
  topologySummary?: TopologySummary;
  twinProvenance?: TwinProvenance;
  dataSources?: Record<string, string>;
  warnings?: string[];
}

function providerChip(label: string, value: string | undefined, accent: string) {
  return (
    <div
      key={label}
      style={{
        padding: "8px 10px",
        borderRadius: "12px",
        border: "1px solid rgba(255,255,255,0.06)",
        background: "rgba(255,255,255,0.04)",
      }}
    >
      <div style={{ color: "var(--text-muted)", fontSize: "0.68rem", textTransform: "uppercase", letterSpacing: "0.08em" }}>
        {label}
      </div>
      <div style={{ marginTop: "4px", color: accent, fontFamily: "var(--font-display)", fontWeight: 700 }}>
        {value || "pending"}
      </div>
    </div>
  );
}

export default function TwinProvenancePanel({
  geoContext,
  twinSummary,
  topologySummary,
  twinProvenance,
  dataSources,
  warnings,
}: TwinProvenancePanelProps) {
  const inferredLayers = twinProvenance?.inferred_layers || [];
  const liveSignalSpine = twinProvenance?.live_signal_spine || {};

  return (
    <div className="glass-panel" style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "12px" }}>
        <div>
          <div style={{ color: "var(--text-muted)", fontSize: "0.72rem", letterSpacing: "0.14em", textTransform: "uppercase" }}>
            Twin Provenance
          </div>
          <h3 style={{ fontSize: "1.05rem", marginTop: "4px" }}>City-To-Twin Trace</h3>
        </div>
        <div
          style={{
            padding: "10px",
            borderRadius: "14px",
            border: "1px solid rgba(255,255,255,0.06)",
            background: "rgba(255,255,255,0.04)",
          }}
        >
          <Orbit size={18} color="var(--neon-cyan)" />
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "12px" }}>
        <div className="metric-card">
          <div style={{ color: "var(--text-muted)", fontSize: "0.68rem", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            Geography
          </div>
          <div style={{ marginTop: "8px", display: "flex", gap: "8px", alignItems: "center" }}>
            <MapPin size={16} color="var(--neon-amber)" />
            <div style={{ fontFamily: "var(--font-display)", fontWeight: 700 }}>
              {geoContext?.city || geoContext?.locality || "Unknown"}
            </div>
          </div>
          <div style={{ marginTop: "6px", color: "var(--text-secondary)", fontSize: "0.85rem" }}>
            {geoContext?.country || "No country"} {geoContext?.country_code ? `(${geoContext.country_code.toUpperCase()})` : ""}
          </div>
        </div>

        <div className="metric-card">
          <div style={{ color: "var(--text-muted)", fontSize: "0.68rem", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            Twin Scope
          </div>
          <div style={{ marginTop: "8px", fontFamily: "var(--font-display)", fontWeight: 700 }}>
            {twinSummary?.district_type?.replace("_", " ") || "adaptive twin"}
          </div>
          <div style={{ marginTop: "6px", color: "var(--text-secondary)", fontSize: "0.85rem" }}>
            {twinSummary?.n_control_entities || 0} control entities
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: "10px" }}>
        {providerChip("Carbon", liveSignalSpine.carbon, "var(--neon-green)")}
        {providerChip("Weather", liveSignalSpine.weather, "var(--neon-cyan)")}
        {providerChip("Tariff", liveSignalSpine.tariff, "var(--neon-amber)")}
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
          gap: "12px",
        }}
      >
        <div className="metric-card">
          <div style={{ color: "var(--text-muted)", fontSize: "0.68rem", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            Topology
          </div>
          <div style={{ marginTop: "8px", display: "flex", flexDirection: "column", gap: "4px", fontSize: "0.88rem", color: "var(--text-secondary)" }}>
            <div>{topologySummary?.n_feeders || 0} feeders</div>
            <div>{topologySummary?.n_buses || 0} buses</div>
            <div>{topologySummary?.n_lines || 0} lines</div>
          </div>
        </div>
        <div className="metric-card">
          <div style={{ color: "var(--text-muted)", fontSize: "0.68rem", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            Capacity
          </div>
          <div style={{ marginTop: "8px", display: "flex", flexDirection: "column", gap: "4px", fontSize: "0.88rem", color: "var(--text-secondary)" }}>
            <div>{twinSummary?.solar_capacity_kw || 0} kW solar</div>
            <div>{twinSummary?.storage_capacity_kwh || 0} kWh storage</div>
            <div>{twinSummary?.dispatch_capacity_kw || 0} kW dispatch</div>
          </div>
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        <div style={{ color: "var(--text-muted)", fontSize: "0.72rem", letterSpacing: "0.14em", textTransform: "uppercase" }}>
          Inferred Layers
        </div>
        {inferredLayers.length ? (
          inferredLayers.map((layer) => (
            <div
              key={`${layer.layer}-${layer.source}`}
              className="xai-log-entry normal"
              style={{ padding: "12px 14px" }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", gap: "12px" }}>
                <div>
                  <div style={{ fontWeight: 600 }}>{layer.layer.replace("_", " ")}</div>
                  <div style={{ color: "var(--text-secondary)", fontSize: "0.82rem", marginTop: "4px" }}>
                    {layer.source}
                  </div>
                </div>
                <div style={{ color: "var(--neon-cyan)", fontFamily: "var(--font-display)", fontWeight: 700 }}>
                  {typeof layer.confidence === "number" ? `${Math.round(layer.confidence * 100)}%` : "--"}
                </div>
              </div>
            </div>
          ))
        ) : (
          <div style={{ color: "var(--text-secondary)" }}>No provenance layers yet.</div>
        )}
      </div>

      {dataSources && Object.keys(dataSources).length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ color: "var(--text-muted)", fontSize: "0.72rem", letterSpacing: "0.14em", textTransform: "uppercase" }}>
            Runtime Sources
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "10px" }}>
            {Object.entries(dataSources).slice(0, 4).map(([key, value]) => (
              <div key={key} className="metric-card" style={{ padding: "12px" }}>
                <div style={{ color: "var(--text-muted)", fontSize: "0.68rem", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                  {key.replaceAll("_", " ")}
                </div>
                <div style={{ marginTop: "6px", color: "var(--text-secondary)", fontSize: "0.8rem" }}>
                  {value}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {warnings && warnings.length > 0 && (
        <div
          style={{
            padding: "12px 14px",
            borderRadius: "14px",
            background: "rgba(245, 158, 11, 0.08)",
            border: "1px solid rgba(245, 158, 11, 0.2)",
            color: "#fde68a",
            display: "flex",
            gap: "10px",
            alignItems: "flex-start",
          }}
        >
          <TriangleAlert size={16} />
          <div>{warnings[0]}</div>
        </div>
      )}
    </div>
  );
}

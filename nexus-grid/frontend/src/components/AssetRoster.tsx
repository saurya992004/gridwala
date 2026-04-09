import { ArrowDownRight, ArrowUpRight, Battery, Car, Home, Wallet } from "lucide-react";
import { BuildingState } from "@/hooks/useSimulationWebSocket";


function assetState(building: BuildingState) {
  if (building.is_ev_away) return "away";
  if (building.net_electricity_consumption < -0.2) return "exporting";
  if (building.net_electricity_consumption > 0.2) return "importing";
  return "balanced";
}

function formatMetric(value: number | undefined, digits: number) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "--";
  }

  return value.toFixed(digits);
}


export default function AssetRoster({ buildings }: { buildings: BuildingState[] }) {
  const ranked = [...buildings].sort(
    (left, right) =>
      Math.abs(right.net_electricity_consumption) - Math.abs(left.net_electricity_consumption),
  );

  return (
    <div
      className="glass-panel"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "16px",
        padding: "20px",
        minHeight: "320px",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ color: "var(--text-muted)", fontSize: "0.72rem", letterSpacing: "0.14em", textTransform: "uppercase" }}>
            Asset Fleet
          </div>
          <h3 style={{ fontSize: "1.1rem", marginTop: "4px" }}>Operational Roster</h3>
        </div>
        <div
          style={{
            padding: "10px",
            borderRadius: "14px",
            background: "rgba(255,255,255,0.06)",
            border: "1px solid rgba(255,255,255,0.08)",
          }}
        >
          <Battery size={18} color="var(--neon-green)" />
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "10px", overflowY: "auto" }}>
        {ranked.map((building, index) => {
          const state = assetState(building);
          const color =
            state === "exporting"
              ? "var(--neon-green)"
              : state === "importing"
                ? "var(--neon-red)"
                : "var(--text-secondary)";
          const icon = building.type === "ev" ? (
            <Car size={16} color="var(--neon-purple)" />
          ) : (
            <Home size={16} color="var(--neon-blue)" />
          );

          return (
            <div
              key={`${building.id ?? "asset"}-${building.type ?? "node"}-${index}`}
              style={{
                display: "grid",
                gridTemplateColumns: "minmax(0, 1.2fr) minmax(0, 0.8fr) minmax(0, 0.8fr)",
                gap: "12px",
                alignItems: "center",
                padding: "12px 14px",
                borderRadius: "14px",
                background: "rgba(255,255,255,0.03)",
                border: "1px solid rgba(255,255,255,0.06)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "10px", minWidth: 0 }}>
                <div
                  style={{
                    padding: "8px",
                    borderRadius: "12px",
                    background: "rgba(255,255,255,0.04)",
                    border: "1px solid rgba(255,255,255,0.06)",
                  }}
                >
                  {icon}
                </div>
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontWeight: 600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {building.id}
                  </div>
                  <div style={{ color: "var(--text-muted)", fontSize: "0.76rem", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                    {building.type}
                  </div>
                </div>
              </div>

              <div>
                <div style={{ color: "var(--text-muted)", fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                  Power
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "6px", color }}>
                  {state === "exporting" ? <ArrowDownRight size={14} /> : <ArrowUpRight size={14} />}
                  <span style={{ fontFamily: "var(--font-display)", fontWeight: 700 }}>
                    {formatMetric(Math.abs(building.net_electricity_consumption), 2)}
                  </span>
                </div>
              </div>

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "8px" }}>
                <div>
                  <div style={{ color: "var(--text-muted)", fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                    SoC
                  </div>
                  <div style={{ fontFamily: "var(--font-display)", fontWeight: 700 }}>
                    {Math.round(building.battery_soc * 100)}%
                  </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--text-secondary)" }}>
                  <Wallet size={14} />
                  <span style={{ fontFamily: "var(--font-display)", fontWeight: 700 }}>
                    {formatMetric(building.nexus_wallet, 1)}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

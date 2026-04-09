import { Cpu, Network, Zap } from "lucide-react";
import { ControlEntity } from "@/hooks/useSimulationWebSocket";

export default function ControlEntitiesPanel({ controlEntities }: { controlEntities: ControlEntity[] }) {
  if (!controlEntities.length) {
    return (
      <div
        className="glass-panel"
        style={{
          display: "flex",
          minHeight: "320px",
          alignItems: "center",
          justifyContent: "center",
          color: "var(--text-secondary)",
          padding: "24px",
        }}
      >
        No generated control entities yet.
      </div>
    );
  }

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
        gap: "14px",
        padding: "18px",
        width: "100%",
        height: "100%",
        overflowY: "auto",
        alignContent: "start",
      }}
    >
      {controlEntities.map((entity) => (
        <div
          key={entity.id}
          className="glass-panel"
          style={{
            padding: "16px",
            display: "flex",
            flexDirection: "column",
            gap: "12px",
            minHeight: "220px",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "12px" }}>
            <div>
              <div style={{ color: "var(--text-muted)", fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                {entity.role.replaceAll("_", " ")}
              </div>
              <div style={{ marginTop: "4px", fontFamily: "var(--font-display)", fontWeight: 700 }}>
                {entity.label}
              </div>
            </div>
            <div
              style={{
                padding: "8px",
                borderRadius: "12px",
                background: "rgba(59,130,246,0.12)",
                border: "1px solid rgba(59,130,246,0.18)",
              }}
            >
              <Cpu size={16} color="var(--neon-blue)" />
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "6px", color: "var(--text-secondary)", fontSize: "0.84rem" }}>
            <div>Agent class: <span style={{ color: "white" }}>{entity.agent_class}</span></div>
            <div>Feeder: <span style={{ color: "white" }}>{entity.feeder_id || "shared"}</span></div>
            <div>Members: <span style={{ color: "white" }}>{entity.member_buildings.length}</span></div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: "8px" }}>
            <div className="metric-card" style={{ padding: "10px" }}>
              <div style={{ color: "var(--text-muted)", fontSize: "0.66rem", textTransform: "uppercase" }}>Solar</div>
              <div style={{ marginTop: "4px", fontFamily: "var(--font-display)", fontWeight: 700 }}>
                {entity.solar_capacity_kw || 0}
              </div>
            </div>
            <div className="metric-card" style={{ padding: "10px" }}>
              <div style={{ color: "var(--text-muted)", fontSize: "0.66rem", textTransform: "uppercase" }}>Storage</div>
              <div style={{ marginTop: "4px", fontFamily: "var(--font-display)", fontWeight: 700 }}>
                {entity.storage_capacity_kwh || 0}
              </div>
            </div>
            <div className="metric-card" style={{ padding: "10px" }}>
              <div style={{ color: "var(--text-muted)", fontSize: "0.66rem", textTransform: "uppercase" }}>Dispatch</div>
              <div style={{ marginTop: "4px", fontFamily: "var(--font-display)", fontWeight: 700 }}>
                {entity.dispatch_capacity_kw || 0}
              </div>
            </div>
          </div>

          <div
            style={{
              marginTop: "auto",
              padding: "12px",
              borderRadius: "14px",
              background: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.06)",
              color: "var(--text-secondary)",
              fontSize: "0.84rem",
              lineHeight: 1.45,
            }}
          >
            {entity.objective}
          </div>

          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            {entity.member_types.map((memberType) => (
              <div
                key={`${entity.id}-${memberType}`}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "6px 10px",
                  borderRadius: "999px",
                  background: "rgba(16, 185, 129, 0.08)",
                  color: "var(--neon-green)",
                  fontSize: "0.72rem",
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                }}
              >
                {memberType === "ev" ? <Zap size={12} /> : <Network size={12} />}
                {memberType}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

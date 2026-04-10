import { AlertTriangle, Cpu, Gauge, ShieldAlert, Waves } from "lucide-react";
import {
  ControlEntity,
  FeederState,
  TopologyControlSignal,
  TopologyEvent,
  TopologyRuntime,
} from "@/hooks/useSimulationWebSocket";

function statusColor(status: string) {
  if (status === "outage") return "var(--neon-red)";
  if (status === "overload") return "#fb7185";
  if (status === "critical") return "var(--neon-amber)";
  if (status === "warning") return "#facc15";
  return "var(--neon-green)";
}

function percentLabel(value?: number) {
  if (typeof value !== "number" || Number.isNaN(value)) return "--";
  return `${Math.round(value * 100)}%`;
}

function compactKw(value?: number | null) {
  if (typeof value !== "number" || Number.isNaN(value)) return "--";
  return `${value.toFixed(1)} kW`;
}

function eventCard(event: TopologyEvent) {
  return (
    <div
      key={event.id}
      style={{
        padding: "12px 14px",
        borderRadius: "16px",
        border: "1px solid rgba(255,255,255,0.08)",
        background: "rgba(255,255,255,0.04)",
        display: "flex",
        flexDirection: "column",
        gap: "6px",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", alignItems: "center" }}>
        <div style={{ fontWeight: 700 }}>{event.label}</div>
        <div
          style={{
            color: statusColor(event.severity === "critical" ? "outage" : event.severity),
            fontSize: "0.75rem",
            textTransform: "uppercase",
            letterSpacing: "0.08em",
          }}
        >
          {event.severity}
        </div>
      </div>
      <div style={{ color: "var(--text-secondary)", fontSize: "0.84rem", lineHeight: 1.45 }}>
        {event.summary}
      </div>
      <div style={{ color: "var(--text-muted)", fontSize: "0.76rem" }}>
        Target: {event.target} {typeof event.steps_left === "number" ? `· ${event.steps_left} steps left` : ""}
      </div>
    </div>
  );
}

function feederCard(feeder: FeederState) {
  const color = statusColor(feeder.status);
  const width = `${Math.min(100, Math.max(6, (feeder.loading_pct || 0) * 100))}%`;

  return (
    <div
      key={feeder.feeder_id}
      style={{
        padding: "14px",
        borderRadius: "18px",
        border: "1px solid rgba(255,255,255,0.08)",
        background: "rgba(255,255,255,0.04)",
        display: "flex",
        flexDirection: "column",
        gap: "10px",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", alignItems: "center" }}>
        <div>
          <div style={{ color: "var(--text-primary)", fontFamily: "var(--font-display)", fontWeight: 700 }}>
            {feeder.label}
          </div>
          <div style={{ color: "var(--text-muted)", fontSize: "0.76rem" }}>
            {feeder.n_assets || 0} assets · {feeder.line_count || 0} lines
          </div>
        </div>
        <div
          style={{
            color,
            fontSize: "0.76rem",
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            fontWeight: 700,
          }}
        >
          {feeder.status}
        </div>
      </div>

      <div
        style={{
          height: "7px",
          borderRadius: "999px",
          background: "rgba(255,255,255,0.08)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width,
            height: "100%",
            background: color,
            boxShadow: `0 0 18px ${color}`,
          }}
        />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: "10px" }}>
        <div className="metric-card" style={{ padding: "10px" }}>
          <div style={{ color: "var(--text-muted)", fontSize: "0.66rem", textTransform: "uppercase" }}>Loading</div>
          <div style={{ marginTop: "4px", fontFamily: "var(--font-display)", fontWeight: 700 }}>
            {percentLabel(feeder.loading_pct)}
          </div>
        </div>
        <div className="metric-card" style={{ padding: "10px" }}>
          <div style={{ color: "var(--text-muted)", fontSize: "0.66rem", textTransform: "uppercase" }}>Headroom</div>
          <div style={{ marginTop: "4px", fontFamily: "var(--font-display)", fontWeight: 700 }}>
            {compactKw(feeder.headroom_kw)}
          </div>
        </div>
        <div className="metric-card" style={{ padding: "10px" }}>
          <div style={{ color: "var(--text-muted)", fontSize: "0.66rem", textTransform: "uppercase" }}>Constraints</div>
          <div style={{ marginTop: "4px", fontFamily: "var(--font-display)", fontWeight: 700 }}>
            {feeder.constrained_lines || 0}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function TopologyStressPanel({
  topologyRuntime,
  topologyControlSignal,
  activeScenario,
  controlEntities,
}: {
  topologyRuntime?: TopologyRuntime;
  topologyControlSignal?: TopologyControlSignal;
  activeScenario?: string | null;
  controlEntities: ControlEntity[];
}) {
  const events = topologyRuntime?.active_events || [];
  const feeders = topologyRuntime?.feeder_states || [];
  const criticalEntities = controlEntities.slice(0, 4);
  const posture = topologyControlSignal?.controller_posture?.replaceAll("_", " ").toUpperCase();
  const primaryEvent = topologyControlSignal?.primary_event;
  const isPendingEmergency = Boolean(activeScenario && events.length === 0);

  return (
    <div
      className="glass-panel"
      style={{
        padding: "18px",
        display: "flex",
        flexDirection: "column",
        gap: "16px",
        overflowY: "auto",
        minWidth: 0,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", alignItems: "flex-start" }}>
        <div>
          <div style={{ color: "var(--text-muted)", fontSize: "0.72rem", letterSpacing: "0.14em", textTransform: "uppercase" }}>
            Grid Stress
          </div>
          <h3 style={{ fontSize: "1.08rem", marginTop: "4px" }}>Topology And Constraints</h3>
        </div>
        <div
          style={{
            padding: "10px",
            borderRadius: "14px",
            background: "rgba(255,255,255,0.05)",
            border: "1px solid rgba(255,255,255,0.08)",
          }}
        >
          <ShieldAlert size={18} color="var(--neon-amber)" />
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(96px, 1fr))", gap: "10px" }}>
        <div className="metric-card" style={{ padding: "12px" }}>
          <div style={{ color: "var(--text-muted)", fontSize: "0.66rem", textTransform: "uppercase" }}>Stress Index</div>
          <div style={{ marginTop: "4px", fontFamily: "var(--font-display)", fontWeight: 700 }}>
            {percentLabel(topologyRuntime?.system_stress_index)}
          </div>
        </div>
        <div className="metric-card" style={{ padding: "12px" }}>
          <div style={{ color: "var(--text-muted)", fontSize: "0.66rem", textTransform: "uppercase" }}>Constrained Feeders</div>
          <div style={{ marginTop: "4px", fontFamily: "var(--font-display)", fontWeight: 700 }}>
            {topologyRuntime?.constrained_feeders || 0}
          </div>
        </div>
        <div className="metric-card" style={{ padding: "12px" }}>
          <div style={{ color: "var(--text-muted)", fontSize: "0.66rem", textTransform: "uppercase" }}>Overloaded Lines</div>
          <div style={{ marginTop: "4px", fontFamily: "var(--font-display)", fontWeight: 700 }}>
            {topologyRuntime?.overloaded_lines || 0}
          </div>
        </div>
      </div>

      {posture && (
        <div
          style={{
            padding: "12px 14px",
            borderRadius: "16px",
            border: "1px solid rgba(255,255,255,0.08)",
            background:
              topologyControlSignal?.controller_posture === "resilience_priority"
                ? "rgba(127, 29, 29, 0.22)"
                : "rgba(8, 47, 73, 0.22)",
            display: "flex",
            flexDirection: "column",
            gap: "6px",
          }}
        >
          <div style={{ color: "var(--text-muted)", fontSize: "0.72rem", letterSpacing: "0.14em", textTransform: "uppercase" }}>
            Control Posture
          </div>
          <div style={{ fontFamily: "var(--font-display)", fontWeight: 700 }}>
            {posture}
          </div>
          <div style={{ color: "var(--text-secondary)", fontSize: "0.84rem", lineHeight: 1.45 }}>
            {primaryEvent?.summary ||
              "The controller posture shifts between economic optimization and feeder-resilience protection based on live topology stress."}
          </div>
        </div>
      )}

      {events.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <div style={{ color: "var(--text-muted)", fontSize: "0.72rem", letterSpacing: "0.14em", textTransform: "uppercase" }}>
            Active Events
          </div>
          {events.map(eventCard)}
        </div>
      )}

      {isPendingEmergency && (
        <div
          style={{
            padding: "12px 14px",
            borderRadius: "16px",
            border: "1px solid rgba(245, 158, 11, 0.22)",
            background: "rgba(245, 158, 11, 0.1)",
            color: "#fde68a",
            display: "flex",
            gap: "10px",
            alignItems: "flex-start",
            lineHeight: 1.45,
          }}
        >
          <AlertTriangle size={16} style={{ marginTop: "2px", flexShrink: 0 }} />
          <div>
            <div style={{ fontWeight: 700 }}>Emergency command is armed</div>
            <div style={{ color: "var(--text-secondary)", fontSize: "0.84rem", marginTop: "4px" }}>
              The runtime has not acknowledged the event yet. If the simulation is paused, press Resume. If this does not clear quickly, use Clear Emergency and inject it again.
            </div>
          </div>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "10px", minWidth: 0 }}>
        <div style={{ color: "var(--text-muted)", fontSize: "0.72rem", letterSpacing: "0.14em", textTransform: "uppercase" }}>
          Feeder States
        </div>
        {feeders.length ? feeders.map(feederCard) : (
          <div style={{ color: "var(--text-secondary)", lineHeight: 1.45 }}>
            {isPendingEmergency
              ? "Waiting for backend feeder metrics to acknowledge the injected event."
              : "Feeder runtime metrics will appear after the simulation starts."}
          </div>
        )}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        <div style={{ color: "var(--text-muted)", fontSize: "0.72rem", letterSpacing: "0.14em", textTransform: "uppercase" }}>
          Control Surface
        </div>
        {criticalEntities.length ? criticalEntities.map((entity) => (
          <div
            key={entity.id}
            style={{
              padding: "12px 14px",
              borderRadius: "16px",
              background: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.06)",
              display: "flex",
              justifyContent: "space-between",
              gap: "12px",
              alignItems: "center",
            }}
          >
            <div>
              <div style={{ fontWeight: 700 }}>{entity.label}</div>
              <div style={{ color: "var(--text-secondary)", fontSize: "0.82rem", marginTop: "4px" }}>
                {entity.role.replaceAll("_", " ")} · {entity.member_buildings.length} members
              </div>
            </div>
            <div style={{ display: "flex", gap: "8px", color: "var(--text-muted)" }}>
              <Cpu size={14} />
              <Gauge size={14} />
              <Waves size={14} />
            </div>
          </div>
        )) : (
          <div style={{ color: "var(--text-secondary)" }}>Control entities will appear after city twin generation.</div>
        )}
      </div>

      {!events.length && feeders.every((feeder) => feeder.status === "nominal") && feeders.length > 0 && (
        <div
          style={{
            padding: "12px 14px",
            borderRadius: "16px",
            border: "1px solid rgba(16, 185, 129, 0.18)",
            background: "rgba(16, 185, 129, 0.08)",
            color: "#d1fae5",
            display: "flex",
            gap: "10px",
            alignItems: "center",
          }}
        >
          <AlertTriangle size={16} />
          Network is stable. No active feeder stress or outage events right now.
        </div>
      )}
    </div>
  );
}

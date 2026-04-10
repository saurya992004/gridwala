import { AlertCircle, ArrowRight, Brain, CloudLightning, Gauge, Zap } from "lucide-react";
import { SimulationPayload } from "@/hooks/useSimulationWebSocket";


function postureLabel(posture?: string) {
  if (posture === "resilience_priority") return "RESILIENCE";
  if (posture === "economic_optimization") return "ECONOMIC";
  return "STANDBY";
}

function derivePriority(payload: SimulationPayload | null) {
  if (!payload) {
    return {
      title: "Waiting for telemetry",
      detail: "The operator deck will populate as soon as the first simulation ticks arrive.",
      tone: "rgba(30, 41, 59, 0.6)",
      icon: <Gauge size={16} color="var(--text-secondary)" />,
    };
  }

  if (payload.forecast_scenario) {
    return {
      title: `Prepare for ${payload.forecast_scenario.replaceAll("_", " ")}`,
      detail: `The system is staging an intervention in ${payload.forecast_steps_left || 0} steps.`,
      tone: "rgba(120, 53, 15, 0.35)",
      icon: <AlertCircle size={16} color="var(--neon-amber)" />,
    };
  }

  if (payload.topology_control_signal?.controller_posture === "resilience_priority") {
    const primaryEvent = payload.topology_control_signal.primary_event;
    const constrainedCount = payload.topology_control_signal.constrained_feeders || 0;
    return {
      title: primaryEvent?.label || "Resilience posture active",
      detail:
        primaryEvent?.summary ||
        `${constrainedCount} constrained feeders detected. The controller is prioritizing feeder relief and local continuity over pure market optimization.`,
      tone: "rgba(127, 29, 29, 0.35)",
      icon: <AlertCircle size={16} color="var(--neon-red)" />,
    };
  }

  if ((payload.topology_runtime?.active_events || []).length > 0) {
    const activeEvent = payload.topology_runtime?.active_events?.[0];
    return {
      title: activeEvent?.label || "Topology event in progress",
      detail: activeEvent?.summary || "The network is operating through a live feeder or line event.",
      tone: "rgba(127, 29, 29, 0.35)",
      icon: <AlertCircle size={16} color="var(--neon-red)" />,
    };
  }

  if ((payload.topology_runtime?.constrained_feeders || 0) > 0) {
    return {
      title: "Feeder stress rising",
      detail: "One or more feeders are entering constrained operation. Prioritize headroom preservation and reduce avoidable imports.",
      tone: "rgba(120, 53, 15, 0.35)",
      icon: <Gauge size={16} color="var(--neon-amber)" />,
    };
  }

  if (
    payload.operating_context_live &&
    typeof payload.grid_renewable_share_pct === "number" &&
    payload.grid_renewable_share_pct < 35
  ) {
    return {
      title: "Low renewable share on the regional grid",
      detail: "This is a good interval to reduce imports, preserve flexibility, and prioritize local balancing.",
      tone: "rgba(120, 53, 15, 0.35)",
      icon: <CloudLightning size={16} color="var(--neon-amber)" />,
    };
  }

  if (
    payload.grid_interchange_state === "net_importing" &&
    typeof payload.grid_net_interchange_mw === "number" &&
    payload.grid_net_interchange_mw > 1000
  ) {
    return {
      title: "Region is leaning on external imports",
      detail: "Feeder coordinators should hold flexible demand and protect storage while the wider zone is importing heavily.",
      tone: "rgba(8, 47, 73, 0.35)",
      icon: <Brain size={16} color="var(--neon-cyan)" />,
    };
  }

  if (payload.grid_tariff_band === "high") {
    return {
      title: "High-cost utility window",
      detail: "Favor discharge, local balancing, and P2P exchanges while tariffs stay elevated.",
      tone: "rgba(127, 29, 29, 0.35)",
      icon: <Zap size={16} color="var(--neon-red)" />,
    };
  }

  if ((payload.carbon_intensity || 0) > 0.45) {
    return {
      title: "Dirty grid interval",
      detail: "The controller should reduce imports and lean harder on stored energy.",
      tone: "rgba(120, 53, 15, 0.35)",
      icon: <CloudLightning size={16} color="var(--neon-amber)" />,
    };
  }

  return {
    title: "Balanced operating posture",
    detail: "No acute stressors detected. The controller can optimize for economics and flexibility.",
    tone: "rgba(8, 47, 73, 0.35)",
    icon: <Brain size={16} color="var(--neon-cyan)" />,
  };
}


export default function OperatorDecisionPanel({ payload }: { payload: SimulationPayload | null }) {
  const decisions = payload?.rationales?.slice(0, 4) || [];
  const priority = derivePriority(payload);
  const topologySignal = payload?.topology_control_signal;
  const constrainedFeeders = topologySignal?.constrained_feeder_ids || [];
  const primaryEvent = topologySignal?.primary_event;

  return (
    <div
      className="glass-panel"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "16px",
        padding: "20px",
        minHeight: "360px",
        minWidth: 0,
        overflowY: "auto",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ color: "var(--text-muted)", fontSize: "0.72rem", letterSpacing: "0.14em", textTransform: "uppercase" }}>
            Operator Deck
          </div>
          <h3 style={{ fontSize: "1.1rem", marginTop: "4px" }}>Control Guidance</h3>
        </div>
        <div
          style={{
            padding: "10px",
            borderRadius: "14px",
            background: "rgba(255,255,255,0.06)",
            border: "1px solid rgba(255,255,255,0.08)",
          }}
        >
          <Brain size={18} color="var(--neon-purple)" />
        </div>
      </div>

      <div
        style={{
          padding: "16px",
          borderRadius: "16px",
          background: priority.tone,
          border: "1px solid rgba(255,255,255,0.08)",
          display: "flex",
          gap: "12px",
          alignItems: "flex-start",
        }}
      >
        <div style={{ paddingTop: "3px" }}>{priority.icon}</div>
        <div>
          <div style={{ fontWeight: 700 }}>{priority.title}</div>
          <div style={{ color: "var(--text-secondary)", fontSize: "0.9rem", marginTop: "6px", lineHeight: 1.5 }}>
            {priority.detail}
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(96px, 1fr))", gap: "12px" }}>
        <div className="metric-card" style={{ background: "rgba(2, 6, 23, 0.32)" }}>
          <div style={{ color: "var(--text-muted)", fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.1em" }}>
            Policy
          </div>
          <div style={{ marginTop: "8px", fontFamily: "var(--font-display)", fontSize: "1.08rem", lineHeight: 1.15, overflowWrap: "anywhere" }}>
            {payload?.controller_mode?.toUpperCase() || "STANDBY"}
          </div>
        </div>
        <div className="metric-card" style={{ background: "rgba(2, 6, 23, 0.32)" }}>
          <div style={{ color: "var(--text-muted)", fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.1em" }}>
            Context
          </div>
          <div style={{ marginTop: "8px", fontFamily: "var(--font-display)", fontSize: "1.08rem", lineHeight: 1.15, overflowWrap: "anywhere" }}>
            {payload?.operating_context_mode?.replaceAll("_", " ").toUpperCase() || "STATIC"}
          </div>
        </div>
        <div className="metric-card" style={{ background: "rgba(2, 6, 23, 0.32)" }}>
          <div style={{ color: "var(--text-muted)", fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.1em" }}>
            Posture
          </div>
          <div style={{ marginTop: "8px", fontFamily: "var(--font-display)", fontSize: "1.08rem", lineHeight: 1.15, overflowWrap: "anywhere" }}>
            {postureLabel(topologySignal?.controller_posture)}
          </div>
        </div>
      </div>

      {(primaryEvent || constrainedFeeders.length > 0) && (
        <div
          style={{
            padding: "14px 16px",
            borderRadius: "16px",
            background: "rgba(255,255,255,0.03)",
            border: "1px solid rgba(255,255,255,0.06)",
            display: "flex",
            flexDirection: "column",
            gap: "8px",
          }}
        >
          <div style={{ color: "var(--text-muted)", fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.14em" }}>
            Constraint Focus
          </div>
          {primaryEvent && (
            <div style={{ fontWeight: 700 }}>
              {primaryEvent.label}
            </div>
          )}
          <div style={{ color: "var(--text-secondary)", fontSize: "0.9rem", lineHeight: 1.5 }}>
            {primaryEvent?.summary ||
              "The controller is clipping market behavior to protect stressed feeders and preserve local continuity."}
          </div>
          {constrainedFeeders.length > 0 && (
            <div style={{ color: "var(--text-secondary)", fontSize: "0.84rem" }}>
              Target feeders: {constrainedFeeders.slice(0, 3).join(", ")}
              {constrainedFeeders.length > 3 ? ` +${constrainedFeeders.length - 3} more` : ""}
            </div>
          )}
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        <div style={{ color: "var(--text-muted)", fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.14em" }}>
          Agent Decisions
        </div>
        {decisions.length ? (
          decisions.map((decision, index) => (
            <div
              key={`agent-${index + 1}`}
              style={{
                display: "flex",
                gap: "10px",
                alignItems: "flex-start",
                padding: "12px 14px",
                borderRadius: "14px",
                background: "rgba(255,255,255,0.03)",
                border: "1px solid rgba(255,255,255,0.06)",
              }}
            >
              <ArrowRight size={14} color="var(--neon-cyan)" style={{ marginTop: "4px", flexShrink: 0 }} />
              <div>
                <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                  Agent {index + 1}
                </div>
                <div style={{ fontSize: "0.88rem", color: "var(--text-primary)", lineHeight: 1.5, marginTop: "4px" }}>
                  {decision}
                </div>
              </div>
            </div>
          ))
        ) : (
          <div style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
            Decisions will appear here once the controller starts acting on the grid.
          </div>
        )}
      </div>
    </div>
  );
}

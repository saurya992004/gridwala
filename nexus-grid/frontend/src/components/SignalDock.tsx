import { ReactNode } from "react";
import { Activity, CloudLightning, Coins, Cpu, Radar, Zap } from "lucide-react";
import { SimulationPayload } from "@/hooks/useSimulationWebSocket";

function controllerMeta(mode?: string) {
  if (mode === "dqn") return "adaptive multi-agent controller";
  if (mode === "rule-based") return "adaptive fallback controller";
  if (!mode) return "Awaiting controller state";
  return `${mode.replaceAll("_", " ")} controller`;
}

function metricValue(value: number | undefined, digits: number, suffix: string) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "--";
  }

  return `${value.toFixed(digits)} ${suffix}`.trim();
}

function compactPower(valueMw: number | undefined) {
  if (typeof valueMw !== "number" || Number.isNaN(valueMw)) {
    return "system load pending";
  }
  if (Math.abs(valueMw) >= 1000) {
    return `${(valueMw / 1000).toFixed(1)} GW system`;
  }
  return `${valueMw.toFixed(0)} MW system`;
}

function compactMarket(value: number | undefined, unit: string | undefined) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "wholesale pending";
  }
  return `${value.toFixed(1)} ${unit || ""}`.trim();
}

function dockTile(
  eyebrow: string,
  title: string,
  value: string,
  meta: string,
  icon: ReactNode,
) {
  return (
    <div className="signal-tile">
      <div className="signal-tile-header">
        <div>
          <div className="signal-eyebrow">{eyebrow}</div>
          <div className="signal-title">{title}</div>
        </div>
        <div className="signal-icon-shell">{icon}</div>
      </div>
      <div className="signal-value">{value}</div>
      <div className="signal-meta">{meta}</div>
    </div>
  );
}

export default function SignalDock({ payload }: { payload: SimulationPayload | null }) {
  const activeTopologyEvent = payload?.topology_runtime?.active_events?.[0];
  const controlPosture = payload?.topology_control_signal?.controller_posture
    ?.replaceAll("_", " ")
    .toUpperCase();

  return (
    <div className="signal-dock">
      {dockTile(
        "Grid",
        "Net load",
        metricValue(payload?.district_net_consumption, 2, "kW"),
        typeof payload?.grid_total_load_mw === "number"
          ? `${payload.electricity_maps_zone || "zone"} / ${compactPower(payload.grid_total_load_mw)}`
          : controllerMeta(payload?.controller_mode),
        <Activity size={16} color="var(--neon-cyan)" />,
      )}
      {dockTile(
        "Carbon",
        "Intensity",
        metricValue(payload?.carbon_intensity, 3, "kgCO2/kWh"),
        payload?.grid_renewable_share_pct !== undefined
          ? `${payload.electricity_maps_zone || "zone"} / ${payload.grid_renewable_share_pct.toFixed(0)}% renewable${payload.grid_signal_estimated ? " / estimated" : ""}`
          : payload?.operating_context_live
            ? "Live-enriched signal"
            : "Static or heuristic signal",
        <CloudLightning size={16} color="var(--neon-green)" />,
      )}
      {dockTile(
        "Utility",
        "Tariff",
        metricValue(payload?.grid_tariff_rate, 3, payload?.grid_tariff_currency || "USD"),
        typeof payload?.grid_wholesale_price === "number"
          ? `${payload?.grid_tariff_window || "utility schedule"} / wholesale ${compactMarket(payload.grid_wholesale_price, payload.grid_wholesale_price_unit)}`
          : payload?.grid_tariff_window || "utility schedule pending",
        <Coins size={16} color="var(--neon-amber)" />,
      )}
      {dockTile(
        "Twin",
        "Topology",
        `${payload?.topology_summary?.n_feeders || 0} feeders`,
        typeof payload?.topology_runtime?.constrained_feeders === "number" && payload.topology_runtime.constrained_feeders > 0
          ? `${payload.topology_runtime.constrained_feeders} constrained / ${payload.topology_runtime.overloaded_lines || 0} overloaded`
          : `${payload?.topology_summary?.n_buses || 0} buses / ${payload?.topology_summary?.n_lines || 0} lines`,
        <Radar size={16} color="var(--neon-purple)" />,
      )}
      {dockTile(
        "Control",
        "Agents",
        `${payload?.control_entities?.length || 0}`,
        controlPosture
          ? `${controlPosture} posture`
          : payload?.twin_summary?.dominant_asset_type
            ? `${payload.twin_summary.dominant_asset_type} dominated`
            : "control entities pending",
        <Cpu size={16} color="var(--neon-blue)" />,
      )}
      {dockTile(
        "Solar",
        "Forecast",
        metricValue(payload?.solar_capacity_factor, 2, "factor"),
        activeTopologyEvent
          ? activeTopologyEvent.label
          : payload?.grid_interchange_state
            ? payload.grid_interchange_state.replaceAll("_", " ")
            : payload?.weather_outlook || "weather outlook pending",
        <Zap size={16} color="var(--neon-amber)" />,
      )}
    </div>
  );
}

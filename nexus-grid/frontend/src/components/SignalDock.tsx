import { ReactNode } from "react";
import { Activity, CloudLightning, Coins, Cpu, Radar, Zap } from "lucide-react";
import { SimulationPayload } from "@/hooks/useSimulationWebSocket";

function metricValue(value: number | undefined, digits: number, suffix: string) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "--";
  }

  return `${value.toFixed(digits)} ${suffix}`.trim();
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
  return (
    <div className="signal-dock">
      {dockTile(
        "Grid",
        "Net load",
        metricValue(payload?.district_net_consumption, 2, "kW"),
        payload?.controller_mode ? `${payload.controller_mode.toUpperCase()} controller` : "Awaiting controller state",
        <Activity size={16} color="var(--neon-cyan)" />,
      )}
      {dockTile(
        "Carbon",
        "Intensity",
        metricValue(payload?.carbon_intensity, 3, "kgCO2/kWh"),
        payload?.operating_context_live ? "Live-enriched signal" : "Static or heuristic signal",
        <CloudLightning size={16} color="var(--neon-green)" />,
      )}
      {dockTile(
        "Utility",
        "Tariff",
        metricValue(payload?.grid_tariff_rate, 3, payload?.grid_tariff_currency || "USD"),
        payload?.grid_tariff_window || "utility schedule pending",
        <Coins size={16} color="var(--neon-amber)" />,
      )}
      {dockTile(
        "Twin",
        "Topology",
        `${payload?.topology_summary?.n_feeders || 0} feeders`,
        `${payload?.topology_summary?.n_buses || 0} buses · ${payload?.topology_summary?.n_lines || 0} lines`,
        <Radar size={16} color="var(--neon-purple)" />,
      )}
      {dockTile(
        "Control",
        "Agents",
        `${payload?.control_entities?.length || 0}`,
        payload?.twin_summary?.dominant_asset_type
          ? `${payload.twin_summary.dominant_asset_type} dominated`
          : "control entities pending",
        <Cpu size={16} color="var(--neon-blue)" />,
      )}
      {dockTile(
        "Solar",
        "Forecast",
        metricValue(payload?.solar_capacity_factor, 2, "factor"),
        payload?.weather_outlook || "weather outlook pending",
        <Zap size={16} color="var(--neon-amber)" />,
      )}
    </div>
  );
}

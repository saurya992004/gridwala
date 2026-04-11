import { ReactNode } from "react";
import {
  Activity,
  Battery,
  Coins,
  SunMedium,
} from "lucide-react";
import { BuildingState, SimulationPayload } from "@/hooks/useSimulationWebSocket";

function controllerSummary(mode?: string) {
  if (mode === "dqn") return "adaptive multi-agent control";
  if (mode === "rule-based") return "adaptive fallback orchestration";
  return mode || "control";
}

function average(values: number[]) {
  if (!values.length) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}


function currencyLabel(payload: SimulationPayload) {
  return payload.grid_tariff_currency || "USD";
}


function fleetStats(buildings: BuildingState[]) {
  const importing = buildings.filter((building) => building.net_electricity_consumption > 0.25).length;
  const exporting = buildings.filter((building) => building.net_electricity_consumption < -0.25).length;
  const averageSoc = average(buildings.map((building) => building.battery_soc)) * 100;
  const walletBalance = buildings.reduce((sum, building) => sum + (building.nexus_wallet || 0), 0);
  return { importing, exporting, averageSoc, walletBalance };
}


function summaryCard(
  title: string,
  eyebrow: string,
  primary: string,
  secondary: string,
  icon: ReactNode,
  tone: string,
) {
  return (
    <div
      className="glass-panel"
      style={{
        padding: "18px",
        display: "flex",
        flexDirection: "column",
        gap: "14px",
        minHeight: "150px",
        background: `linear-gradient(180deg, ${tone}, rgba(2, 6, 23, 0.52))`,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ color: "var(--text-muted)", fontSize: "0.72rem", letterSpacing: "0.14em", textTransform: "uppercase" }}>
            {eyebrow}
          </div>
          <h3 style={{ fontSize: "1rem", marginTop: "4px" }}>{title}</h3>
        </div>
        <div
          style={{
            padding: "10px",
            borderRadius: "14px",
            background: "rgba(255,255,255,0.06)",
            border: "1px solid rgba(255,255,255,0.08)",
          }}
        >
          {icon}
        </div>
      </div>

      <div style={{ fontFamily: "var(--font-display)", fontSize: "1.75rem", fontWeight: 700 }}>
        {primary}
      </div>
      <div style={{ color: "var(--text-secondary)", fontSize: "0.88rem", lineHeight: 1.5 }}>{secondary}</div>
    </div>
  );
}


export default function OperationsSummary({ payload }: { payload: SimulationPayload | null }) {
  const buildings = payload?.buildings || [];
  const stats = fleetStats(buildings);

  const gridPrimary =
    payload?.district_net_consumption !== undefined
      ? `${payload.district_net_consumption.toFixed(2)} kW`
      : "-";
  const gridSecondary =
    payload?.carbon_intensity !== undefined
      ? `Carbon ${payload.carbon_intensity.toFixed(3)} kgCO2/kWh | ${controllerSummary(payload.controller_mode)}`
      : "Awaiting grid telemetry";

  const marketPrimary =
    payload?.grid_tariff_rate !== undefined
      ? `${payload.grid_tariff_rate.toFixed(3)} ${currencyLabel(payload)}`
      : payload?.p2p_clearing_price !== undefined
        ? `${payload.p2p_clearing_price.toFixed(3)} NEXUS`
        : "-";
  const marketSecondary =
    payload?.grid_tariff_rate !== undefined
      ? `${payload.grid_tariff_window || "utility"} window | P2P ${payload.p2p_volume_kwh?.toFixed(2) || "0.00"} kWh`
      : "Tariff and market signals will appear here";

  const weatherPrimary =
    payload?.ambient_temperature_c !== undefined
      ? `${payload.ambient_temperature_c.toFixed(1)} C`
      : payload?.weather_outlook
        ? payload.weather_outlook.toUpperCase()
        : "-";
  const weatherSecondary =
    payload?.solar_capacity_factor !== undefined
      ? `Solar factor ${payload.solar_capacity_factor.toFixed(2)} | ${payload.weather_outlook || "steady"}`
      : "No enriched operating context yet";

  const fleetPrimary = buildings.length ? `${stats.averageSoc.toFixed(0)}% avg SoC` : "-";
  const fleetSecondary = buildings.length
    ? `${stats.exporting} exporting | ${stats.importing} importing | Wallet ${stats.walletBalance.toFixed(2)}`
    : "No active assets yet";

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        gap: "16px",
      }}
    >
      {summaryCard(
        "Grid State",
        "System",
        gridPrimary,
        gridSecondary,
        <Activity size={18} color="var(--neon-cyan)" />,
        "rgba(8, 47, 73, 0.45)",
      )}
      {summaryCard(
        "Market State",
        "Utility",
        marketPrimary,
        marketSecondary,
        <Coins size={18} color="var(--neon-green)" />,
        "rgba(6, 78, 59, 0.42)",
      )}
      {summaryCard(
        "Ambient State",
        "Weather",
        weatherPrimary,
        weatherSecondary,
        <SunMedium size={18} color="var(--neon-amber)" />,
        "rgba(92, 45, 8, 0.4)",
      )}
      {summaryCard(
        "Fleet State",
        "Assets",
        fleetPrimary,
        fleetSecondary,
        <Battery size={18} color="var(--neon-purple)" />,
        "rgba(49, 46, 129, 0.35)",
      )}
    </div>
  );
}

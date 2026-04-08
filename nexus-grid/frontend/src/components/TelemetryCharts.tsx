import { SimulationPayload } from "@/hooks/useSimulationWebSocket";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";


export default function TelemetryCharts({ history }: { history: SimulationPayload[] }) {
  const chartData = history.map((item) => ({
    time: `S${item.step}`,
    carbon: item.carbon_intensity,
    load: item.district_net_consumption,
    tariff: item.grid_tariff_rate,
    p2p: item.p2p_clearing_price,
    solarFactor: item.solar_capacity_factor,
  }));

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        padding: "18px 18px 12px 18px",
        display: "grid",
        gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
        gap: "18px",
      }}
    >
      <div style={{ minHeight: "250px", position: "relative" }}>
        <div style={{ color: "var(--text-muted)", fontSize: "0.72rem", letterSpacing: "0.14em", textTransform: "uppercase" }}>
          System Stress
        </div>
        <h4 style={{ fontSize: "1rem", marginTop: "4px", marginBottom: "10px" }}>
          Carbon And Load Envelope
        </h4>
        <ResponsiveContainer width="100%" height="82%">
          <AreaChart data={chartData} margin={{ top: 12, right: 10, left: -16, bottom: 0 }}>
            <defs>
              <linearGradient id="carbonGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--neon-amber)" stopOpacity={0.35} />
                <stop offset="95%" stopColor="var(--neon-amber)" stopOpacity={0.03} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis dataKey="time" hide />
            <YAxis
              yAxisId="carbon"
              stroke="var(--text-muted)"
              fontSize={10}
              axisLine={false}
              tickLine={false}
              width={34}
            />
            <YAxis
              yAxisId="load"
              orientation="right"
              stroke="var(--text-muted)"
              fontSize={10}
              axisLine={false}
              tickLine={false}
              width={34}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "rgba(3, 7, 18, 0.95)",
                border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: "12px",
              }}
              itemStyle={{ color: "var(--text-primary)" }}
            />
            <Area
              yAxisId="carbon"
              type="monotone"
              dataKey="carbon"
              stroke="var(--neon-amber)"
              strokeWidth={2}
              fill="url(#carbonGradient)"
              isAnimationActive={false}
            />
            <Line
              yAxisId="load"
              type="monotone"
              dataKey="load"
              stroke="var(--neon-cyan)"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div style={{ minHeight: "250px", position: "relative" }}>
        <div style={{ color: "var(--text-muted)", fontSize: "0.72rem", letterSpacing: "0.14em", textTransform: "uppercase" }}>
          Market State
        </div>
        <h4 style={{ fontSize: "1rem", marginTop: "4px", marginBottom: "10px" }}>
          Tariff And P2P Flow
        </h4>
        <ResponsiveContainer width="100%" height="82%">
          <LineChart data={chartData} margin={{ top: 12, right: 10, left: -16, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis dataKey="time" hide />
            <YAxis
              stroke="var(--text-muted)"
              fontSize={10}
              axisLine={false}
              tickLine={false}
              width={34}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "rgba(3, 7, 18, 0.95)",
                border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: "12px",
              }}
              itemStyle={{ color: "var(--text-primary)" }}
            />
            <Line
              type="stepAfter"
              dataKey="tariff"
              stroke="var(--neon-red)"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="p2p"
              stroke="var(--neon-green)"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="solarFactor"
              stroke="var(--neon-purple)"
              strokeWidth={1.8}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

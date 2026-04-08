import { SimulationPayload } from "@/hooks/useSimulationWebSocket";
import { 
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine
} from "recharts";

export default function TelemetryCharts({ history }: { history: SimulationPayload[] }) {
  // Format the history for recharts
  const chartData = history.map(h => ({
    time: `Step ${h.step}`,
    carbon: h.carbon_intensity,
    price: h.p2p_clearing_price,
    load: h.district_net_consumption,
    isEmergency: h.emergency ? 1 : 0
  }));

  return (
    <div style={{ width: "100%", height: "100%", position: "relative", padding: "16px", display: "flex", flexDirection: "column", gap: "16px" }}>
      
      {/* Carbon Curve */}
      <div style={{ width: "100%", height: "100%", position: "relative" }}>
        <h4 style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: "8px", position: "absolute", top: 0, left: 0, zIndex: 10 }}>
          Grid Carbon Intensity Curve
        </h4>
        <ResponsiveContainer width="100%" height="90%">
          <AreaChart data={chartData} margin={{ top: 20, right: 0, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorCarbon" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--neon-amber)" stopOpacity={0.4}/>
                <stop offset="95%" stopColor="var(--neon-amber)" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis dataKey="time" hide />
            <YAxis stroke="var(--text-muted)" fontSize={10} axisLine={false} tickLine={false} domain={['dataMin - 0.1', 'dataMax + 0.1']} />
            <Tooltip 
              contentStyle={{ backgroundColor: 'var(--bg-dark)', border: '1px solid var(--panel-border)', borderRadius: '8px' }}
              itemStyle={{ color: 'var(--text-primary)' }}
            />
            {/* If emergency is active, draw a red zone */}
            {chartData.find(d => d.isEmergency) && (
              <ReferenceLine x={chartData.find(d => d.isEmergency)?.time} stroke="var(--neon-red)" strokeDasharray="3 3" label={{ position: 'top', value: 'EMERGENCY', fill: 'var(--neon-red)', fontSize: 10 }} />
            )}
            <Area type="monotone" dataKey="carbon" stroke="var(--neon-amber)" strokeWidth={2} fillOpacity={1} fill="url(#colorCarbon)" isAnimationActive={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* P2P Token Price Curve */}
      <div style={{ flex: 1, position: "relative" }}>
        <h4 style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: "8px", position: "absolute", top: 0, left: 0, zIndex: 10 }}>
          P2P Clearing Price ($NEXUS)
        </h4>
        <ResponsiveContainer width="100%" height="90%">
          <AreaChart data={chartData} margin={{ top: 20, right: 0, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--neon-green)" stopOpacity={0.4}/>
                <stop offset="95%" stopColor="var(--neon-green)" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis dataKey="time" hide />
            <YAxis stroke="var(--text-muted)" fontSize={10} axisLine={false} tickLine={false} domain={[0.04, 0.16]} />
            <Tooltip 
              contentStyle={{ backgroundColor: 'var(--bg-dark)', border: '1px solid var(--panel-border)', borderRadius: '8px' }}
              itemStyle={{ color: 'var(--text-primary)' }}
            />
            <Area type="stepAfter" dataKey="price" stroke="var(--neon-green)" strokeWidth={2} fillOpacity={1} fill="url(#colorPrice)" isAnimationActive={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

    </div>
  );
}

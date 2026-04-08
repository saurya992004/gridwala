import { motion } from "framer-motion";
import { BuildingState } from "@/hooks/useSimulationWebSocket";
import { Home, Zap, Car, Battery, ArrowUpRight, ArrowDownRight } from "lucide-react";

export default function DistrictMap({ buildings }: { buildings: BuildingState[] }) {
  if (!buildings || buildings.length === 0) return null;

  return (
    <div style={{ 
      display: "grid", 
      gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", 
      gap: "16px", 
      padding: "24px",
      width: "100%",
      height: "100%",
      overflowY: "auto",
      overflowX: "hidden",
      alignContent: "start"
    }}>
      {buildings.map((b) => {
        
        // Visual logic based on stats
        const isEv = b.type === "ev";
        const isAway = b.is_ev_away;
        const isDischarging = b.net_electricity_consumption < -1.0; // Sending power back to grid (surplus)
        const isCharging = b.net_electricity_consumption > 1.0;     // Pulling power from grid

        let outerGlow = "transparent";
        let statusColor = "var(--text-secondary)";
        if (isDischarging) {
          outerGlow = "rgba(16, 185, 129, 0.2)"; // Green (giving to grid)
          statusColor = "var(--neon-green)";
        } else if (isCharging) {
          outerGlow = "rgba(239, 68, 68, 0.2)"; // Red (taking from grid)
          statusColor = "var(--neon-red)";
        }

        return (
          <motion.div 
            key={b.id}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: isAway ? 0.4 : 1, scale: 1, boxShadow: `0 0 20px ${outerGlow}` }}
            style={{ 
              position: "relative",
              background: "rgba(30, 41, 59, 0.6)",
              border: `1px solid ${isAway ? 'var(--panel-border)' : statusColor}`,
              borderRadius: "16px",
              padding: "16px",
              display: "flex",
              flexDirection: "column",
              gap: "12px",
              transition: "all 0.5s ease"
            }}
          >
            {/* Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                {isEv ? <Car size={18} color="var(--neon-purple)" /> : <Home size={18} color="var(--neon-blue)" />}
                <span style={{ fontSize: "0.9rem", fontWeight: 600 }}>{b.id ? b.id.substring(0,10) : "Node"}</span>
              </div>
              <span style={{ fontSize: "0.7rem", color: statusColor, fontWeight: "bold" }}>
                {isAway ? "AWAY" : "ACTIVE"}
              </span>
            </div>

            {/* Battery Level */}
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <Battery size={16} color="var(--text-secondary)" />
              <div style={{ flex: 1, height: "6px", background: "rgba(0,0,0,0.4)", borderRadius: "100px", overflow: "hidden" }}>
                <motion.div 
                  initial={false}
                  animate={{ width: `${b.battery_soc * 100}%` }}
                  style={{ 
                    height: "100%", 
                    background: b.battery_soc < 0.2 ? "var(--neon-red)" : b.battery_soc > 0.8 ? "var(--neon-green)" : "var(--neon-cyan)" 
                  }}
                />
              </div>
              <span style={{ fontSize: "0.75rem", fontFamily: "var(--font-display)" }}>{Math.round(b.battery_soc * 100)}%</span>
            </div>

            {/* Power Flow */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginTop: "auto" }}>
              <div style={{ display: "flex", flexDirection: "column" }}>
                <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>NET CONSUMPTION</span>
                <span style={{ fontSize: "1.1rem", fontWeight: 700, color: statusColor, display: "flex", alignItems: "center", gap: "4px" }}>
                  {isDischarging ? <ArrowDownRight size={14} /> : <ArrowUpRight size={14} />}
                  {Math.abs(b.net_electricity_consumption).toFixed(2)} kW
                </span>
              </div>
              {b.solar_generation > 0.5 && (
                <div style={{ display: "flex", alignItems: "center", gap: "4px", color: "var(--neon-amber)" }}>
                   <Zap size={14} fill="var(--neon-amber)" />
                   <span style={{ fontSize: "0.8rem", fontWeight: 600 }}>+{b.solar_generation.toFixed(1)}</span>
                </div>
              )}
            </div>

          </motion.div>
        );
      })}
    </div>
  );
}

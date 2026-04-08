import { motion } from "framer-motion";
import { BuildingState } from "@/hooks/useSimulationWebSocket";
import { Database, TrendingUp, TrendingDown, Coins } from "lucide-react";

export default function LedgerTable({ buildings }: { buildings: BuildingState[] }) {
  if (!buildings || buildings.length === 0) return null;

  return (
    <div style={{ padding: "24px", width: "100%", height: "100%", overflowY: "auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <h3 style={{ fontSize: "1.1rem", display: "flex", alignItems: "center", gap: "8px" }}>
          <Database size={18} color="var(--neon-green)" /> Live P2P Settlements
        </h3>
      </div>

      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
        <thead>
          <tr style={{ borderBottom: "1px solid var(--panel-border)", color: "var(--text-secondary)", textAlign: "left" }}>
            <th style={{ padding: "12px" }}>Node ID</th>
            <th style={{ padding: "12px" }}>Type</th>
            <th style={{ padding: "12px" }}>P2P Traded (kWh)</th>
            <th style={{ padding: "12px" }}>Grid Exchanged (kWh)</th>
            <th style={{ padding: "12px", textAlign: "right" }}>Wallet Balance</th>
          </tr>
        </thead>
        <tbody>
          {buildings.map((b, idx) => {
            const P2P_Volume = b.p2p_traded_kwh || 0;
            const isSeller = P2P_Volume > 0 && b.nexus_tokens_earned > 0;
            const isBuyer = P2P_Volume > 0 && b.nexus_tokens_earned < 0;

            return (
              <motion.tr 
                key={b.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.05 }}
                style={{ 
                  borderBottom: "1px solid rgba(255,255,255,0.02)",
                  background: isSeller ? "rgba(16, 185, 129, 0.05)" : isBuyer ? "rgba(239, 68, 68, 0.05)" : "transparent"
                }}
              >
                <td style={{ padding: "12px", fontFamily: "var(--font-display)", fontWeight: 600 }}>{b.id ? b.id.substring(0,8) : "Node"}</td>
                <td style={{ padding: "12px", textTransform: "uppercase", fontSize: "0.75rem", color: "var(--text-muted)" }}>{b.type || "—"}</td>
                <td style={{ padding: "12px" }}>
                  {P2P_Volume > 0 ? (
                    <span style={{ display: "inline-flex", alignItems: "center", gap: "4px", color: isSeller ? "var(--neon-green)" : "var(--neon-red)" }}>
                      {isSeller ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                      {P2P_Volume.toFixed(2)}
                    </span>
                  ) : "—"}
                </td>
                <td style={{ padding: "12px", opacity: 0.6 }}>{b.grid_exchanged_kwh ? Math.abs(b.grid_exchanged_kwh).toFixed(2) : "—"}</td>
                <td style={{ padding: "12px", textAlign: "right", fontFamily: "var(--font-display)", fontWeight: 700, color: b.nexus_wallet > 0 ? "var(--neon-green)" : "var(--neon-red)" }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: "6px" }}>
                    {b.nexus_wallet.toFixed(2)} <Coins size={14} />
                  </div>
                </td>
              </motion.tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

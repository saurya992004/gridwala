import { motion } from "framer-motion";
import { BuildingState } from "@/hooks/useSimulationWebSocket";
import { Coins, Database, TrendingDown, TrendingUp } from "lucide-react";

function formatMetric(value: number | undefined, digits: number) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "--";
  }

  return value.toFixed(digits);
}

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
          {buildings.map((building, index) => {
            const p2pVolume = building.p2p_traded_kwh || 0;
            const nexusTokensEarned = building.nexus_tokens_earned || 0;
            const walletBalance = building.nexus_wallet || 0;
            const isSeller = p2pVolume > 0 && nexusTokensEarned > 0;
            const isBuyer = p2pVolume > 0 && nexusTokensEarned < 0;

            return (
              <motion.tr
                key={`${building.id ?? "node"}-${building.type ?? "asset"}-${index}`}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                style={{
                  borderBottom: "1px solid rgba(255,255,255,0.02)",
                  background: isSeller
                    ? "rgba(16, 185, 129, 0.05)"
                    : isBuyer
                      ? "rgba(239, 68, 68, 0.05)"
                      : "transparent",
                }}
              >
                <td style={{ padding: "12px", fontFamily: "var(--font-display)", fontWeight: 600 }}>
                  {building.id ? building.id.substring(0, 8) : "Node"}
                </td>
                <td style={{ padding: "12px", textTransform: "uppercase", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                  {building.type || "--"}
                </td>
                <td style={{ padding: "12px" }}>
                  {p2pVolume > 0 ? (
                    <span style={{ display: "inline-flex", alignItems: "center", gap: "4px", color: isSeller ? "var(--neon-green)" : "var(--neon-red)" }}>
                      {isSeller ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                      {p2pVolume.toFixed(2)}
                    </span>
                  ) : "--"}
                </td>
                <td style={{ padding: "12px", opacity: 0.6 }}>
                  {typeof building.grid_exchanged_kwh === "number"
                    ? Math.abs(building.grid_exchanged_kwh).toFixed(2)
                    : "--"}
                </td>
                <td
                  style={{
                    padding: "12px",
                    textAlign: "right",
                    fontFamily: "var(--font-display)",
                    fontWeight: 700,
                    color: walletBalance > 0 ? "var(--neon-green)" : "var(--neon-red)",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: "6px" }}>
                    {formatMetric(walletBalance, 2)} <Coins size={14} />
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

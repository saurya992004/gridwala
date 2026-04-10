import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, Siren, CloudLightning } from "lucide-react";
import { TopologyEvent } from "@/hooks/useSimulationWebSocket";

interface EmergencyAlertBannerProps {
  activeEvents: TopologyEvent[];
  activeScenario?: string | null;
}

const PENDING_EVENT_COPY: Record<
  string,
  { label: string; summary: string; severity: string }
> = {
  congestion_wave: {
    label: "Congestion Wave",
    summary: "Emergency command accepted. Applying feeder-wide congestion stress on the next simulation tick.",
    severity: "high",
  },
  feeder_fault: {
    label: "Feeder Fault",
    summary: "Emergency command accepted. The target feeder will transition into outage handling on the next simulation tick.",
    severity: "critical",
  },
  line_derating: {
    label: "Line Derating",
    summary: "Emergency command accepted. A constrained branch will be derated on the next simulation tick.",
    severity: "high",
  },
  heatwave: {
    label: "Heatwave",
    summary: "Emergency command accepted. The environment is preparing a high-load weather stress condition.",
    severity: "high",
  },
  carbon_spike: {
    label: "Carbon Spike",
    summary: "Emergency command accepted. Carbon intensity stress will apply on the next simulation tick.",
    severity: "high",
  },
  solar_offline: {
    label: "Solar Offline",
    summary: "Emergency command accepted. Solar support will be suppressed on the next simulation tick.",
    severity: "warning",
  },
};

export default function EmergencyAlertBanner({
  activeEvents,
  activeScenario,
}: EmergencyAlertBannerProps) {
  const currentEvent =
    activeEvents && activeEvents.length > 0
      ? activeEvents[0]
      : activeScenario
        ? {
            id: `pending::${activeScenario}`,
            kind: activeScenario,
            severity: PENDING_EVENT_COPY[activeScenario]?.severity ?? "warning",
            label: PENDING_EVENT_COPY[activeScenario]?.label ?? "Emergency Pending",
            target: "pending",
            summary:
              PENDING_EVENT_COPY[activeScenario]?.summary ??
              "Emergency command accepted. Waiting for the next simulation step.",
          }
        : null;

  if (!currentEvent) return null;

  const getEventStyles = (severity: string) => {
    switch (severity) {
      case "critical":
        return {
          bg: "rgba(220, 38, 38, 0.15)",
          border: "1px solid rgba(220, 38, 38, 0.3)",
          icon: <Siren size={24} color="var(--neon-red)" />,
          color: "var(--neon-red)",
        };
      case "high":
        return {
          bg: "rgba(245, 158, 11, 0.15)",
          border: "1px solid rgba(245, 158, 11, 0.3)",
          icon: <CloudLightning size={24} color="var(--neon-amber)" />,
          color: "var(--neon-amber)",
        };
      default:
        return {
          bg: "rgba(234, 179, 8, 0.15)",
          border: "1px solid rgba(234, 179, 8, 0.3)",
          icon: <AlertTriangle size={24} color="#eab308" />,
          color: "#eab308",
        };
    }
  };

  const styles = getEventStyles(currentEvent.severity);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -20, scale: 0.95 }}
        transition={{ type: "spring", stiffness: 300, damping: 20 }}
        style={{
          width: "100%",
          padding: "16px 20px",
          background: styles.bg.replace("0.15", "0.88"),
          border: styles.border,
          borderRadius: "12px",
          display: "flex",
          alignItems: "center",
          gap: "16px",
          marginBottom: "16px",
          backdropFilter: "blur(18px)",
          boxShadow: "0 18px 44px rgba(2, 6, 23, 0.42)",
          position: "relative",
          overflow: "hidden",
        }}
      >
        <motion.div
          animate={{ scale: [1, 1.2, 1] }}
          transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
        >
          {styles.icon}
        </motion.div>
        
        <div style={{ flex: 1 }}>
          <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 600, color: styles.color }}>
            {currentEvent.label.toUpperCase()}
          </h3>
          <p style={{ margin: "4px 0 0", fontSize: "13px", color: "var(--text-secondary)" }}>
            {currentEvent.summary}
          </p>
        </div>

        {currentEvent.steps_left !== undefined && currentEvent.steps_left > 0 && (
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: "12px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "1px" }}>
              Time to Clear
            </div>
            <div style={{ fontSize: "20px", fontWeight: 700, color: styles.color, fontFamily: "monospace" }}>
              T-{currentEvent.steps_left} steps
            </div>
          </div>
        )}

        <motion.div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            bottom: 0,
            width: "4px",
            background: styles.color,
          }}
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
        />
      </motion.div>
    </AnimatePresence>
  );
}

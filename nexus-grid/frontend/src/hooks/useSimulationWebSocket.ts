import { useState, useEffect, useCallback, useRef } from 'react';

export interface BuildingState {
  id: string;
  type: string;
  is_ev_away: boolean;
  net_electricity_consumption: number;
  solar_generation: number;
  battery_soc: number;
  reward: number;
  p2p_traded_kwh?: number;
  grid_exchanged_kwh?: number;
  nexus_tokens_earned?: number;
  nexus_wallet?: number;
}

export interface SimulationPayload {
  type: 'step' | 'connected' | 'done';
  step?: number;
  hour?: number;
  day?: number;
  done?: boolean;
  buildings?: BuildingState[];
  carbon_intensity?: number;
  district_net_consumption?: number;
  p2p_volume_kwh?: number;
  p2p_clearing_price?: number;
  forecast_scenario?: string | null;
  forecast_steps_left?: number;
  rationales?: string[];
  emergency?: string | null;
  preset?: string;
  district_name?: string;
  max_steps?: number;
  controller_mode?: string;
  model_id?: string;
  engine_mode?: string;
  operating_context_mode?: string;
  operating_context_live?: boolean;
  grid_tariff_rate?: number;
  grid_export_rate?: number;
  grid_tariff_currency?: string;
  grid_tariff_window?: string;
  grid_tariff_band?: string;
  ambient_temperature_c?: number;
  solar_capacity_factor?: number;
  weather_outlook?: string;
}

export function useSimulationWebSocket(presetId: string = 'residential_district') {
  const [data, setData] = useState<SimulationPayload | null>(null);
  const [history, setHistory] = useState<SimulationPayload[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    const connect = () => {
      if (wsRef.current?.readyState === WebSocket.OPEN) return;

      const ws = new WebSocket(`ws://127.0.0.1:8000/ws/simulate?preset=${presetId}`);

      ws.onopen = () => {
        setIsConnected(true);
        console.log('Connected to Nexus Simulation Engine');
      };

      ws.onmessage = (event) => {
        try {
          const payload: SimulationPayload = JSON.parse(event.data);
          setData(payload);

          if (payload.type === 'step') {
            setHistory(prev => {
              const next = [...prev, payload];
              if (next.length > 50) return next.slice(next.length - 50); // Keep last 50 ticks for charts
              return next;
            });
          }

          if (payload.type === 'done') {
            setIsPaused(true);
          }
        } catch (e) {
          console.error('Failed to parse websocket message', e);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        console.log('Disconnected from Simulation Engine');
        reconnectTimer = setTimeout(() => {
          connect();
        }, 2000);
      };

      wsRef.current = ws;
    };

    connect();

    return () => {
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
      }
      if (wsRef.current) {
        wsRef.current.onclose = null; // prevent reconnect loop on unmount
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [presetId]);

  // Actions
  const togglePause = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const newPausedState = !isPaused;
      wsRef.current.send(JSON.stringify({ action: newPausedState ? 'pause' : 'resume' }));
      setIsPaused(newPausedState);
    }
  }, [isPaused]);

  const setSpeed = useCallback((val: number) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'set_speed', value: val }));
    }
  }, []);

  const triggerEmergency = useCallback((scenario: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'emergency', scenario }));
    }
  }, []);

  const triggerForecast = useCallback((scenario: string, steps: number = 4) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'forecast_emergency', scenario, steps }));
    }
  }, []);

  const clearEmergency = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'clear_emergency' }));
    }
  }, []);

  return {
    data,
    history,
    isConnected,
    isPaused,
    togglePause,
    setSpeed,
    triggerEmergency,
    triggerForecast,
    clearEmergency,
  };
}

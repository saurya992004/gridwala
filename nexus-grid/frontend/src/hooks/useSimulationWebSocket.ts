import { useState, useEffect, useCallback, useRef } from "react";

export interface BuildingState {
  id: string;
  bus_id?: string;
  feeder_id?: string;
  feeder_label?: string;
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
  feeder_status?: string;
  feeder_loading_pct?: number;
  feeder_headroom_kw?: number | null;
  line_id?: string;
  line_status?: string;
  line_loading_pct?: number;
  topology_stress_index?: number;
  topology_stressed?: boolean;
  topology_event_targeted?: boolean;
  topology_reward_adjustment?: number;
}

export interface GeoContext {
  display_name?: string;
  latitude?: number;
  longitude?: number;
  country?: string;
  country_code?: string;
  state?: string;
  city?: string;
  locality?: string;
  category?: string;
  type?: string;
}

export interface TopologySummary {
  topology_type?: string;
  slack_bus?: string;
  n_buses?: number;
  n_lines?: number;
  n_feeders?: number;
  n_assets_attached?: number;
  max_line_capacity_kw?: number;
  radial?: boolean;
}

export interface TopologyEvent {
  id: string;
  kind: string;
  severity: string;
  label: string;
  target: string;
  summary: string;
  steps_left?: number;
}

export interface TopologyLineState {
  line_id: string;
  feeder_id: string;
  from_bus: string;
  to_bus: string;
  capacity_kw?: number;
  available_capacity_kw?: number;
  flow_kw?: number;
  loading_pct?: number;
  status: string;
  is_outaged?: boolean;
  is_feeder_head?: boolean;
}

export interface FeederState {
  feeder_id: string;
  label: string;
  n_assets?: number;
  net_load_kw?: number;
  loading_kw?: number;
  loading_pct?: number;
  headroom_kw?: number | null;
  capacity_kw?: number | null;
  status: string;
  line_count?: number;
  constrained_lines?: number;
  is_outaged?: boolean;
}

export interface TopologyRuntime {
  system_stress_index?: number;
  constrained_feeders?: number;
  overloaded_lines?: number;
  feeder_states?: FeederState[];
  line_states?: TopologyLineState[];
  active_events?: TopologyEvent[];
}

export interface TopologyControlSignal {
  system_stress_index?: number;
  constrained_feeders?: number;
  overloaded_lines?: number;
  primary_event?: TopologyEvent;
  constrained_feeder_ids?: string[];
  controller_posture?: string;
}

export interface ControlEntity {
  id: string;
  label: string;
  role: string;
  agent_class: string;
  feeder_id?: string;
  member_buildings: string[];
  member_types: string[];
  solar_capacity_kw?: number;
  storage_capacity_kwh?: number;
  dispatch_capacity_kw?: number;
  objective?: string;
}

export interface TwinSummary {
  phase?: string;
  location_label?: string;
  country_code?: string;
  district_type?: string;
  n_buildings?: number;
  n_control_entities?: number;
  n_feeders?: number;
  dominant_asset_type?: string;
  solar_capacity_kw?: number;
  storage_capacity_kwh?: number;
  dispatch_capacity_kw?: number;
  electricity_maps_zone?: string;
  electricity_maps_provider_mode?: string;
  renewable_share_pct?: number;
  rl_agent_scope?: string[];
}

export interface AtlasContext {
  phase?: string;
  mode?: string;
  generator?: string;
  selection_kind?: string;
  district_type?: string;
  agentization_strategy?: string;
  control_surface?: string;
  feature_flags?: string[];
}

export interface TwinProvenanceLayer {
  layer: string;
  source: string;
  confidence?: number;
}

export interface TwinProvenance {
  geography?: {
    source?: string;
    label?: string;
    coordinates?: {
      latitude?: number;
      longitude?: number;
    };
  };
  live_signal_spine?: Record<string, string>;
  inferred_layers?: TwinProvenanceLayer[];
  editable_assumptions?: string[];
}

export interface GeoFeaturedLocation {
  query: string;
  location: GeoContext;
  recommended_district_type: string;
}

export interface CityTwinRequest {
  query: string;
  provider?: string;
  districtType?: string;
  buildingCount?: number;
  weatherProvider?: string;
  carbonProvider?: string;
  tariffProvider?: string;
}

export interface SimulationPayload {
  type: "step" | "connected" | "done";
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
  electricity_maps_zone?: string;
  electricity_maps_provider_mode?: string;
  grid_signal_estimated?: boolean;
  grid_renewable_share_pct?: number;
  grid_total_load_mw?: number;
  grid_import_mw?: number;
  grid_export_mw?: number;
  grid_net_interchange_mw?: number;
  grid_interchange_state?: string;
  grid_wholesale_price?: number;
  grid_wholesale_price_unit?: string;
  ambient_temperature_c?: number;
  solar_capacity_factor?: number;
  weather_outlook?: string;
  topology_summary?: TopologySummary;
  topology_runtime?: TopologyRuntime;
  topology_control_signal?: TopologyControlSignal;
  geo_context?: GeoContext;
  twin_summary?: TwinSummary;
  atlas_context?: AtlasContext;
  control_entities?: ControlEntity[];
  twin_provenance?: TwinProvenance;
  data_sources?: Record<string, string>;
  enrichment_warnings?: string[];
}

type RawSchema = Record<string, unknown>;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function seedBuildingsFromSchema(schema: RawSchema): BuildingState[] {
  const rawBuildings = Array.isArray(schema.buildings) ? schema.buildings : [];
  return rawBuildings.map((building, index) => {
    const raw = isRecord(building) ? building : {};
    return {
      id: typeof raw.name === "string" ? raw.name : `Asset ${index + 1}`,
      type: typeof raw.type === "string" ? raw.type : "residential",
      is_ev_away: false,
      net_electricity_consumption: 0,
      solar_generation: 0,
      battery_soc: 0.5,
      reward: 0,
      p2p_traded_kwh: 0,
      grid_exchanged_kwh: 0,
      nexus_tokens_earned: 0,
      nexus_wallet: 0,
    };
  });
}

function sendSchemaToRunner(ws: WebSocket, schema: RawSchema) {
  ws.send(JSON.stringify({ action: "load_schema", schema }));
}

export function useSimulationWebSocket(presetId: string = "residential_district") {
  const [data, setData] = useState<SimulationPayload | null>(null);
  const [history, setHistory] = useState<SimulationPayload[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isTwinLoading, setIsTwinLoading] = useState(false);
  const [twinError, setTwinError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const activeSchemaRef = useRef<RawSchema | null>(null);

  const applySchema = useCallback((schema: RawSchema) => {
    activeSchemaRef.current = schema;
    setHistory([]);
    setIsPaused(false);
    setData((previous) => ({
      ...(previous ?? { type: "connected" as const }),
      type: "connected",
      preset: "atlas_city_twin",
      district_name:
        typeof schema.district_name === "string" ? schema.district_name : previous?.district_name,
      buildings: seedBuildingsFromSchema(schema),
      topology_summary: isRecord(schema.topology_summary)
        ? (schema.topology_summary as TopologySummary)
        : previous?.topology_summary,
      geo_context: isRecord(schema.geo_context) ? (schema.geo_context as GeoContext) : previous?.geo_context,
      twin_summary: isRecord(schema.twin_summary)
        ? (schema.twin_summary as TwinSummary)
        : previous?.twin_summary,
      atlas_context: isRecord(schema.atlas_context)
        ? (schema.atlas_context as AtlasContext)
        : previous?.atlas_context,
      control_entities: Array.isArray(schema.control_entities)
        ? (schema.control_entities as ControlEntity[])
        : previous?.control_entities,
      twin_provenance: isRecord(schema.twin_provenance)
        ? (schema.twin_provenance as TwinProvenance)
        : previous?.twin_provenance,
      data_sources: isRecord(schema.data_sources)
        ? (schema.data_sources as Record<string, string>)
        : previous?.data_sources,
      enrichment_warnings: Array.isArray(schema.enrichment_warnings)
        ? (schema.enrichment_warnings as string[])
        : previous?.enrichment_warnings,
    }));

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      sendSchemaToRunner(wsRef.current, schema);
    }
  }, []);

  const clearTwinError = useCallback(() => {
    setTwinError(null);
  }, []);

  const loadCityTwin = useCallback(
    async (request: CityTwinRequest) => {
      setIsTwinLoading(true);
      setTwinError(null);

      try {
        const response = await fetch("http://127.0.0.1:8000/api/geo/schema", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            query: request.query,
            provider: request.provider ?? "auto",
            district_type: request.districtType ?? "auto",
            building_count: request.buildingCount,
            include_enrichment: true,
            weather_provider: request.weatherProvider ?? "auto",
            carbon_provider: request.carbonProvider ?? "auto",
            tariff_provider: request.tariffProvider ?? "auto",
          }),
        });

        const result = (await response.json()) as { detail?: string; schema?: RawSchema };
        if (!response.ok || !result.schema) {
          throw new Error(result.detail ?? `Failed to build city twin (${response.status})`);
        }

        applySchema(result.schema);
        return result;
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "Failed to build and load the city twin.";
        setTwinError(message);
        throw error;
      } finally {
        setIsTwinLoading(false);
      }
    },
    [applySchema],
  );

  useEffect(() => {
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    const connect = () => {
      if (wsRef.current?.readyState === WebSocket.OPEN) return;

      const ws = new WebSocket(`ws://127.0.0.1:8000/ws/simulate?preset=${presetId}`);

      ws.onopen = () => {
        setIsConnected(true);
        if (activeSchemaRef.current) {
          sendSchemaToRunner(ws, activeSchemaRef.current);
        }
      };

      ws.onmessage = (event) => {
        try {
          const payload: SimulationPayload = JSON.parse(event.data);
          if (payload.type === "connected" && activeSchemaRef.current) {
            const schema = activeSchemaRef.current;
            setData({
              ...payload,
              district_name:
                typeof schema.district_name === "string" ? schema.district_name : payload.district_name,
              buildings: seedBuildingsFromSchema(schema),
              topology_summary: isRecord(schema.topology_summary)
                ? (schema.topology_summary as TopologySummary)
                : payload.topology_summary,
              geo_context: isRecord(schema.geo_context)
                ? (schema.geo_context as GeoContext)
                : payload.geo_context,
              twin_summary: isRecord(schema.twin_summary)
                ? (schema.twin_summary as TwinSummary)
                : payload.twin_summary,
              atlas_context: isRecord(schema.atlas_context)
                ? (schema.atlas_context as AtlasContext)
                : payload.atlas_context,
              control_entities: Array.isArray(schema.control_entities)
                ? (schema.control_entities as ControlEntity[])
                : payload.control_entities,
              twin_provenance: isRecord(schema.twin_provenance)
                ? (schema.twin_provenance as TwinProvenance)
                : payload.twin_provenance,
              data_sources: isRecord(schema.data_sources)
                ? (schema.data_sources as Record<string, string>)
                : payload.data_sources,
              enrichment_warnings: Array.isArray(schema.enrichment_warnings)
                ? (schema.enrichment_warnings as string[])
                : payload.enrichment_warnings,
            });
          } else {
            setData(payload);
          }

          if (payload.type === "step") {
            setHistory((previous) => {
              const next = [...previous, payload];
              if (next.length > 50) {
                return next.slice(next.length - 50);
              }
              return next;
            });
          }

          if (payload.type === "done") {
            setIsPaused(true);
          }
        } catch (error) {
          console.error("Failed to parse websocket message", error);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
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
        wsRef.current.onclose = null;
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [presetId]);

  const togglePause = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const newPausedState = !isPaused;
      wsRef.current.send(JSON.stringify({ action: newPausedState ? "pause" : "resume" }));
      setIsPaused(newPausedState);
    }
  }, [isPaused]);

  const setSpeed = useCallback((value: number) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "set_speed", value }));
    }
  }, []);

  const triggerEmergency = useCallback((scenario: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "emergency", scenario }));
      setData((previous) =>
        previous
          ? {
              ...previous,
              emergency: scenario,
            }
          : previous,
      );
    }
  }, []);

  const triggerForecast = useCallback((scenario: string, steps: number = 4) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "forecast_emergency", scenario, steps }));
    }
  }, []);

  const clearEmergency = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "clear_emergency" }));
      setData((previous) =>
        previous
          ? {
              ...previous,
              emergency: null,
              topology_runtime: previous.topology_runtime
                ? {
                    ...previous.topology_runtime,
                    active_events: [],
                  }
                : previous.topology_runtime,
            }
          : previous,
      );
    }
  }, []);

  return {
    data,
    history,
    isConnected,
    isPaused,
    isTwinLoading,
    twinError,
    togglePause,
    setSpeed,
    triggerEmergency,
    triggerForecast,
    clearEmergency,
    clearTwinError,
    loadCityTwin,
    applySchema,
  };
}

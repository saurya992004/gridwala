"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import maplibregl, {
  GeoJSONSource,
  LngLatLike,
  Map as MapLibreMap,
  StyleSpecification,
} from "maplibre-gl";
import type { Feature, FeatureCollection, LineString, Point } from "geojson";
import { Protocol } from "pmtiles";
import {
  BuildingState,
  ControlEntity,
  GeoContext,
  TopologyRuntime,
  TwinSummary,
} from "@/hooks/useSimulationWebSocket";

const PMTILES_URL = process.env.NEXT_PUBLIC_NEXUS_PMTILES_URL;
const MAP_STYLE_URL = process.env.NEXT_PUBLIC_NEXUS_MAP_STYLE_URL;

let pmtilesRegistered = false;

type TwinFeatureSet = {
  center: FeatureCollection<Point>;
  assets: FeatureCollection<Point>;
  feederHeads: FeatureCollection<Point>;
  lines: FeatureCollection<LineString>;
};

function hashValue(input: string) {
  let hash = 0;
  for (let index = 0; index < input.length; index += 1) {
    hash = (hash << 5) - hash + input.charCodeAt(index);
    hash |= 0;
  }
  return Math.abs(hash);
}

function safeId(value: unknown, fallback: string) {
  return typeof value === "string" && value.trim().length > 0 ? value : fallback;
}

function statusColor(status: string) {
  if (status === "outage") return "#ef4444";
  if (status === "overload") return "#fb7185";
  if (status === "critical") return "#f59e0b";
  if (status === "warning") return "#fde047";
  return "#06b6d4";
}

function assetColor(assetType: string) {
  if (assetType === "ev") return "#8b5cf6";
  if (assetType === "industrial") return "#f59e0b";
  if (assetType === "hospital" || assetType === "campus") return "#06b6d4";
  if (assetType === "commercial") return "#10b981";
  return "#3b82f6";
}

function normalizeCenter(geoContext?: GeoContext): [number, number] {
  const longitude = typeof geoContext?.longitude === "number" ? geoContext.longitude : -0.1276;
  const latitude = typeof geoContext?.latitude === "number" ? geoContext.latitude : 51.5072;
  return [longitude, latitude];
}

function fallbackMapStyle(): StyleSpecification {
  return {
    version: 8,
    glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
    sources: {
      dark_raster: {
        type: "raster",
        tiles: [
          "https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
        ],
        tileSize: 256,
        attribution: "&copy; OpenStreetMap contributors &copy; CARTO",
      },
    },
    layers: [
      {
        id: "background",
        type: "background",
        paint: {
          "background-color": "#020617",
        },
      },
      {
        id: "dark_raster",
        type: "raster",
        source: "dark_raster",
        paint: {
          "raster-opacity": 0.88,
          "raster-saturation": -0.35,
          "raster-contrast": 0.1,
        },
      },
    ],
  };
}

function coordinateForFeeder(
  feederId: string,
  center: [number, number],
  index: number,
  total: number,
): [number, number] {
  const [longitude, latitude] = center;
  const jitter = (hashValue(feederId) % 1000) / 1000;
  const angleBase = (Math.PI * 2 * index) / Math.max(total, 1);
  const angle = angleBase + (jitter * 0.32);
  const radius = 0.0038 + (jitter * 0.0012);
  const lngDelta = (radius * Math.cos(angle)) / Math.max(Math.cos((latitude * Math.PI) / 180), 0.25);
  const latDelta = radius * Math.sin(angle);
  return [longitude + lngDelta, latitude + latDelta];
}

function buildTwinFeatures(
  center: [number, number],
  buildings: BuildingState[],
  controlEntities: ControlEntity[],
  topologyRuntime?: TopologyRuntime,
): TwinFeatureSet {
  const [longitude, latitude] = center;
  const assetCoordinates = new Map<string, [number, number]>();
  const busCoordinates = new Map<string, [number, number]>();
  const assets: Feature<Point>[] = [];

  buildings.forEach((building, index) => {
    const angleOffset = (Math.PI * 2 * index) / Math.max(buildings.length, 1);
    const buildingId = safeId(building.id, `asset-${index + 1}`);
    const buildingType = typeof building.type === "string" ? building.type : "residential";
    const jitter = (hashValue(buildingId) % 1000) / 1000;
    const radius = 0.008 + (index % 3) * 0.0035 + (jitter * 0.0018);
    const angle = angleOffset + (jitter * 0.35);
    const lngDelta = (radius * Math.cos(angle)) / Math.max(Math.cos((latitude * Math.PI) / 180), 0.25);
    const latDelta = radius * Math.sin(angle);
    const assetCoordinate: [number, number] = [longitude + lngDelta, latitude + latDelta];
    assetCoordinates.set(buildingId, assetCoordinate);
    if (building.bus_id) {
      busCoordinates.set(building.bus_id, assetCoordinate);
    }

    assets.push({
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: assetCoordinate,
      },
      properties: {
        id: buildingId,
        label: buildingId,
        assetType: buildingType,
        batterySoc: typeof building.battery_soc === "number" ? building.battery_soc : 0,
        netConsumption:
          typeof building.net_electricity_consumption === "number"
            ? building.net_electricity_consumption
            : 0,
        color: assetColor(buildingType),
      },
    });
  });

  const feederIds = Array.from(
    new Set(
      (topologyRuntime?.feeder_states || [])
        .map((feeder) => feeder.feeder_id)
        .filter((value): value is string => typeof value === "string" && value.length > 0),
    ),
  );
  if (!feederIds.length) {
    controlEntities.forEach((entity) => {
      if (entity.feeder_id && !feederIds.includes(entity.feeder_id)) {
        feederIds.push(entity.feeder_id);
      }
    });
  }

  const feederHeadCoordinates = new Map<string, [number, number]>();
  feederIds.forEach((feederId, index) => {
    feederHeadCoordinates.set(feederId, coordinateForFeeder(feederId, center, index, feederIds.length));
  });

  const feederHeads: Feature<Point>[] = feederIds.map((feederId) => {
    const feederState = (topologyRuntime?.feeder_states || []).find((item) => item.feeder_id === feederId);
    return {
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: feederHeadCoordinates.get(feederId) || center,
      },
      properties: {
        id: feederId,
        label: feederState?.label || feederId.replaceAll("_", " "),
        status: feederState?.status || "nominal",
      },
    };
  });

  const lines: Feature<LineString>[] = [];
  (topologyRuntime?.line_states || []).forEach((lineState, index) => {
    const feederCoordinate = feederHeadCoordinates.get(lineState.feeder_id) || center;
    const fromCoordinate =
      lineState.is_feeder_head
        ? center
        : busCoordinates.get(lineState.from_bus) || feederCoordinate;
    const toCoordinate =
      lineState.to_bus === "substation_bus"
        ? center
        : busCoordinates.get(lineState.to_bus) || feederCoordinate;

    if (
      Math.abs(fromCoordinate[0] - toCoordinate[0]) < 0.000001 &&
      Math.abs(fromCoordinate[1] - toCoordinate[1]) < 0.000001
    ) {
      return;
    }

    lines.push({
      type: "Feature",
      geometry: {
        type: "LineString",
        coordinates: [fromCoordinate, toCoordinate],
      },
      properties: {
        id: lineState.line_id || `line-${index + 1}`,
        label: lineState.line_id || `line-${index + 1}`,
        status: lineState.status || "nominal",
        loadingPct: typeof lineState.loading_pct === "number" ? lineState.loading_pct : 0,
        lineWidth: Math.max(2.2, 2.2 + ((lineState.loading_pct || 0) * 3.8)),
        color: statusColor(lineState.status || "nominal"),
        isOutaged: Boolean(lineState.is_outaged),
      },
    });
  });

  return {
    center: {
      type: "FeatureCollection",
      features: [
        {
          type: "Feature",
          geometry: {
            type: "Point",
            coordinates: center,
          },
          properties: {
            label: "Grid center",
          },
        },
      ],
    },
    assets: {
      type: "FeatureCollection",
      features: assets,
    },
    feederHeads: {
      type: "FeatureCollection",
      features: feederHeads,
    },
    lines: {
      type: "FeatureCollection",
      features: lines,
    },
  };
}

function setGeoJsonData(
  map: MapLibreMap,
  sourceId: string,
  data: FeatureCollection<Point> | FeatureCollection<LineString>,
) {
  const source = map.getSource(sourceId) as GeoJSONSource | undefined;
  if (source) {
    source.setData(data);
  }
}

interface TwinMapCanvasProps {
  geoContext?: GeoContext;
  buildings: BuildingState[];
  controlEntities: ControlEntity[];
  topologyRuntime?: TopologyRuntime;
  twinSummary?: TwinSummary;
}

export default function TwinMapCanvas({
  geoContext,
  buildings,
  controlEntities,
  topologyRuntime,
  twinSummary,
}: TwinMapCanvasProps) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const previousCenterRef = useRef<[number, number] | null>(null);

  const center = useMemo(() => normalizeCenter(geoContext), [geoContext]);
  const twinFeatures = useMemo(
    () => buildTwinFeatures(center, buildings, controlEntities, topologyRuntime),
    [center, buildings, controlEntities, topologyRuntime],
  );
  const [initialCenter] = useState(center);
  const [initialFeatures] = useState(twinFeatures);
  const activeEvents = topologyRuntime?.active_events || [];
  const feederStressCount = topologyRuntime?.constrained_feeders || 0;

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) {
      return;
    }

    if (!pmtilesRegistered) {
      const protocol = new Protocol();
      maplibregl.addProtocol("pmtiles", protocol.tile);
      pmtilesRegistered = true;
    }

    const style: StyleSpecification | string = MAP_STYLE_URL || fallbackMapStyle();
    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style,
      center: initialCenter as LngLatLike,
      zoom: 10.8,
      pitch: 48,
      bearing: 12,
      attributionControl: false,
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

    map.on("load", () => {
      map.addSource("twin-center", { type: "geojson", data: initialFeatures.center });
      map.addSource("twin-assets", { type: "geojson", data: initialFeatures.assets });
      map.addSource("twin-feeder-heads", { type: "geojson", data: initialFeatures.feederHeads });
      map.addSource("twin-lines", { type: "geojson", data: initialFeatures.lines });

      map.addLayer({
        id: "twin-lines-main",
        type: "line",
        source: "twin-lines",
        layout: {
          "line-cap": "round",
          "line-join": "round",
        },
        paint: {
          "line-color": ["get", "color"],
          "line-width": ["get", "lineWidth"],
          "line-opacity": 0.92,
        },
      });

      map.addLayer({
        id: "twin-lines-outage",
        type: "line",
        source: "twin-lines",
        filter: ["==", ["get", "isOutaged"], true],
        paint: {
          "line-color": "#ef4444",
          "line-width": 5.4,
          "line-opacity": 0.42,
        },
      });

      map.addLayer({
        id: "twin-feeder-heads",
        type: "circle",
        source: "twin-feeder-heads",
        paint: {
          "circle-radius": 8,
          "circle-color": [
            "match",
            ["get", "status"],
            "outage", "#ef4444",
            "overload", "#fb7185",
            "critical", "#f59e0b",
            "warning", "#fde047",
            "#06b6d4",
          ],
          "circle-stroke-width": 1.3,
          "circle-stroke-color": "rgba(255,255,255,0.9)",
        },
      });

      map.addLayer({
        id: "twin-center-glow",
        type: "circle",
        source: "twin-center",
        paint: {
          "circle-radius": 26,
          "circle-color": "rgba(59, 130, 246, 0.16)",
          "circle-stroke-width": 1,
          "circle-stroke-color": "rgba(59, 130, 246, 0.34)",
        },
      });

      map.addLayer({
        id: "twin-assets-points",
        type: "circle",
        source: "twin-assets",
        paint: {
          "circle-radius": [
            "interpolate",
            ["linear"],
            ["get", "batterySoc"],
            0,
            5,
            1,
            10,
          ],
          "circle-color": ["get", "color"],
          "circle-stroke-width": 1.2,
          "circle-stroke-color": "rgba(255,255,255,0.75)",
          "circle-opacity": 0.95,
        },
      });
    });

    mapRef.current = map;
    previousCenterRef.current = initialCenter;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [initialCenter, initialFeatures]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) {
      return;
    }

    setGeoJsonData(map, "twin-center", twinFeatures.center);
    setGeoJsonData(map, "twin-assets", twinFeatures.assets);
    setGeoJsonData(map, "twin-feeder-heads", twinFeatures.feederHeads);
    setGeoJsonData(map, "twin-lines", twinFeatures.lines);

    const previousCenter = previousCenterRef.current;
    if (
      !previousCenter ||
      Math.abs(previousCenter[0] - center[0]) > 0.0001 ||
      Math.abs(previousCenter[1] - center[1]) > 0.0001
    ) {
      map.flyTo({
        center: center as LngLatLike,
        zoom: 10.8,
        speed: 0.7,
        curve: 1.1,
        essential: true,
      });
      previousCenterRef.current = center;
    }
  }, [center, twinFeatures]);

  return (
    <div className="twin-map-shell">
      <div ref={mapContainerRef} className="twin-map-canvas" />

      <div className="map-floating-card map-floating-top-left">
        <div className="map-eyebrow">World Twin</div>
        <div className="map-title">{geoContext?.city || geoContext?.locality || "City Twin"}</div>
        <div className="map-copy">
          {twinSummary?.n_control_entities || 0} control entities across {twinSummary?.n_feeders || 0} feeders
        </div>
      </div>

      <div className="map-floating-card map-floating-top-right">
        <div className="map-eyebrow">Grid Stress</div>
        <div className="map-copy">
          {feederStressCount} constrained feeders · {topologyRuntime?.overloaded_lines || 0} overloaded lines
        </div>
        <div className="map-stack-meta">
          {activeEvents.length
            ? activeEvents[0].label
            : `${MAP_STYLE_URL ? "Custom MapLibre Style" : "Open fallback style"} · ${PMTILES_URL ? "PMTiles wired" : "PMTiles ready"}`}
        </div>
      </div>

      <div className="map-floating-card map-floating-bottom-left">
        <div className="map-eyebrow">Legend</div>
        <div className="map-legend-row">
          <span className="map-dot" style={{ background: "#06b6d4" }} />
          Nominal feeder
        </div>
        <div className="map-legend-row">
          <span className="map-dot" style={{ background: "#fde047" }} />
          Warning / constrained
        </div>
        <div className="map-legend-row">
          <span className="map-dot" style={{ background: "#f59e0b" }} />
          Critical loading
        </div>
        <div className="map-legend-row">
          <span className="map-dot" style={{ background: "#ef4444" }} />
          Outage / faulted line
        </div>
      </div>
    </div>
  );
}

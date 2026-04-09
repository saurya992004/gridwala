"use client";

import { useEffect, useMemo, useRef } from "react";
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
  TwinSummary,
} from "@/hooks/useSimulationWebSocket";

const PMTILES_URL = process.env.NEXT_PUBLIC_NEXUS_PMTILES_URL;
const MAP_STYLE_URL = process.env.NEXT_PUBLIC_NEXUS_MAP_STYLE_URL;

let pmtilesRegistered = false;

type TwinFeatureSet = {
  center: FeatureCollection<Point>;
  assets: FeatureCollection<Point>;
  feeders: FeatureCollection<LineString>;
  centroids: FeatureCollection<Point>;
};

function hashValue(input: string) {
  let hash = 0;
  for (let index = 0; index < input.length; index += 1) {
    hash = (hash << 5) - hash + input.charCodeAt(index);
    hash |= 0;
  }
  return Math.abs(hash);
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

function buildTwinFeatures(
  center: [number, number],
  buildings: BuildingState[],
  controlEntities: ControlEntity[],
): TwinFeatureSet {
  const [longitude, latitude] = center;
  const coordinateMap = new Map<string, [number, number]>();
  const assets: Feature<Point>[] = [];

  buildings.forEach((building, index) => {
    const angleOffset = (Math.PI * 2 * index) / Math.max(buildings.length, 1);
    const jitter = (hashValue(building.id) % 1000) / 1000;
    const radius = 0.008 + (index % 3) * 0.0035 + (jitter * 0.0018);
    const angle = angleOffset + (jitter * 0.35);
    const lngDelta = (radius * Math.cos(angle)) / Math.max(Math.cos((latitude * Math.PI) / 180), 0.25);
    const latDelta = radius * Math.sin(angle);
    const assetCoordinate: [number, number] = [
      longitude + lngDelta,
      latitude + latDelta,
    ];
    coordinateMap.set(building.id, assetCoordinate);

    assets.push({
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: assetCoordinate,
      },
      properties: {
        id: building.id,
        label: building.id,
        assetType: building.type,
        batterySoc: building.battery_soc,
        netConsumption: building.net_electricity_consumption,
        color: assetColor(building.type),
      },
    });
  });

  const feeders: Feature<LineString>[] = [];
  const centroids: Feature<Point>[] = [];
  controlEntities.forEach((entity) => {
    const memberCoordinates = entity.member_buildings
      .map((member) => coordinateMap.get(member))
      .filter((coordinate): coordinate is [number, number] => Boolean(coordinate));

    if (!memberCoordinates.length) {
      return;
    }

    const centroid: [number, number] = [
      memberCoordinates.reduce((sum, coordinate) => sum + coordinate[0], 0) / memberCoordinates.length,
      memberCoordinates.reduce((sum, coordinate) => sum + coordinate[1], 0) / memberCoordinates.length,
    ];

    centroids.push({
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: centroid,
      },
      properties: {
        id: entity.id,
        label: entity.label,
        role: entity.role,
        memberCount: entity.member_buildings.length,
      },
    });

    if (entity.role === "feeder_coordinator") {
      feeders.push({
        type: "Feature",
        geometry: {
          type: "LineString",
          coordinates: [center, centroid],
        },
        properties: {
          id: entity.id,
          label: entity.label,
          role: entity.role,
        },
      });
    }
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
    feeders: {
      type: "FeatureCollection",
      features: feeders,
    },
    centroids: {
      type: "FeatureCollection",
      features: centroids,
    },
  };
}

function setGeoJsonData(map: MapLibreMap, sourceId: string, data: FeatureCollection<Point> | FeatureCollection<LineString>) {
  const source = map.getSource(sourceId) as GeoJSONSource | undefined;
  if (source) {
    source.setData(data);
  }
}

interface TwinMapCanvasProps {
  geoContext?: GeoContext;
  buildings: BuildingState[];
  controlEntities: ControlEntity[];
  twinSummary?: TwinSummary;
}

export default function TwinMapCanvas({
  geoContext,
  buildings,
  controlEntities,
  twinSummary,
}: TwinMapCanvasProps) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const previousCenterRef = useRef<[number, number] | null>(null);

  const center = useMemo(() => normalizeCenter(geoContext), [geoContext]);
  const twinFeatures = useMemo(
    () => buildTwinFeatures(center, buildings, controlEntities),
    [center, buildings, controlEntities],
  );

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
      center: center as LngLatLike,
      zoom: 10.8,
      pitch: 48,
      bearing: 12,
      attributionControl: false,
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

    map.on("load", () => {
      map.addSource("twin-center", {
        type: "geojson",
        data: twinFeatures.center,
      });
      map.addSource("twin-assets", {
        type: "geojson",
        data: twinFeatures.assets,
      });
      map.addSource("twin-feeders", {
        type: "geojson",
        data: twinFeatures.feeders,
      });
      map.addSource("twin-centroids", {
        type: "geojson",
        data: twinFeatures.centroids,
      });

      map.addLayer({
        id: "twin-feeders-line",
        type: "line",
        source: "twin-feeders",
        paint: {
          "line-color": "#06b6d4",
          "line-width": 2.5,
          "line-opacity": 0.78,
          "line-blur": 0.2,
        },
      });

      map.addLayer({
        id: "twin-centroids-glow",
        type: "circle",
        source: "twin-centroids",
        paint: {
          "circle-radius": 12,
          "circle-color": "rgba(6, 182, 212, 0.18)",
          "circle-stroke-width": 1,
          "circle-stroke-color": "rgba(6, 182, 212, 0.45)",
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

      map.addLayer({
        id: "twin-assets-labels",
        type: "symbol",
        source: "twin-assets",
        layout: {
          "text-field": ["get", "label"],
          "text-size": 11,
          "text-font": ["Open Sans Regular"],
          "text-offset": [0, 1.35],
          "text-anchor": "top",
        },
        paint: {
          "text-color": "#e2e8f0",
          "text-halo-color": "rgba(2, 6, 23, 0.95)",
          "text-halo-width": 1,
        },
      });
    });

    mapRef.current = map;
    previousCenterRef.current = center;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [center, twinFeatures]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) {
      return;
    }

    setGeoJsonData(map, "twin-center", twinFeatures.center);
    setGeoJsonData(map, "twin-assets", twinFeatures.assets);
    setGeoJsonData(map, "twin-feeders", twinFeatures.feeders);
    setGeoJsonData(map, "twin-centroids", twinFeatures.centroids);

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
        <div className="map-eyebrow">Map Stack</div>
        <div className="map-copy">
          {MAP_STYLE_URL ? "Custom MapLibre Style" : "Open fallback style"}
        </div>
        <div className="map-stack-meta">
          {PMTILES_URL ? "PMTiles wired" : "PMTiles ready"}
        </div>
      </div>

      <div className="map-floating-card map-floating-bottom-left">
        <div className="map-eyebrow">Legend</div>
        <div className="map-legend-row">
          <span className="map-dot" style={{ background: "#3b82f6" }} />
          Residential
        </div>
        <div className="map-legend-row">
          <span className="map-dot" style={{ background: "#10b981" }} />
          Commercial
        </div>
        <div className="map-legend-row">
          <span className="map-dot" style={{ background: "#8b5cf6" }} />
          EV fleet
        </div>
        <div className="map-legend-row">
          <span className="map-dot" style={{ background: "#06b6d4" }} />
          Feeder spine
        </div>
      </div>
    </div>
  );
}

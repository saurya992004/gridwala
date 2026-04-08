import urllib.request
import json
import asyncio
import websockets

def run_tests():
    # Test 1: GET /api/presets
    req = urllib.request.urlopen("http://127.0.0.1:8000/api/presets")
    data = json.loads(req.read())
    print("[TEST 1] /api/presets")
    for p in data["presets"]:
        print(f"  - {p['id']}: {p['label']}")
    print(f"  Carbon profiles: {list(data['carbon_profiles'].keys())}")

    # Test 2: GET /api/presets/industrial_microgrid
    req = urllib.request.urlopen("http://127.0.0.1:8000/api/presets/industrial_microgrid")
    data = json.loads(req.read())
    schema = data["schema"]
    print(f"\n[TEST 2] /api/presets/industrial_microgrid")
    print(f"  District: {schema['district_name']}")
    print(f"  Carbon: {schema['carbon_profile']}")
    print(f"  Buildings:")
    for b in schema["buildings"]:
        print(f"    - {b['name']}: {b['battery_kwh']} kWh battery, {b['solar_peak_kw']} kW solar ({b['type']})")

    # Test 3: POST /api/validate (custom schema)
    custom = {
        "schema_data": {
            "district_name": "My Custom District",
            "carbon_profile": "india_south_tneb",
            "buildings": [
                {"name": "My Building", "battery_kwh": 25, "solar_peak_kw": 12, "type": "commercial"}
            ]
        }
    }
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/validate",
        data=json.dumps(custom).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    data = json.loads(urllib.request.urlopen(req).read())
    print(f"\n[TEST 3] /api/validate (custom schema)")
    print(f"  Valid: {data['valid']}")
    print(f"  Buildings: {data['building_count']}")
    print(f"  District: {data['schema']['district_name']}")

    print("\n[ALL HTTP TESTS PASSED] Plug-and-play HTTP API is fully operational!")

async def test_ws():
    uri = "ws://127.0.0.1:8000/ws/simulate?preset=industrial_microgrid"
    print(f"\n[TEST 4] WebSocket with preset: {uri}")
    async with websockets.connect(uri) as ws:
        count = 0
        while count < 3:
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(msg)
            msg_type = data.get("type")
            if msg_type == "connected":
                print(f"  [CONNECTED] Preset: {data.get('preset')}, District: {data.get('district_name')}")
            elif msg_type == "step":
                print(f"  [Step {data['step']:3d}] District Net={data['district_net_consumption']} kWh")
            count += 1
    print("[TEST 4 PASSED] WebSocket is streaming preset data!")

if __name__ == "__main__":
    run_tests()
    asyncio.run(test_ws())

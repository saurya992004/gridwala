import asyncio
import websockets
import json

async def test_forecast_ws():
    uri = "ws://127.0.0.1:8000/ws/simulate"
    print(f"[TEST] Connecting to WS...")
    async with websockets.connect(uri) as ws:
        count = 0
        while count < 8:
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(msg)
            msg_type = data.get("type")
            
            if msg_type == "connected":
                pass
            elif msg_type == "step":
                hr = data["hour"]
                forecast = data.get("forecast_scenario")
                p2p = data.get("p2p_volume_kwh", 0)
                
                print(f"Step {data['step']:3d} | Hour {hr:02d}:00 | Forecast: {forecast}")
                # We'll just look at Building 1's rationale
                for b in data.get("buildings", []):
                    # In simulation_runner, rationales is added to payload root, not strictly inside buildings. Let's check payload root.
                    pass
                
                rationales = data.get("rationales", [])
                if rationales:
                    print(f"  [Agent 1 Rationale] {rationales[0]}")
                print("-" * 50)
                count += 1

                if count == 3:
                    # Inject forecast on step 3
                    print("\n>>> SENDING FORECAST: heatwave in 3 steps <<<")
                    await ws.send(json.dumps({
                        "action": "forecast_emergency",
                        "scenario": "heatwave",
                        "steps": 3
                    }))

if __name__ == "__main__":
    asyncio.run(test_forecast_ws())

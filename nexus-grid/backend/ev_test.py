import asyncio
import websockets
import json

async def test_p2p_ws():
    # We will use the custom validation schema payload to inject an EV and residential building
    custom_schema = {
        "action": "load_schema",
        "schema": {
            "district_name": "V2G Test Microgrid",
            "carbon_profile": "uk_national_grid",
            "buildings": [
                {"name": "Solar Home", "type": "residential", "battery_kwh": 20, "solar_peak_kw": 10},
                {"name": "Tesla Model Model 3", "type": "ev", "battery_kwh": 60, "solar_peak_kw": 0}
            ]
        }
    }
    
    uri = "ws://127.0.0.1:8000/ws/simulate"
    print(f"[TEST] Connecting to WS...")
    async with websockets.connect(uri) as ws:
        # Send custom schema to initialize P2P+EV test
        await ws.send(json.dumps(custom_schema))
        print("Sent custom V2G schema.")
        
        count = 0
        while count < 10:
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(msg)
            msg_type = data.get("type")
            
            if msg_type == "connected":
                pass
            elif msg_type == "step":
                hr = data["hour"]
                p2p = data.get("p2p_volume_kwh", 0)
                
                print(f"Step {data['step']:3d} | Hour {hr:02d}:00 | P2P Traded: {p2p} kWh")
                for b in data["buildings"]:
                    ev_status = "(AWAY)" if b.get("is_ev_away") else "(HOME)"
                    wallet = b.get("nexus_wallet", 0)
                    print(f"  [{b['type'].upper():4s}] {b['id']} {ev_status} | Net: {b['net_electricity_consumption']:6.2f} kW | Wallet: {wallet} $NEXUS | r: {b['reward']}")
                print("-" * 50)
                count += 1
                
if __name__ == "__main__":
    asyncio.run(test_p2p_ws())

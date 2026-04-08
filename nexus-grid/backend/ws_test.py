"""
NEXUS GRID — Phase 2 WebSocket Test
Connects to the running server and prints 6 live step payloads.
Run: python ws_test.py   (with server already running on port 8000)
"""

import asyncio
import json
import websockets


async def test():
    uri = "ws://127.0.0.1:8000/ws/simulate"
    print(f"Connecting to {uri}...")

    async with websockets.connect(uri) as ws:
        count = 0
        while count < 7:
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(msg)
            msg_type = data.get("type")

            if msg_type == "connected":
                buildings = data["buildings"]
                print(f"\n[CONNECTED] Buildings: {buildings}")
                print(f"            Max steps: {data['max_steps']}\n")

            elif msg_type == "step":
                step = data["step"]
                hour = data["hour"]
                carbon = data["carbon_intensity"]
                net = data["district_net_consumption"]
                rationales = data.get("rationales", [])

                print(f"[Step {step:3d}] Hour={hour:02d}h | Carbon={carbon} kgCO2/kWh | Net={net} kWh")

                if rationales and count == 2:
                    print(f"  XAI → {rationales[0]}")

            count += 1

        print("\n[✅ TEST PASSED] WebSocket is streaming live NEXUS GRID simulation data!")


if __name__ == "__main__":
    asyncio.run(test())

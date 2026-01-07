import asyncio
import json
import websockets

connected = set()

async def handler(ws):
    connected.add(ws)
    print("接続:", ws.remote_address)

    try:
        async for msg in ws:
            data = json.loads(msg)

            if data["type"] == "POST":
                message = json.dumps({
                    "type": "POST",
                    "text": data["text"]
                })

                await asyncio.gather(
                    *[c.send(message) for c in connected]
                )
    finally:
        connected.remove(ws)
        print("切断")

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8888):
        print("WebSocket起動 ws://localhost:8888")
        await asyncio.Future()

asyncio.run(main())

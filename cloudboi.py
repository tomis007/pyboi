#! /usr/bin/env python3
import logging
from pyboi import Pyboi
import asyncio
import websockets

#turn off logging
logging.disable(level=logging.CRITICAL)

# websocket handler for streaming gb screen
async def gameboy(websocket, path):
    print(path)
    gb = Pyboi()
    gb.load_rom('roms/tetris.gb')
    while True:
        message = gb.get_boot_frame()
        await websocket.send(bytes(message))

#simple websocket test for graphics
def main():
    start_server = websockets.serve(gameboy, '127.0.0.1', 8888)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    main()


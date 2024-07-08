#!/usr/bin/env python3

import asyncio
import logging
import subprocess
from os import getenv, environ
from os.path import realpath, dirname, isfile
from typing import Dict

import websockets
import json

logger = logging.getLogger(__name__)


async def ws_send_details(ws):
    envs: Dict[str, str] = dict(environ)
    data = {}
    for key, command in envs.items():
        if key.startswith("DETAIL_CMD_"):
            detail_key = key[len("DETAIL_CMD_#") + 1:].lower()
            result = subprocess.check_output(["bash", "-c", command])
            data[detail_key] = str(result.decode("utf-8").strip())
    await ws.send(json.dumps({"event": "details", "data": data}))


async def handle_message(ws, ws_message_string):
    websocket_message = json.loads(ws_message_string)
    event = websocket_message.get("event", "unset")
    data = websocket_message.get("data", {})

    if event == "refresh":
        logger.info("WS: 'refresh' received")
        await ws_send_details(ws)
    elif event == "run":
        logger.info("WS: 'run' received")

        async def respond(result: bool, message: str):
            logger.info("Responding to 'run' result")
            identity: str = data.get("id")
            await ws.send(json.dumps({
                "event": "run_result",
                "data": {
                    "id": identity,
                    "result": result,
                    "message": message,
                },
            }))

        try:
            run_script = getenv("RUN_SCRIPT")
            settings: list = data.get("settings", [])
            run_args = [run_script] + settings
            output = subprocess.check_output(run_args)
        except subprocess.CalledProcessError as exc:
            await respond(result=False, message=f"code={exc.returncode}; {str(exc)}")
            return
        except Exception as exc:
            await respond(result=False, message=str(exc))
            return

        await respond(result=True, message=output.decode('utf-8'))
    elif event == "ping":
        logger.info("WS: 'ping' received")
        await ws.send(json.dumps({"event": "pong"}))
    else:
        logger.error(f"WS: Unknown {event=}")


async def init_details(ws):
    await asyncio.sleep(2)
    await ws_send_details(ws)
    logger.info("Sent init details")


async def main():
    project_root_dir = realpath(dirname(realpath(__file__)) + "/")
    dotenv_file = f"{project_root_dir}/.env"
    if isfile(dotenv_file):
        try:
            from dotenv import load_dotenv
            load_dotenv(dotenv_path=dotenv_file)
        except ImportError:
            pass
    logging.basicConfig(level=getenv("LOGLEVEL", "INFO").upper())

    ws_endpoint = getenv("WS_ENDPOINT", "ws://127.0.0.1")
    ws_headers = {
        "AUTH_TOKEN": getenv("WS_AUTH_TOKEN", "")
    }

    async with websockets.connect(ws_endpoint, extra_headers=ws_headers) as ws:
        await init_details(ws)
        async for message in ws:
            await handle_message(ws, message)


if __name__ == "__main__":
    asyncio.run(main())

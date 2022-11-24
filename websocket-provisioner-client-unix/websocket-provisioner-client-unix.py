#!/usr/bin/env python

import asyncio
import logging
import socket
import subprocess
from os import getenv
from os.path import realpath, dirname, isfile
import subprocess
from typing import Dict
from os import environ

import socketio

logger = logging.getLogger(__name__)


sio = socketio.AsyncClient()


async def ws_send_details():
    envs: Dict[str, str] = dict(environ)
    data = {}
    for key, command in envs.items():
        if key.startswith("DETAIL_CMD_"):
            detail_key = key[len("DETAIL_CMD_#") + 1:].lower()
            result = subprocess.check_output(["bash", "-c", command])
            data[detail_key] = str(result.decode("utf-8").strip())
    await sio.emit("details", data)


@sio.event
async def refresh():
    logger.info("WS: 'refresh' received")
    await ws_send_details()


@sio.event
async def run(data: dict):
    logger.info("WS: 'run' received")

    async def respond(result: bool, message: str):
        logger.info("Responding to 'run' result")
        identity: str = data.get("id")
        await sio.emit("run_result", data={"id": identity, "result": result, "message": message})

    try:
        run_script = getenv("RUN_SCRIPT")
        settings: list = data.get("settings", [])
        run_args = [run_script] + settings
        output = subprocess.check_output(run_args)
    except subprocess.CalledProcessError as exc:
        # Since this is being run on a remote machine, we want the full exception
        # However, it may contain sensitive data!
        await respond(result=False, message=f"code={exc.returncode}; {str(exc)}")
        return
    except Exception as exc:
        # Since this is being run on a remote machine, we want the full exception
        # However, it may contain sensitive data!
        await respond(result=False, message=str(exc))
        return

    # Success
    await respond(result=True, message=output)


@sio.event
async def ping():
    logger.info("WS: 'ping' received")
    await sio.emit("pong")


async def init_details():
    await sio.sleep(2)
    await ws_send_details()
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
    await sio.connect(ws_endpoint, headers=ws_headers)
    sio.start_background_task(init_details)
    await sio.wait()


if __name__ == "__main__":
    asyncio.run(main())

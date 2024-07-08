import os
import uuid
import asyncio
import logging
from typing import Dict, List, Any, Optional
import json
from datetime import datetime
from dataclasses import dataclass
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)
root_dir = os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + "/..")
load_dotenv(dotenv_path=f"{root_dir}/.env")
logging.basicConfig(level=os.getenv("LOGLEVEL", "INFO").upper())


@dataclass
class ClientDetails:
    websocket: WebSocket
    auth_id: int  # auth token id
    connected_on: datetime
    details_on: datetime = None
    details: Optional[Dict[str, Any]] = None  # Client supplied details
    run_last_result_on: datetime = None
    run_last_result: Optional[Dict[str, Any]] = None


class Config:
    SCHEDULER_API_ENABLED = False
    RUN_PORT = os.getenv("RUN_PORT", 80)
    RUN_HOST = os.getenv("RUN_HOST", "0.0.0.0")
    CLIENT_REFRESH_INTERVAL = os.getenv("CLIENT_REFRESH_INTERVAL", 60)


config = Config()
app = FastAPI()

clients: Dict[str, ClientDetails] = {}
scheduler = AsyncIOScheduler()
scheduler.start()


def client_sids() -> List[str]:
    return list(clients.keys())


def get_auth_codes() -> Dict[str, int]:
    key: str
    value: str
    codes = {}
    for key, value in dict(os.environ).items():
        if key.startswith("WS_CLIENT_AUTH_"):
            codes[value] = int(key.removeprefix("WS_CLIENT_AUTH_"))
    return codes


async def msg_all_clients(message: str, data=None):
    for client_sid, client_details in list(clients.items()):
        try:
            await client_details.websocket.send_text(json.dumps({"event": message, "data": data}))
        except Exception:
            # Catch any single client send exceptions and report
            logger.exception(f"Failed to send message to client {client_sid}")


@app.get("/", response_class=PlainTextResponse)
async def index():
    return "Hi!"


@app.get("/clients.txt", response_class=PlainTextResponse)
async def clients_txt():
    logger.info("WEB: Getting all clients")
    results = ["=== CLIENTS ===".ljust(120, "=")]

    fields = {
        "sid": 30,
        "auth_id": 10,
        "connected_on": 30,
        "run_last_result_on": 30,
        "run_last_result": 120,
        "details_on": 30,
        "details": None,
    }

    header = ""
    for key, justify in fields.items():
        if justify is not None:
            header += key.ljust(justify) + "- "
        else:
            header += key

    results.append(header)

    for client_sid, client_details in clients.items():
        client_row = ""
        for key, justify in fields.items():
            value = json.dumps(client_details.__getattribute__(key), default=str)
            if justify is not None:
                client_row += value.ljust(justify) + "- "
            else:
                client_row += value
        results.append(client_row)

    return "\n".join(results)


@app.get("/clients/ping", response_class=PlainTextResponse)
async def clients_ping_all():
    logger.info("WEB: Sending 'ping' to all WebSocket clients")
    await msg_all_clients("ping")
    return "Sent!"


@app.get("/clients/refresh", response_class=PlainTextResponse)
async def clients_info():
    logger.info("WEB: Sending 'refresh' to all WebSocket clients")
    await msg_all_clients("refresh")
    return "Sent!"


@app.put("/client/{sid}/run", response_class=PlainTextResponse)
async def client_sid_run(sid: str, request: Request):
    logger.info("WEB: Sending 'run' to a client")
    identity = str(uuid.uuid4())
    settings = await request.json()
    logger.info("Sending 'run' to sid='%s' run_id='%s'", sid, identity)
    if sid not in client_sids():
        return PlainTextResponse("Failed, SID not found!", status_code=400)
    await clients[sid].websocket.send_text(json.dumps({"event": "run", "data": {"id": identity, "settings": settings}}))
    return "Sent!"


async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    logger.info("Client connected")
    client_auth_token = websocket.headers.get("AUTH_TOKEN", "")

    # Token min length and is set
    if len(client_auth_token) <= 5:
        logger.info("WebSocket Client rejected due to length of or missing auth token")
        await websocket.close()
        return

    # Token verification
    valid_auth_codes = get_auth_codes()
    if client_auth_token not in valid_auth_codes.keys():
        logger.info("WebSocket Client rejected due to auth key not being correct")
        await websocket.close()
        return

    # Valid!
    auth_id = valid_auth_codes[client_auth_token]
    sid = str(uuid.uuid4())
    clients[sid] = ClientDetails(
        websocket=websocket,
        auth_id=auth_id,
        connected_on=datetime.now(),
    )
    logger.info(f"WebSocket Client is valid using key '{auth_id}'")

    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            event = data.get("event")
            if event == "ping":
                logger.info(f"WebSocket received 'ping' from client '{sid}'")
                await websocket.send_text(json.dumps({"event": "pong"}))
            elif event == "details":
                logger.info(f"WebSocket received 'details' from client '{sid}'")
                clients[sid].details_on = datetime.now()
                clients[sid].details = data.get("data")
            elif event == "run_result":
                logger.info(f"WebSocket received 'run_result' from client '{sid}'")
                clients[sid].run_last_result = data.get("data")
                clients[sid].run_last_result_on = datetime.now()
            elif event == "refresh":
                logger.info(f"WebSocket received 'refresh' from client '{sid}'")
                await websocket.send_text(json.dumps({"event": "details", "data": clients[sid].details}))
            elif event == "run":
                logger.info(f"WebSocket received 'run' from client '{sid}'")
                await websocket.send_text(json.dumps({"event": "run_result", "data": {"id": data.get("id"), "result": True, "message": "Run command executed"}}))

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected '{sid}'")
        if sid in clients:
            del clients[sid]
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        if sid in clients:
            del clients[sid]


def ask_clients_refresh():
    asyncio.create_task(msg_all_clients("refresh"))


scheduler.add_job(ask_clients_refresh, 'interval', seconds=config.CLIENT_REFRESH_INTERVAL, max_instances=1)


@app.websocket("/ws")
async def websocket_endpoint_entrypoint(websocket: WebSocket):
    await websocket_endpoint(websocket)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host=config.RUN_HOST, port=config.RUN_PORT)

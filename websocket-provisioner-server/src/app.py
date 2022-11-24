import uuid

import flask
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, make_response
from flask_apscheduler import APScheduler
from flask_socketio import SocketIO
from os import getenv, environ as os_environ
import logging
import eventlet

from dotenv import load_dotenv
from os.path import realpath, dirname
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import socket
import json
from datetime import datetime

# https://stackoverflow.com/questions/71474916/is-it-possible-to-call-socketio-emit-from-a-job-scheduled-via-apscheduler-backg
eventlet.monkey_patch(thread=True, time=True)

logger = logging.getLogger(__name__)
root_dir = realpath(dirname(realpath(__file__)) + "/..")
load_dotenv(dotenv_path=f"{root_dir}/.env")
logging.basicConfig(level=getenv("LOGLEVEL", "INFO").upper())


@dataclass
class ClientDetails:
    sid: str
    auth_id: int  # auth token id
    connected_on: datetime
    # details = Client supplied details
    details_on: datetime = None
    details: Optional[Dict[str, Any]] = None
    run_last_result_on: datetime = None
    run_last_result: Optional[Dict[str, Any]] = None


class Config:
    SCHEDULER_API_ENABLED = False
    RUN_PORT = getenv("RUN_PORT", 80)
    RUN_HOST = getenv("RUN_HOST", "0.0.0.0")
    CLIENT_REFRESH_INTERVAL = getenv("CLIENT_REFRESH_INTERVAL", 60)


app = Flask(__name__)
app.config.from_object(Config())
sio = SocketIO(app, cors_allowed_origins="*")

hostname = socket.gethostname()
scheduler = BackgroundScheduler()
flask_scheduler = APScheduler(scheduler)
flask_scheduler.init_app(app)
logger.info("")

clients: Dict[str, ClientDetails] = {}


def client_sids() -> List[str]:
    return list(clients.keys())


def get_auth_codes() -> Dict[str, int]:
    key: str
    value: str
    codes = {}
    for key, value in dict(os_environ).items():
        if key.startswith("WS_CLIENT_AUTH_"):
            codes[value] = int(key.removeprefix("WS_CLIENT_AUTH_"))
    return codes


def msg_all_clients(message: str, data=None):
    for client in list(clients.keys()):
        try:
            sio.emit(message, data, to=client)
        except Exception:
            # Catch any single client send exceptions and report
            logger.exception("")


@app.route("/")
def index():
    response = make_response("Hi!", 200)
    response.mimetype = "text/plain"
    return response


@app.route("/clients.txt")
def clients_txt():
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

    response = make_response("\n".join(results), 200)
    response.mimetype = "text/plain"
    return response


@app.route("/clients/ping")
def clients_ping_all():
    logger.info("WEB: Sending 'ping' to all SIO clients")
    msg_all_clients("ping")
    response = make_response("Sent!", 200)
    response.mimetype = "text/plain"
    return response


@app.route("/clients/refresh")
def clients_info():
    logger.info("WEB: Sending 'refresh' to all SIO clients")
    msg_all_clients("refresh")
    response = make_response("Sent!", 200)
    response.mimetype = "text/plain"
    return response


@app.route("/client/<sid>/run", methods=['PUT'])
def client_sid_run(sid):
    logger.info("WEB: Sending 'run' to a client")
    identity = str(uuid.uuid4())
    settings = flask.request.get_json()
    logger.info("Sending 'run' to sid='%s' run_id='%s'", sid, identity)
    if sid not in client_sids():
        response = make_response("Failed, SID not found!", 400)
        response.mimetype = "text/plain"
        return response
    sio.emit("run", {"id": identity, "settings": settings}, to=sid)
    response = make_response("Sent!", 200)
    response.mimetype = "text/plain"
    return response


@sio.event
def connect():
    sid = flask.request.sid
    logger.info("SIO client connected '%s'", sid)

    client_auth_token = flask.request.headers.get("AUTH_TOKEN", "")

    # Token min length and is set
    if len(client_auth_token) <= 5:
        logger.info("SIO Client rejected due to length of or missing auth token")
        sio.disconnect(sid)
        return

    # Token verification
    valid_auth_codes = get_auth_codes()
    if client_auth_token not in valid_auth_codes.keys():
        logger.info("SIO Client rejected due to auth key not being correct")
        sio.disconnect(sid)
        return

    # Valid!
    auth_id = valid_auth_codes[client_auth_token]
    clients[sid] = ClientDetails(
        sid=sid,
        auth_id=auth_id,
        connected_on=datetime.now(),
    )
    logger.info(f"SIO Client is valid using key '%d'", auth_id)


@sio.event
def disconnect():
    sid = flask.request.sid
    logger.info("SIO client disconnected '%s'", sid)
    if sid in clients:
        del clients[sid]


@sio.event
def pong():
    sid = flask.request.sid
    logger.info("SIO received 'pong' from client '%s'", sid)


@sio.event
def details(device_details):
    sid = flask.request.sid
    logger.info("SIO received 'details' from client '%s'", sid)
    clients[sid].details_on = datetime.now()
    clients[sid].details = device_details


@sio.event
def run_result(run_result_details: Dict[str, Any]):
    sid = flask.request.sid
    logger.info("SIO received 'run_result' from client '%s'", sid)
    clients[sid].run_last_result = run_result_details
    clients[sid].run_last_result_on = datetime.now()


def ask_clients_refresh():
    msg_all_clients("refresh")


scheduler.add_job(ask_clients_refresh, 'interval', seconds=app.config.get("CLIENT_REFRESH_INTERVAL"), max_instances=1)
flask_scheduler.start()

if __name__ == '__main__':
    sio.run(app, host=app.config.get("RUN_HOST"), port=app.config.get("RUN_PORT"))

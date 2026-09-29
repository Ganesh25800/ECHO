from pathlib import Path
import threading
import time
import subprocess
import asyncio

import requests
import uvicorn

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


# ===========================================================
# CONFIGURATION
# ===========================================================

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

HOST = "127.0.0.1"
PORT = 8000

URL = f"http://{HOST}:{PORT}"


# ===========================================================
# WEBSOCKET CONFIGURATION
# ===========================================================

# Stores all currently connected frontend WebSockets
websocket_connections = []

# Stores FastAPI's asyncio event loop.
# TTS runs in another thread, so we use this loop to safely
# send events from the TTS thread to the frontend.
server_loop = None


# ===========================================================
# FRONTEND STATIC FILES
# ===========================================================

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static"
)


# ===========================================================
# MAIN FRONTEND
# ===========================================================

@app.get("/")
def get_frontend():

    return FileResponse(
        FRONTEND_DIR / "index.html"
    )


# ===========================================================
# REST API STATUS
# ===========================================================

@app.get("/api/status")
def get_echo_status():

    return {
        "status": "running",
        "message": "ECHO API is working"
    }


# ===========================================================
# WEBSOCKET
# ===========================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    global server_loop

    # Get FastAPI's currently running asyncio loop
    server_loop = asyncio.get_running_loop()

    # Accept browser connection
    await websocket.accept()

    # Store browser connection
    websocket_connections.append(websocket)

    print("ECHO frontend connected.")

    try:

        # Keep WebSocket connection alive
        while True:

            await websocket.receive_text()

    except WebSocketDisconnect:

        if websocket in websocket_connections:
            websocket_connections.remove(websocket)

        print("ECHO frontend disconnected.")

    except Exception as error:

        if websocket in websocket_connections:
            websocket_connections.remove(websocket)

        print(
            f"ECHO WebSocket error: {error}"
        )


# ===========================================================
# SEND EVENT TO ALL CONNECTED FRONTENDS
# ===========================================================

async def notify_frontend(event):

    disconnected = []

    for websocket in websocket_connections:

        try:

            await websocket.send_json(
                {
                    "event": event
                }
            )

        except Exception:

            disconnected.append(
                websocket
            )


    # Remove broken/disconnected connections
    for websocket in disconnected:

        if websocket in websocket_connections:

            websocket_connections.remove(
                websocket
            )


# ===========================================================
# THREAD-SAFE FRONTEND EVENT
# ===========================================================

def send_frontend_event(event):

    # Frontend hasn't connected yet
    if server_loop is None:
        return False


    # No browser currently connected
    if not websocket_connections:
        return False


    try:

        asyncio.run_coroutine_threadsafe(
            notify_frontend(event),
            server_loop
        )

        return True

    except Exception as error:

        print(
            f"Unable to send frontend event: {error}"
        )

        return False


# ===========================================================
# RUN UVICORN SERVER
# ===========================================================

def run_server():

    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        reload=False
    )


# ===========================================================
# WAIT UNTIL SERVER IS READY
# ===========================================================

def wait_for_server(timeout=15):

    start_time = time.time()

    while time.time() - start_time < timeout:

        try:

            response = requests.get(
                f"{URL}/api/status",
                timeout=1
            )

            if response.status_code == 200:

                return True


        except requests.RequestException:

            pass


        time.sleep(0.25)


    return False


# ===========================================================
# OPEN ECHO FRONTEND
# ===========================================================

def open_frontend():

    try:

        subprocess.Popen(
            [
                "open",
                "-a",
                "Google Chrome",
                URL
            ]
        )

        return True


    except Exception as error:

        print(
            f"Unable to open ECHO frontend: {error}"
        )

        return False


# ===========================================================
# START ECHO SERVER
# ===========================================================

def start_server():

    server_thread = threading.Thread(
        target=run_server,
        name="EchoAPIServer",
        daemon=True
    )


    # Start FastAPI in background
    server_thread.start()


    # Wait until FastAPI responds
    if wait_for_server():

        print(
            "ECHO server is ready."
        )


        # Open Chrome
        open_frontend()


        return True


    print(
        "ECHO server failed to start."
    )

    return False
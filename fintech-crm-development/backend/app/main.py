import asyncio
from typing import Annotated

from fastapi import (
    Cookie,
    Depends,
    FastAPI,
    Query,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
    status,
)
from fastapi.responses import HTMLResponse
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.utils.generate_welcome_page import generate_welcome_page
from app.api.api_v1 import deps
from app.api.api_v1.api import api_router
from app.core.config import settings
from app.core.kafka import KafkaConsumer
from app.core.websocket import websocket_manager,websocket_manager_notifications
from app.db.session import database, engine, metadata

loop = asyncio.get_event_loop()
metadata.create_all(engine)

app = FastAPI(title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json")

kafka_consumer = None
kafka_websocket_consumer = None


@app.get("/")
async def root():
    return generate_welcome_page()


@app.on_event("startup")
async def startup():
    await database.connect()
    consume_kafka()
    consume_websocket_kafka()
    metadata.create_all(engine)


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


async def get_cookie_or_token(
    websocket: WebSocket,
    session: Annotated[str | None, Cookie()] = None,
    token: Annotated[str | None, Query()] = None,
):
    if session is None and token is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    return session or token


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    # cookie_or_token: Annotated[str, Depends(get_cookie_or_token)],
):
    """
    Websocket endpoint to send messages to the client
    Using JWT token to verify the user
    """
    # await deps.websocket_auth(cookie_or_token)
    await websocket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket_manager.broadcast(data)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
        
@app.websocket("/ws/notifications")
async def notification_websocket_endpoint(websocket: WebSocket):
    await websocket_manager_notifications.connect(websocket)
    try:
        while True:
            await asyncio.sleep(1)  
    except WebSocketDisconnect:
        websocket_manager_notifications.disconnect(websocket)


def consume_kafka():
    global kafka_consumer
    kafka_consumer = KafkaConsumer(loop)
    asyncio.create_task(kafka_consumer.consume())


def consume_websocket_kafka():
    global kafka_websocket_consumer
    kafka_websocket_consumer = KafkaConsumer(loop)
    asyncio.create_task(kafka_websocket_consumer.send_via_websocket())
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  
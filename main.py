import os
import time
import logging
import asyncio
import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("app.main")

from app.database import init_db, SessionLocal, Strike, get_config_val
from app.hardware import sensor_hardware, gpio_manager
from app.display_manager import display_manager
from app.websocket import manager as ws_manager
from app.telegram import send_telegram_notification
from app.api import router as api_router

main_loop = None

def callback_handle(channel):
    """
    AS3935 hardware/mock interrupt handler.
    Called when the IRQ pin transitions from low to high.
    """
    logger.info("Sensor hardware interrupt detected!")
    # Wait 5ms as recommended in sensor datasheet
    time.sleep(0.005)
    
    try:
        int_src = sensor_hardware.get_interrupt_src()
        logger.info(f"Read interrupt source register value: {int_src}")

        db = SessionLocal()
        try:
            if int_src == 1:  # Lightning strike
                dist = sensor_hardware.get_lightning_distKm()
                intensity = sensor_hardware.get_strike_energy_raw()
                logger.info(f"⚡ Strike Detected! Distance: {dist}km, Intensity: {intensity}")

                # Record in database
                strike = Strike(distance=dist, intensity=intensity)
                db.add(strike)
                db.commit()
                db.refresh(strike)

                # Broadcast strike notification to WebSocket clients
                if main_loop is not None:
                    coro_ws = ws_manager.broadcast({
                        "type": "strike",
                        "data": {
                            "id": strike.id,
                            "distance": strike.distance,
                            "intensity": strike.intensity,
                            "timestamp": strike.timestamp.isoformat()
                        }
                    })
                    asyncio.run_coroutine_threadsafe(coro_ws, main_loop)

                    # Send Telegram Notification
                    coro_tg = send_telegram_notification(db, strike)
                    asyncio.run_coroutine_threadsafe(coro_tg, main_loop)

                # Trigger Waveshare display update
                display_manager.trigger_update()

            elif int_src == 2:  # Disturber detected
                logger.warning("Disturber discovered!")
                if main_loop is not None:
                    coro_warn = ws_manager.broadcast({
                        "type": "warning",
                        "data": {
                            "message": "Disturber discovered!",
                            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
                        }
                    })
                    asyncio.run_coroutine_threadsafe(coro_warn, main_loop)

            elif int_src == 3:  # Noise level too high
                logger.warning("Noise level too high!")
                if main_loop is not None:
                    coro_warn = ws_manager.broadcast({
                        "type": "warning",
                        "data": {
                            "message": "Noise level too high!",
                            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
                        }
                    })
                    asyncio.run_coroutine_threadsafe(coro_warn, main_loop)

        except Exception as err:
            logger.error(f"Error handling interrupt in db/ws dispatch: {err}")
        finally:
            db.close()

    except Exception as err:
        logger.error(f"Failed to read interrupt source from sensor: {err}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global main_loop
    main_loop = asyncio.get_running_loop()
    
    # Initialize DB schemas
    init_db()
    logger.info("Database initialized successfully.")
    
    # Read default settings from database, calibrating AS3935 sensor
    db = SessionLocal()
    try:
        capacitance = int(get_config_val(db, "capacitance", "96"))
        location = int(get_config_val(db, "location", "0"))
        disturber = int(get_config_val(db, "disturber", "1"))
        noise_floor = int(get_config_val(db, "noise_floor", "2"))
        watchdog = int(get_config_val(db, "watchdog", "2"))
        spike_rejection = int(get_config_val(db, "spike_rejection", "2"))
        
        # Apply settings
        sensor_hardware.reset()
        sensor_hardware.manual_cal(capacitance, location, disturber)
        sensor_hardware.set_noise_floor_lv1(noise_floor)
        sensor_hardware.set_watchdog_threshold(watchdog)
        sensor_hardware.set_spike_rejection(spike_rejection)
        logger.info("AS3935 Sensor calibration parameters written successfully.")
    except Exception as e:
        logger.error(f"AS3935 Sensor startup calibration failed: {e}")
    finally:
        db.close()
        
    # Configure GPIO interrupts
    gpio_manager.setup_interrupt(callback_handle)
    
    # Run display background loop
    display_manager.start()
    
    yield
    
    # Clean shutdown
    display_manager.stop()
    gpio_manager.cleanup()
    logger.info("Application shut down cleanly.")

# Create FastAPI Instance
app = FastAPI(
    title="RPi Lightning Tracker",
    description="AS3935 Lightning tracker server",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Backend API Router
app.include_router(api_router, prefix="/api")

# Live Broadcast WebSocket route
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep socket alive and respond to client close requests
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket client error: {e}")
        ws_manager.disconnect(websocket)

# Mount frontend bundle if it exists
frontend_dist = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
else:
    logger.warning("Vue static bundle not found at frontend/dist. Serving default landing page.")
    @app.get("/")
    def fallback_root():
        return HTMLResponse(content="""
        <html>
            <head>
                <title>Lightning Radar Server</title>
                <style>
                    body {
                        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                        background: #0d0d15;
                        color: #ffffff;
                        text-align: center;
                        padding-top: 15vh;
                    }
                    .container {
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 40px;
                        background: rgba(255, 255, 255, 0.03);
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        border-radius: 16px;
                        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
                        backdrop-filter: blur(8px);
                    }
                    h1 { color: #f59e0b; margin-bottom: 8px; }
                    p { color: #9ca3af; font-size: 1.1em; line-height: 1.6; }
                    .badge {
                        display: inline-block;
                        padding: 6px 12px;
                        background: rgba(245, 158, 11, 0.1);
                        color: #f59e0b;
                        border: 1px solid rgba(245, 158, 11, 0.3);
                        border-radius: 20px;
                        font-size: 0.9em;
                        font-weight: 500;
                        margin-top: 16px;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>⚡ Lightning Tracker Server Running</h1>
                    <p>The FastAPI API backend is successfully listening, but the frontend static distribution has not been built yet.</p>
                    <div class="badge">Running in Mock/Development Mode</div>
                </div>
            </body>
        </html>
        """)

def main():
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()

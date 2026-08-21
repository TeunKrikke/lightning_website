import datetime
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db, Strike, get_config_val, set_config_val
from app.schemas import (
    StrikeResponse, StatsResponse, SensorConfigResponse, 
    SensorConfigUpdate, StrikeCreate, TelegramTestRequest,
    DiagnosticResponse, ToggleMockErrorRequest
)
from app.hardware import sensor_hardware, gpio_manager, IS_MOCK_AS3935, IS_MOCK_LCD
from app.websocket import manager as ws_manager
from app.display_manager import display_manager
from app.telegram import send_telegram_notification, send_test_message

logger = logging.getLogger("app.api")
router = APIRouter()

@router.get("/strikes/recent", response_model=List[StrikeResponse])
def get_recent_strikes(limit: int = 50, db: Session = Depends(get_db)):
    """
    Fetch the list of recent strikes, ordered by newest first.
    """
    strikes = db.query(Strike).order_by(Strike.timestamp.desc()).limit(limit).all()
    return strikes

@router.get("/strikes/stats", response_model=StatsResponse)
def get_strike_stats(db: Session = Depends(get_db)):
    """
    Calculate summary metrics of detected strikes.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    day_ago = now - datetime.timedelta(days=1)
    week_ago = now - datetime.timedelta(days=7)

    amount_24h = db.query(Strike).filter(Strike.timestamp >= day_ago).count()
    amount_7d = db.query(Strike).filter(Strike.timestamp >= week_ago).count()

    # Aggregates
    stats = db.query(
        func.avg(Strike.distance).label("avg_dist"),
        func.avg(Strike.intensity).label("avg_int"),
        func.min(Strike.distance).label("min_dist")
    ).first()

    return StatsResponse(
        amount_24h=amount_24h,
        amount_7d=amount_7d,
        avg_distance=round(float(stats.avg_dist or 0.0), 1),
        avg_intensity=round(float(stats.avg_int or 0.0), 1),
        closest_distance=stats.min_dist
    )

@router.get("/sensor/status", response_model=SensorConfigResponse)
def get_sensor_status(db: Session = Depends(get_db)):
    """
    Read active settings and calibration values.
    """
    try:
        # Get settings from database config, defaulting to standard calibration values
        capacitance = int(get_config_val(db, "capacitance", "96"))
        location = int(get_config_val(db, "location", "0"))  # 0: Indoors, 1: Outdoors
        disturber = int(get_config_val(db, "disturber", "1"))  # 0: Disabled, 1: Enabled
        noise_floor = int(get_config_val(db, "noise_floor", "2"))
        watchdog = int(get_config_val(db, "watchdog", "2"))
        spike_rejection = int(get_config_val(db, "spike_rejection", "2"))
        display_active_start = int(get_config_val(db, "display_active_start", "8"))
        display_active_end = int(get_config_val(db, "display_active_end", "20"))
        
        telegram_enabled = get_config_val(db, "telegram_enabled", "false").lower() == "true"
        telegram_token = get_config_val(db, "telegram_token", "")
        telegram_chat_id = get_config_val(db, "telegram_chat_id", "")

        return SensorConfigResponse(
            capacitance=capacitance,
            location=location,
            disturber=disturber,
            noise_floor=noise_floor,
            watchdog=watchdog,
            spike_rejection=spike_rejection,
            display_active_start=display_active_start,
            display_active_end=display_active_end,
            telegram_enabled=telegram_enabled,
            telegram_token=telegram_token,
            telegram_chat_id=telegram_chat_id,
            is_mock_as3935=IS_MOCK_AS3935,
            is_mock_lcd=IS_MOCK_LCD
        )
    except Exception as e:
        logger.error(f"Error loading sensor configuration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error reading config.")

@router.post("/sensor/config", response_model=SensorConfigResponse)
def update_sensor_config(config: SensorConfigUpdate, db: Session = Depends(get_db)):
    """
    Update calibration and system configuration properties.
    """
    try:
        # Save to database
        set_config_val(db, "capacitance", str(config.capacitance))
        set_config_val(db, "location", str(config.location))
        set_config_val(db, "disturber", str(config.disturber))
        set_config_val(db, "noise_floor", str(config.noise_floor))
        set_config_val(db, "watchdog", str(config.watchdog))
        set_config_val(db, "spike_rejection", str(config.spike_rejection))
        set_config_val(db, "display_active_start", str(config.display_active_start))
        set_config_val(db, "display_active_end", str(config.display_active_end))
        set_config_val(db, "telegram_enabled", str(config.telegram_enabled).lower())
        set_config_val(db, "telegram_token", config.telegram_token)
        set_config_val(db, "telegram_chat_id", config.telegram_chat_id)

        # Apply calibration values to actual or mock hardware
        try:
            sensor_hardware.manual_cal(config.capacitance, config.location, config.disturber)
            sensor_hardware.set_noise_floor_lv1(config.noise_floor)
            sensor_hardware.set_watchdog_threshold(config.watchdog)
            sensor_hardware.set_spike_rejection(config.spike_rejection)
        except Exception as hw_err:
            logger.error(f"Failed to write calibration settings directly to sensor: {hw_err}")

        # Trigger an immediate redraw in display manager to pick up any updated display timing
        display_manager.trigger_update()

        return get_sensor_status(db)
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error updating config.")

@router.post("/strikes/simulate", response_model=StrikeResponse)
async def simulate_strike(payload: StrikeCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Force-injects a simulated strike to verify the detection pipeline.
    """
    try:
        if IS_MOCK_AS3935:
            # Full simulation loop: set state on mock sensor and trigger fake GPIO interrupt
            sensor_hardware.simulate_strike_event(payload.distance, payload.intensity)
            gpio_manager.trigger_mock_interrupt()

            # Wait briefly for background thread to process database write
            time_spent = 0.0
            strike = None
            import asyncio
            while time_spent < 1.0:
                time_spent += 0.05
                await asyncio.sleep(0.05) # yield control
                strike = db.query(Strike).order_by(Strike.timestamp.desc()).first()
                if strike and strike.distance == payload.distance and strike.intensity == payload.intensity:
                    # Check that it is a very recent insert
                    now = datetime.datetime.now(datetime.timezone.utc)
                    if (now - strike.timestamp).total_seconds() < 2:
                        break
            
            if not strike:
                raise HTTPException(status_code=500, detail="Mock pipeline failed to write strike record.")
            return strike

        else:
            # Physical hardware is active. We don't want to interfere with GPIO callbacks,
            # so we directly record the strike, broadcast WebSocket event, update display, and send Telegram alerts.
            new_strike = Strike(
                distance=payload.distance,
                intensity=payload.intensity,
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            db.add(new_strike)
            db.commit()
            db.refresh(new_strike)

            # Broadcast WebSocket updates to open browsers
            await ws_manager.broadcast({
                "type": "strike",
                "data": {
                    "id": new_strike.id,
                    "distance": new_strike.distance,
                    "intensity": new_strike.intensity,
                    "timestamp": new_strike.timestamp.isoformat()
                }
            })

            # Redraw Waveshare LCD screen
            display_manager.trigger_update()

            # Alert Telegram Bot asynchronously
            background_tasks.add_task(send_telegram_notification, db, new_strike)

            return new_strike
    except Exception as e:
        logger.error(f"Failed to simulate strike: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/telegram/test")
async def test_telegram(payload: TelegramTestRequest):
    """
    Send a test Telegram message.
    """
    success = await send_test_message(payload.token, payload.chat_id)
    if success:
        return {"status": "success", "message": "Test message sent successfully!"}
    else:
        raise HTTPException(status_code=400, detail="Failed to send Telegram test message. Check token and chat ID.")

@router.get("/sensor/diagnostics", response_model=DiagnosticResponse)
def get_sensor_diagnostics(db: Session = Depends(get_db)):
    """
    Query the AS3935 sensor hardware registers and run diagnostics.
    """
    try:
        # Load the configuration targets from database
        db_config = {
            "capacitance": int(get_config_val(db, "capacitance", "96")),
            "location": int(get_config_val(db, "location", "0")),
            "disturber": int(get_config_val(db, "disturber", "1")),
            "noise_floor": int(get_config_val(db, "noise_floor", "2")),
            "watchdog": int(get_config_val(db, "watchdog", "2")),
            "spike_rejection": int(get_config_val(db, "spike_rejection", "2"))
        }

        # Run checks on hardware wrapper
        diag_data = sensor_hardware.get_diagnostics(db_config)

        # Evaluate health status
        status = "healthy"
        message = "AS3935 sensor communication is active and properly calibrated."
        recommendations = []

        if not diag_data["i2c_connected"]:
            status = "error"
            message = f"Sensor communication failure: {diag_data['error_message'] or 'Cannot read registers'}"
            recommendations.extend([
                "Check physical I2C wiring: ensure SDA/SCL, VCC (3.3V/5V), and GND are securely connected.",
                "Verify I2C interface is enabled on the Raspberry Pi (run 'ls /dev/i2c*' or check interface settings in raspi-config).",
                "Ensure I2C pull-up resistors are installed (usually built into the DFRobot Gravity breakout board).",
                "Verify the configured sensor address (default 0x03) matches your sensor board's hardware address solder-bridges.",
                "Run 'sudo i2cdetect -y 1' in the Pi terminal to verify if the chip appears on the bus."
            ])
        elif diag_data["is_mock"]:
            status = "warning"
            message = "System is running in simulation mode. Hardware drivers could not be loaded."
            recommendations.extend([
                "Ensure the application is running directly on the Raspberry Pi host hardware.",
                "Run the installation shell script './setup.sh' to compile and install all required native dependencies.",
                "Check system logs to see why physical libraries failed to load."
            ])
        else:
            # Check for matches
            mismatches = []
            if not diag_data["capacitance_match"]:
                mismatches.append(f"Capacitance ({diag_data['capacitance_read']}pF read vs {db_config['capacitance']}pF configured)")
            if not diag_data["location_match"]:
                mismatches.append(f"Environment Mode ({diag_data['location_read']} read vs {db_config['location']} configured)")
            if not diag_data["disturber_match"]:
                mismatches.append(f"Disturber Mask ({diag_data['disturber_read']} read)")
            if not diag_data["noise_floor_match"]:
                mismatches.append(f"Noise Floor ({diag_data['noise_floor_read']} read vs {db_config['noise_floor']} configured)")
            if not diag_data["watchdog_match"]:
                mismatches.append(f"Watchdog Threshold ({diag_data['watchdog_read']} read vs {db_config['watchdog']} configured)")
            if not diag_data["spike_rejection_match"]:
                mismatches.append(f"Spike Rejection ({diag_data['spike_rejection_read']} read vs {db_config['spike_rejection']} configured)")

            if mismatches:
                status = "warning"
                message = f"Configuration mismatch detected for: {', '.join(mismatches)}."
                recommendations.extend([
                    "Navigate to the Calibration Console tab and hit 'Save Configuration' to force-rewrite register values.",
                    "Verify power supply stability: voltage fluctuations on the 3.3V rail can cause register write corruption."
                ])
            else:
                # Connected and matching, but user complained they aren't seeing lightnings.
                # Provide advanced calibration/tuning hints.
                recommendations.extend([
                    "Verify antenna tuning: The AS3935 requires its LC circuit to be tuned precisely to 500kHz (±3.5%). The default is 96pF, but component tolerances may require selecting another value.",
                    "Verify the IRQ pin connection: Check if the BCM 4 (Pin 7) is wired securely. The Pi cannot receive strike detection alerts if the IRQ interrupt link is broken.",
                    "High noise floor levels: If your environment has excessive electromagnetic interference (EMI) from routers or appliances, the sensor might trigger noise/disturber interrupts instead of lightning strikes. Try relocating the sensor.",
                    "Verify the hardware detection pipeline: Press the 'Simulate Strike' button on the Dashboard tab to inject a test interrupt and verify the server database + frontend refresh chain."
                ])

        return {
            "status": status,
            "message": message,
            "details": diag_data,
            "recommendations": recommendations
        }
    except Exception as e:
        logger.error(f"Error compiling diagnostics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sensor/diagnostics/toggle-mock-error")
def toggle_mock_diagnostics_error(payload: ToggleMockErrorRequest):
    """
    Allow developers to toggle I2C failures on the mock sensor to test UI error behaviors.
    """
    try:
        # Check if physical or mock
        sensor_obj = sensor_hardware._sensor
        if hasattr(sensor_obj, "mock_i2c_failure"):
            sensor_obj.mock_i2c_failure = payload.enable_error
            return {
                "status": "success",
                "mock_i2c_failure": sensor_obj.mock_i2c_failure,
                "message": f"Mock I2C failure set to {sensor_obj.mock_i2c_failure}"
            }
        else:
            raise HTTPException(status_code=400, detail="Cannot toggle mock error on physical hardware.")
    except Exception as e:
        logger.error(f"Failed to toggle mock error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

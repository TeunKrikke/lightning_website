import os
import time
import logging
import threading
import datetime
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.orm import Session
from app.config import DISPLAY_ACTIVE_START, DISPLAY_ACTIVE_END
from app.database import SessionLocal, Strike, get_config_val
from app.hardware import WaveshareDisplayWrapper

logger = logging.getLogger("app.display_manager")

FONT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "waveshare_lib",
    "Font01.ttf"
)

class DisplayManager:
    def __init__(self):
        self.display = WaveshareDisplayWrapper()
        self.display_initialized = False
        self.thread = None
        self.running = False
        self.last_state = None  # Track whether screen was ON or OFF
        self.redraw_event = threading.Event()

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._display_loop, daemon=True)
        self.thread.start()
        logger.info("Display manager background loop started.")

    def stop(self):
        self.running = False
        self.redraw_event.set()
        if self.thread:
            self.thread.join()
        try:
            self.display.module_exit()
        except Exception as e:
            logger.error(f"Error during display exit: {e}")
        logger.info("Display manager stopped.")

    def trigger_update(self):
        """Trigger an immediate redraw of the screen"""
        self.redraw_event.set()

    def _display_loop(self):
        # Initialize the hardware screen
        try:
            self.display.Init()
            self.display_initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize display hardware: {e}")

        while self.running:
            self._update_display()
            # Wait for 30 seconds or until an immediate redraw is triggered
            self.redraw_event.wait(timeout=30)
            self.redraw_event.clear()

    def _update_display(self):
        if not self.display_initialized:
            return

        db = SessionLocal()
        try:
            # Load display active hours dynamically from config table, fallback to env config defaults
            start_hour = int(get_config_val(db, "display_active_start", str(DISPLAY_ACTIVE_START)))
            end_hour = int(get_config_val(db, "display_active_end", str(DISPLAY_ACTIVE_END)))

            now = datetime.datetime.now()
            current_hour = now.hour
            is_active_window = start_hour <= current_hour < end_hour

            if not is_active_window:
                # Should be off
                if self.last_state != "OFF":
                    logger.info("Outside active hours window. Turning display off.")
                    try:
                        self.display.clear()
                        self.display.bl_DutyCycle(0)
                        self.last_state = "OFF"
                    except Exception as e:
                        logger.error(f"Failed to turn off screen backlight: {e}")
                return

            # Should be on, redraw screen
            logger.debug("Active window. Drawing recent strikes to display.")
            try:
                # Turn backlight on (e.g. 50% for longevity)
                self.display.bl_DutyCycle(50)

                # Fetch 3 most recent strikes
                recent_strikes = db.query(Strike).order_by(Strike.timestamp.desc()).limit(3).all()

                # Generate PIL Image (240x135)
                image = Image.new("RGB", (self.display.width, self.display.height), "BLACK")
                draw = ImageDraw.Draw(image)

                # Load fonts
                try:
                    title_font = ImageFont.truetype(FONT_PATH, 16)
                    body_font = ImageFont.truetype(FONT_PATH, 12)
                except Exception as font_err:
                    logger.warning(f"Could not load custom font, using default: {font_err}")
                    title_font = ImageFont.load_default()
                    body_font = ImageFont.load_default()

                # Header
                draw.rectangle([(0, 0), (self.display.width, 24)], fill=(20, 20, 40))
                draw.text((10, 4), "⚡ RECENT STRIKES ⚡", font=title_font, fill=(255, 200, 0))

                # List recent strikes
                y_offset = 30
                if not recent_strikes:
                    draw.text((40, 60), "Listening for strikes...", font=body_font, fill=(150, 150, 150))
                else:
                    for idx, strike in enumerate(recent_strikes):
                        # Convert to local time or keep short time
                        strike_time = strike.timestamp.astimezone().strftime("%H:%M:%S")
                        
                        # Style text based on distance (closer is brighter/alert)
                        color = (255, 50, 50) if strike.distance < 10 else (255, 165, 0) if strike.distance < 25 else (0, 255, 150)
                        
                        text = f"{idx+1}. Dist: {strike.distance}km  |  Int: {strike.intensity}"
                        draw.text((10, y_offset), text, font=body_font, fill=color)
                        draw.text((180, y_offset), strike_time, font=body_font, fill=(200, 200, 200))
                        
                        # Add a separator line
                        draw.line([(5, y_offset+16), (235, y_offset+16)], fill=(40, 40, 40), width=1)
                        y_offset += 24

                # Send image buffer to physical/mock display
                self.display.ShowImage(image)
                self.last_state = "ON"

            except Exception as draw_err:
                logger.error(f"Failed to draw to display: {draw_err}")

        finally:
            db.close()

# Singleton Display Manager instance
display_manager = DisplayManager()

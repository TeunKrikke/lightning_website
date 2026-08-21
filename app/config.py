import os

# Database configurations
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://lightning_user:lightning_pass@localhost:5432/lightning_db"
)

# Test/Development database url (SQLite in-memory for tests)
TEST_DATABASE_URL = "sqlite:///:memory:"

# AS3935 Sensor configuration defaults
# I2C Address options are 0x01, 0x02, or 0x03
I2C_ADDR = int(os.getenv("AS3935_I2C_ADDR", "3"), 16) if os.getenv("AS3935_I2C_ADDR") else 0x03
I2C_BUS = int(os.getenv("AS3935_I2C_BUS", "1"))
IRQ_PIN = int(os.getenv("AS3935_IRQ_PIN", "4"))  # Board mode Pin 7 (BCM 4)

# Waveshare LCD Display configuration defaults
DISPLAY_RST_PIN = int(os.getenv("DISPLAY_RST_PIN", "27"))
DISPLAY_DC_PIN = int(os.getenv("DISPLAY_DC_PIN", "25"))
DISPLAY_BL_PIN = int(os.getenv("DISPLAY_BL_PIN", "18"))
DISPLAY_BUS = int(os.getenv("DISPLAY_BUS", "0"))
DISPLAY_DEVICE = int(os.getenv("DISPLAY_DEVICE", "0"))
DISPLAY_FONT_STYLE = os.getenv("DISPLAY_FONT_STYLE", "sans")  # "sans" (Arial/LiberationSans) or "serif" (Times/Tinos)

# Display active timer
DISPLAY_ACTIVE_START = int(os.getenv("DISPLAY_ACTIVE_START", "8"))  # 08:00
DISPLAY_ACTIVE_END = int(os.getenv("DISPLAY_ACTIVE_END", "20"))    # 20:00

# Telegram notification settings
TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

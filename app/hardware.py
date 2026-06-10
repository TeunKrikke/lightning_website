import logging
import time
from PIL import Image

logger = logging.getLogger("app.hardware")

# Detection flags
IS_MOCK_AS3935 = False
IS_MOCK_LCD = False

# Import AS3935 sensor driver
try:
    from as3935_lib.DFRobot_AS3935_Lib import DFRobot_AS3935
    import smbus2 as smbus
except ImportError:
    logger.warning("Could not load physical AS3935 libraries. Falling back to Mock AS3935.")
    IS_MOCK_AS3935 = True

# Import Waveshare LCD driver
try:
    from waveshare_lib import LCD_1inch14
except ImportError:
    logger.warning("Could not load physical Waveshare LCD libraries. Falling back to Mock Waveshare LCD.")
    IS_MOCK_LCD = True

# Import RPi.GPIO
try:
    import RPi.GPIO as GPIO
except ImportError:
    logger.warning("Could not load RPi.GPIO. Falling back to Mock GPIO.")
    GPIO = None

# Mock AS3935 Sensor implementation
class MockAS3935Sensor:
    def __init__(self, address=0x03, bus=1):
        self.address = address
        self.bus = bus
        self.capacitance = 96
        self.indoors = True
        self.disturber_enabled = True
        self.noise_floor = 2
        self.watchdog = 2
        self.spike_rejection = 2
        self._mock_interrupt_src = 0
        self._mock_distance = 0
        self._mock_intensity = 0

    def reset(self):
        logger.info("Mock AS3935: Resetting sensor.")
        return 1

    def manual_cal(self, capacitance, mode, disturber):
        self.capacitance = capacitance
        self.indoors = (mode == 0)
        self.disturber_enabled = (disturber == 1)
        logger.info(
            f"Mock AS3935: Calibrated. Cap={capacitance}pF, "
            f"Mode={'Indoor' if self.indoors else 'Outdoor'}, "
            f"Disturbers={'Enabled' if self.disturber_enabled else 'Disabled'}"
        )

    def set_indoors(self):
        self.indoors = True
        logger.info("Mock AS3935: Set mode to indoor.")

    def set_outdoors(self):
        self.indoors = False
        logger.info("Mock AS3935: Set mode to outdoor.")

    def disturber_en(self):
        self.disturber_enabled = True
        logger.info("Mock AS3935: Enabled disturber detection.")

    def disturber_dis(self):
        self.disturber_enabled = False
        logger.info("Mock AS3935: Disabled disturber detection.")

    def get_interrupt_src(self):
        src = self._mock_interrupt_src
        self._mock_interrupt_src = 0  # clear after reading
        return src

    def get_lightning_distKm(self):
        return self._mock_distance

    def get_strike_energy_raw(self):
        return self._mock_intensity

    def get_noise_floor_lv1(self):
        return self.noise_floor

    def set_noise_floor_lv1(self, nf):
        self.noise_floor = nf
        logger.info(f"Mock AS3935: Set noise floor to {nf}.")

    def get_watchdog_threshold(self):
        return self.watchdog

    def set_watchdog_threshold(self, wd):
        self.watchdog = wd
        logger.info(f"Mock AS3935: Set watchdog threshold to {wd}.")

    def get_spike_rejection(self):
        return self.spike_rejection

    def set_spike_rejection(self, sr):
        self.spike_rejection = sr
        logger.info(f"Mock AS3935: Set spike rejection to {sr}.")

    def simulate_strike_event(self, distance: int, intensity: int):
        self._mock_interrupt_src = 1
        self._mock_distance = distance
        self._mock_intensity = intensity

    def simulate_disturber_event(self):
        self._mock_interrupt_src = 2

    def simulate_noise_event(self):
        self._mock_interrupt_src = 3


# Mock Waveshare LCD Display implementation
class MockWaveshareDisplay:
    width = 240
    height = 135

    def __init__(self):
        self.backlight = 0
        logger.info("Mock Waveshare LCD: Created display instance.")

    def Init(self):
        logger.info("Mock Waveshare LCD: Initialized display.")

    def clear(self):
        logger.info("Mock Waveshare LCD: Cleared display screen.")

    def bl_DutyCycle(self, duty):
        self.backlight = duty
        logger.info(f"Mock Waveshare LCD: Set backlight duty cycle to {duty}%.")

    def ShowImage(self, image):
        logger.info(
            f"Mock Waveshare LCD: Showing PIL image with size {image.size} "
            f"(backlight={self.backlight}%)."
        )

    def module_exit(self):
        logger.info("Mock Waveshare LCD: Exited display module.")


# Unified Hardware Interface Classes
class AS3935SensorWrapper:
    def __init__(self, address=0x03, bus=1):
        if IS_MOCK_AS3935:
            self._sensor = MockAS3935Sensor(address, bus)
        else:
            try:
                self._sensor = DFRobot_AS3935(address, bus)
            except Exception as e:
                logger.error(f"Failed to initialize physical AS3935: {e}. Falling back to mock.")
                self._sensor = MockAS3935Sensor(address, bus)

    def __getattr__(self, name):
        # Forward calls to the underlying physical/mock sensor
        return getattr(self._sensor, name)


class WaveshareDisplayWrapper:
    def __init__(self):
        if IS_MOCK_LCD:
            self._display = MockWaveshareDisplay()
        else:
            try:
                self._display = LCD_1inch14.LCD_1inch14()
            except Exception as e:
                logger.error(f"Failed to initialize physical Waveshare LCD: {e}. Falling back to mock.")
                self._display = MockWaveshareDisplay()

    def __getattr__(self, name):
        # Forward calls to the underlying physical/mock display
        return getattr(self._display, name)


# Interrupt Handling Utility
class GPIOInterruptManager:
    def __init__(self, irq_pin=7):
        self.irq_pin = irq_pin
        self.callback = None

    def setup_interrupt(self, callback):
        self.callback = callback
        if GPIO is not None:
            try:
                GPIO.setmode(GPIO.BOARD)
                GPIO.setup(self.irq_pin, GPIO.IN)
                GPIO.add_event_detect(self.irq_pin, GPIO.RISING, callback=self._gpio_callback)
                logger.info(f"GPIO interrupt configured on physical BOARD pin {self.irq_pin}.")
            except Exception as e:
                logger.error(f"Failed to setup physical GPIO interrupt: {e}. Running in simulation only.")
        else:
            logger.info(f"Mock GPIO interrupt initialized on pin {self.irq_pin}.")

    def _gpio_callback(self, channel):
        if self.callback:
            self.callback(channel)

    def trigger_mock_interrupt(self):
        """Simulate hardware interrupt call for testing on PC"""
        logger.info("Simulating GPIO interrupt rising edge.")
        if self.callback:
            # Pass pin number as channel
            self.callback(self.irq_pin)

    def cleanup(self):
        if GPIO is not None:
            try:
                GPIO.cleanup(self.irq_pin)
                logger.info("Cleaned up GPIO interrupt pin.")
            except Exception as e:
                logger.error(f"Failed to cleanup GPIO: {e}")

from app.config import I2C_ADDR, I2C_BUS, IRQ_PIN

sensor_hardware = AS3935SensorWrapper(address=I2C_ADDR, bus=I2C_BUS)
gpio_manager = GPIOInterruptManager(irq_pin=IRQ_PIN)


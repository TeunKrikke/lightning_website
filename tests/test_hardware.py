import pytest
from app.hardware import (
    MockAS3935Sensor, MockWaveshareDisplay, GPIOInterruptManager,
    AS3935SensorWrapper, WaveshareDisplayWrapper
)

def test_mock_sensor_calibration():
    sensor = MockAS3935Sensor()
    sensor.manual_cal(capacitance=80, location=1, disturber=0)
    
    assert sensor.capacitance == 80
    assert not sensor.indoors  # location=1 means outdoors
    assert not sensor.disturber_enabled  # disturber=0 means disabled

def test_mock_sensor_thresholds():
    sensor = MockAS3935Sensor()
    sensor.set_noise_floor_lv1(5)
    sensor.set_watchdog_threshold(4)
    sensor.set_spike_rejection(3)

    assert sensor.get_noise_floor_lv1() == 5
    assert sensor.get_watchdog_threshold() == 4
    assert sensor.get_spike_rejection() == 3

def test_mock_sensor_event_simulation():
    sensor = MockAS3935Sensor()
    sensor.simulate_strike_event(distance=15, intensity=800)
    
    assert sensor.get_interrupt_src() == 1
    assert sensor.get_lightning_distKm() == 15
    assert sensor.get_strike_energy_raw() == 800

    # Test disturber simulation
    sensor.simulate_disturber_event()
    assert sensor.get_interrupt_src() == 2

    # Test noise simulation
    sensor.simulate_noise_event()
    assert sensor.get_interrupt_src() == 3

def test_mock_lcd_display():
    lcd = MockWaveshareDisplay()
    lcd.bl_DutyCycle(80)
    assert lcd.backlight == 80

def test_gpio_interrupt_manager():
    called = False
    received_channel = None

    def dummy_callback(channel):
        nonlocal called, received_channel
        called = True
        received_channel = channel

    manager = GPIOInterruptManager(irq_pin=12)
    manager.setup_interrupt(dummy_callback)
    
    # Trigger mock interrupt
    manager.trigger_mock_interrupt()

    assert called
    assert received_channel == 12

    # Test direct _gpio_callback call (as gpiozero would trigger)
    called = False
    manager._gpio_callback()
    assert called

    # Test cleanup
    manager.cleanup()
    assert manager.device is None

def test_wrappers_instantiation():
    # Verify that the wrapper classes forward calls and initialize without errors
    sensor = AS3935SensorWrapper()
    assert hasattr(sensor, "reset")
    assert hasattr(sensor, "manual_cal")

    lcd = WaveshareDisplayWrapper()
    assert hasattr(lcd, "bl_DutyCycle")
    assert hasattr(lcd, "ShowImage")

import os
import sys
import time
from evdev import InputDevice, ecodes
from adafruit_motorkit import MotorKit

try:
    kit = MotorKit()
    motor_left = kit.motor1
    motor_right = kit.motor2
except Exception as e:
    print(f"HAT Error: Ensure I2C is enabled! {e}")
    sys.exit(1)

device_path = None
for dev in [os.path.join('/dev/input', f) for f in os.listdir('/dev/input') if f.startswith('event')]:
    try:
        device = InputDevice(dev)
        name_lower = device.name.lower()
        if '8bitdo' in name_lower or 'pro' in name_lower or 'xbox' in name_lower or 'gamepad' in name_lower:
            device_path = dev
            break
    except:
        continue

if not device_path:
    print("Error: No compatible controller found.")
    sys.exit(1)

gamepad = InputDevice(device_path)
print(f"SUCCESS: Event Loop Engaged -> {gamepad.name}")

# Initialize baseline joystick coordinates (centered)
left_stick_y = 0
right_stick_y = 0

try:
    while True:
        # Drain the event queue completely to get the absolute newest position
        # This fixes the "stuck background event queue" issue
        try:
            for event in gamepad.read():
                if event.type == ecodes.EV_ABS:
                    if event.code == ecodes.ABS_Y:
                        left_stick_y = event.value
                    elif event.code == ecodes.ABS_RY:
                        right_stick_y = event.value
        except BlockingIOError:
            # No new events in the buffer, which is fine
            pass

        # --- CLEAN 16-BIT CONVERSION MATH ---
        left_speed = -(left_stick_y / 32767.0)
        right_speed = -(right_stick_y / 32767.0)

        # Deadzone filter
        if abs(left_speed) < 0.15:
            left_speed = 0.0
        if abs(right_speed) < 0.15:
            right_speed = 0.0

        # Send speeds to Adafruit MotorKit
        motor_left.throttle = max(min(left_speed, 1.0), -1.0)
        motor_right.throttle = max(min(right_speed, 1.0), -1.0)

        # 60Hz Loop Timing
        time.sleep(0.016)

except KeyboardInterrupt:
    print("\nShutting down motors...")
finally:
    motor_left.throttle = 0.0
    motor_right.throttle = 0.0

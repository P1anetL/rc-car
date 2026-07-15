import os
import sys
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
        if "8bitdo" in name_lower or "pro" in name_lower or "xbox" in name_lower or "gamepad" in name_lower:
            device_path = dev
            break
    except:
        continue

if not device_path:
    print("Error: No compatible controller found.")
    sys.exit(1)

gamepad = InputDevice(device_path)
print(f"SUCCESS: Calibrated 16-Bit Logic Engaged -> {gamepad.name}")

# Establish baseline resting values from your evtest feedback
# Rest = -32768, Full Forward = 32767
left_stick_y = -32768
right_stick_y = -32768

try:
    for event in gamepad.read_loop():
        if event.type == ecodes.EV_ABS:
            if event.code == ecodes.ABS_Y:
                left_stick_y = event.value
            elif event.code == ecodes.ABS_RY:
                right_stick_y = event.value
            
            # --- SHIFTED BASEPOINT MATH ---
            # 1. Normalize the coordinate value so that the resting spot (-32768) shifts to 0.0
            # 2. This maps the total mechanical stroke range (from -32768 up to 32767) cleanly.
            left_speed = (left_stick_y + 32768) / 32767.0
            right_speed = (right_stick_y + 32768) / 32767.0
            
            # Clamp limits to allow a slight reverse cushion if the stick drops below baseline
            # (Allows smooth decimal scaling from 0.0 stopped up to 1.0 full speed)
            left_speed = left_speed if abs(left_speed) > 0.12 else 0.0
            right_speed = right_speed if abs(right_speed) > 0.12 else 0.0
            
            # Send speeds safely to your physical motors (M1 and M2)
            motor_left.throttle = max(min(left_speed, 1.0), -1.0)
            motor_right.throttle = max(min(right_speed, 1.0), -1.0)

except KeyboardInterrupt:
    print("\nShutting down motors...")
finally:
    motor_left.throttle = 0.0
    motor_right.throttle = 0.0

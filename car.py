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
    print(f"HAT Error: Ensure I2C is enabled in sudo raspi-config! {e}")
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
    print("Error: No compatible controller found in system files.")
    sys.exit(1)

gamepad = InputDevice(device_path)
print(f"SUCCESS: Tracking Controller -> {gamepad.name}")
print("CALIBRATING JOYSTICKS... PLEASE DO NOT TOUCH THE STICKS FOR 2 SECONDS.")

# Read the current resting physical state of the joysticks to set the true center points
time.sleep(1.0)
left_center = 127
right_center = 127

# Fetch current device state values safely
state = gamepad.active_keys()
try:
    abs_info_y = gamepad.absinfo(ecodes.ABS_Y)
    abs_info_ry = gamepad.absinfo(ecodes.ABS_RY)
    if abs_info_y: left_center = abs_info_y.value
    if abs_info_ry: right_center = abs_info_ry.value
except Exception:
    pass

print(f"Calibrated successfully! Left Center: {left_center}, Right Center: {right_center}")

left_stick_y = left_center
right_stick_y = right_center

try:
    for event in gamepad.read_loop():
        if event.type == ecodes.EV_ABS:
            if event.code == ecodes.ABS_Y:
                left_stick_y = event.value
            elif event.code == ecodes.ABS_RY:
                right_stick_y = event.value
            
            # --- AUTO-CALIBRATED STEERING MATH ---
            # Calculate speed based on deviation from the calibrated center points
            if left_stick_y <= left_center:
                left_speed = (left_center - left_stick_y) / float(left_center) if left_center > 0 else 0
            else:
                left_speed = -(left_stick_y - left_center) / float(255 - left_center) if left_center < 255 else 0

            if right_stick_y <= right_center:
                right_speed = (right_center - right_stick_y) / float(right_center) if right_center > 0 else 0
            else:
                right_speed = -(right_stick_y - right_center) / float(255 - right_center) if right_center < 255 else 0
            
            # Increased deadzone filter from 0.15 to 0.20 to completely kill resting drift humming
            if abs(left_speed) < 0.20: left_speed = 0.0
            if abs(right_speed) < 0.20: right_speed = 0.0
            
            motor_left.throttle = max(min(left_speed, 1.0), -1.0)
            motor_right.throttle = max(min(right_speed, 1.0), -1.0)

except KeyboardInterrupt:
    print("\nShutting down motors...")
finally:
    motor_left.throttle = 0.0
    motor_right.throttle = 0.0

import os
import sys
from evdev import InputDevice, ecodes
from adafruit_motorkit import MotorKit

try:
    kit = MotorKit()
    motor_left = kit.motor1
    motor_right = kit.motor2
except Exception as e:
    print(f"HAT Error: Ensure I2C is enabled in sudo raspi-config! {e}")
    sys.exit(1)

# Look for ANY connected controller device files
device_path = None
print("\n--- Scanning connected hardware devices ---")
for dev in [os.path.join('/dev/input', f) for f in os.listdir('/dev/input') if f.startswith('event')]:
    try:
        device = InputDevice(dev)
        print(f"Found input device: '{device.name}' at path: {dev}")
        
        # Broadened search to catch any variation of 8BitDo, Pro, or Xbox Controller profiles
        name_lower = device.name.lower()
        if "8bitdo" in name_lower or "pro" in name_lower or "xbox" in name_lower or "gamepad" in name_lower:
            device_path = dev
            break
    except:
        continue
print("-------------------------------------------\n")

if not device_path:
    print("Error: No compatible controller found in system files.")
    print("Please check the device list printed above to see what your Pi calls it!")
    sys.exit(1)

gamepad = InputDevice(device_path)
print(f"SUCCESS: Tracking Controller -> {gamepad.name}")

left_stick_y = 127
right_stick_y = 127

try:
    for event in gamepad.read_loop():
        if event.type == ecodes.EV_ABS:
            if event.code == ecodes.ABS_Y:
                left_stick_y = event.value
            elif event.code == ecodes.ABS_RY:
                right_stick_y = event.value
            
            left_speed = ((127 - left_stick_y) / 127.0)
            right_speed = ((127 - right_stick_y) / 127.0)
            
            if abs(left_speed) < 0.15: left_speed = 0.0
            if abs(right_speed) < 0.15: right_speed = 0.0
            
            motor_left.throttle = max(min(left_speed, 1.0), -1.0)
            motor_right.throttle = max(min(right_speed, 1.0), -1.0)

except KeyboardInterrupt:
    print("\nShutting down motors...")
finally:
    motor_left.throttle = 0.0
    motor_right.throttle = 0.0

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


device_path = None
for dev in [os.path.join('/dev/input', f) for f in os.listdir('/dev/input') if f.startswith('event')]:
    try:
        device = InputDevice(dev)
        if "8BitDo" in device.name or "Pro Controller" in device.name:
            device_path = dev
            break
    except:
        continue

if not device_path:
    print("Error: 8BitDo controller not found. Is it connected via Bluetooth?")
    sys.exit(1)

gamepad = InputDevice(device_path)
print(f"Tracking Controller: {gamepad.name}")


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

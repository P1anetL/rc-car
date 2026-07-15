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
print(f"SUCCESS: Linear Throttle Active on -> {gamepad.name}")

# Track the continuous tracking states of BOTH sticks at once
left_stick_y = 0.0
right_stick_y = 0.0

try:
    for event in gamepad.read_loop():
        if event.type == ecodes.EV_ABS:
            # 1. Instantly log the raw 16-bit integer state (-32768 to 32767)
            if event.code == ecodes.ABS_Y:
                # Convert immediately to a raw decimal percentage (-1.0 to 1.0)
                # Inverted with a minus sign so Up = Positive, Down = Negative
                left_stick_y = -(event.value / 32767.0)
            elif event.code == ecodes.ABS_RY:
                right_stick_y = -(event.value / 32767.0)
            
            # 2. Linear Deadzone Smoothing
            # Instead of snapping to 0 or 1.0, we gently zero out tiny values
            # but preserve every single fractional step in between for true throttle scaling.
            left_speed = left_stick_y if abs(left_stick_y) > 0.12 else 0.0
            right_speed = right_stick_y if abs(right_stick_y) > 0.12 else 0.0
            
            # 3. Apply the hardware execution commands directly to the Adafruit HAT
            # The throttle changes incrementally matching how far you push the plastic stick
            motor_left.throttle = max(min(left_speed, 1.0), -1.0)
            motor_right.throttle = max(min(right_speed, 1.0), -1.0)

except KeyboardInterrupt:
    print("\nShutting down motors...")
finally:
    motor_left.throttle = 0.0
    motor_right.throttle = 0.0

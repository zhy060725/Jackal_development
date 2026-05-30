class KeyboardControlState(object):
    def __init__(self, direction="stop", speed=0.0, speed_step=0.1, default_speed=0.3):
        self.direction = direction
        self.speed = float(speed)
        self.speed_step = float(speed_step)
        self.default_speed = float(default_speed)

    def copy(self, direction=None, speed=None):
        return KeyboardControlState(
            direction=self.direction if direction is None else direction,
            speed=self.speed if speed is None else speed,
            speed_step=self.speed_step,
            default_speed=self.default_speed,
        )


def clamp_speed(speed):
    return min(max(float(speed), 0.0), 1.0)


def apply_key(state, key):
    if key == 'w':
        return _with_direction(state, "forward")
    if key == 's':
        return _with_direction(state, "backward")
    if key == 'a':
        return _with_direction(state, "left")
    if key == 'd':
        return _with_direction(state, "right")
    if key == " ":
        return state.copy(direction="stop", speed=0.0)
    if key in ("+", "="):
        return state.copy(speed=clamp_speed(state.speed + state.speed_step))
    if key in ("-", "_"):
        return state.copy(speed=clamp_speed(state.speed - state.speed_step))
    return state


def _with_direction(state, direction):
    speed = state.speed if state.speed > 0.0 else state.default_speed
    return state.copy(direction=direction, speed=clamp_speed(speed))

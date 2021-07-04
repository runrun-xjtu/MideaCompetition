import time

class PID:
    def __init__(self, P, I, D):
        self.Kp = P
        self.Ki = I
        self.Kd = D
        self.sample_time = 0.00
        self.clear()

    def clear(self):
        self.SetPoint = 0.0
        self.PTerm = 0.0
        self.ITerm = 0.0
        self.DTerm = 0.0
        self.last_error = 0.0
        self.int_error = 0.0
        self.windup_guard = 20.0
        self.output = 0.0
        self.delta_time = 0.0

    def update(self, feedback_value):
        error = self.SetPoint - feedback_value
        delta_error = error - self.last_error
        self.PTerm = error  # 比例
        self.ITerm += error * self.delta_time  # 积分
        if (self.ITerm < -self.windup_guard):
            self.ITerm = -self.windup_guard
        elif (self.ITerm > self.windup_guard):
            self.ITerm = self.windup_guard
        self.DTerm = 0.0
        self.DTerm = delta_error / self.delta_time
        self.last_error = error
        self.output = self.Kp * self.PTerm + (self.Ki * self.ITerm) + (self.Kd * self.DTerm)

    def setKp(self, proportional_gain):
        self.Kp = proportional_gain

    def setKi(self, integral_gain):
        self.Ki = integral_gain

    def setKd(self, derivative_gain):
        self.Kd = derivative_gain

    def setWindup(self, windup):
        self.windup_guard = windup

    def setSampleTime(self, sample_time):
        self.sample_time = sample_time

    def setdelta_time(self, delta_time):
        self.delta_time = delta_time
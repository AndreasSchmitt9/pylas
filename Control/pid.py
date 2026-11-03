import math, time
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_HEADER = "t,lwc,lwc_target,error,p,i,d,lastoutput,output\n"

def Base_concentration_linear(desired_lwc):
    #LWC: 0.5 g/m^3→ 250000, LWC 0.01 g/m^3 → 35000 
    return 30000+500000*desired_lwc

def Base_concentration_nonlinear(desired_lwc, DeltaT):
    return 100000

class PID:
    def __init__(self):
        # Parameters (overwritten from settings.toml by load_params; these are fallbacks)
        self.kp = 1.0
        self.ki = 0.1
        self.kd = 0.0
        self.lwc_target = 1e-5
        self.gain = 50000
        self.dt = 1.0
        self.min_conc = 0.0
        self.max_conc = 1.0e8

        self.integral = 0.0
        self.last_error = None
        self.last_output = 0.0

        self.t0 = time.time()
        self.lwc_0 = 0.0
        self.amplitude = 0.0
        self.lwc_omega = 0.0

        LOG_DIR.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_path = LOG_DIR / f"control_{stamp}.csv"
        with open(self.log_path, "w") as f:
            f.write(LOG_HEADER)

    def update(self, lwc):
        """Takes the measured LWC [g/m^3], returns the control signal."""
        if math.isnan(lwc):               # no valid measurement: hold last output
            return self.last_output
        if (self.amplitude !=0.0):
            self.lwc_target = self.live_setpoint()

        error = self.lwc_target - lwc          # > 0: too little water -> increase
        #print(lwc)
        self.integral += error * self.dt
        derivative = 0.0 if self.last_error is None else (error - self.last_error) / self.dt
        self.last_error = error

        p=self.kp * error
        i=self.ki * self.integral
        d=self.kd * derivative
        self.last_output = p + i + d

        self._log(lwc,error,p,i,d)
        return self.last_output

    def live_setpoint(self):
        return self.lwc_0 + self.amplitude * math.cos(self.lwc_omega * (time.time()-self.t0))

    def output(self):
        setpoint = Base_concentration_linear(self.lwc_target) + self.gain * self.last_output
        #print(f"Feedforward setpoint: {setpoint:.2f} for desired LWC: {self.lwc_target:.4f} g/m^3")
        return min(max(setpoint, self.min_conc), self.max_conc)

    def _log(self, lwc, error, p, i, d):
        line = f"{time.time():.3f},{lwc},{self.lwc_target},{error},{p},{i},{d},{self.last_output},{self.output()}\n"
        with open(self.log_path, "a") as f:
            f.write(line)



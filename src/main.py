#!/usr/bin/env python3
import threading
import time
import random
from Aloha.src.utils.budget_utls import cpu_load,memory_load

# ============================================================
#  Base Module Class
# ============================================================

class BaseModule(threading.Thread):
    def __init__(self, name, interval=1.0):
        super().__init__(daemon=True)
        self.name = name
        self.interval = interval
        self.running = False
        self.last_output = None

    def run(self):
        self.running = True
        print(f"[{self.name}] started")

        while self.running:
            start = time.time()

            # Simulate CPU + memory usage
            cpu_load(30)
            memory_load(64)

            # Module-specific work
            self.last_output = self.step()

            # Maintain interval
            elapsed = time.time() - start
            sleep_time = max(0.0, self.interval - elapsed)
            time.sleep(sleep_time)

        print(f"[{self.name}] stopped")

    def stop(self):
        self.running = False

    def step(self):
        """Override in subclass."""
        return None


# ============================================================
#  ADS-B Module (RTL-SDR v4)
# ============================================================

class AdsbModule(BaseModule):
    def step(self):
        # Dummy ADS-B message
        msg = {
            "icao": hex(random.randint(0x100000, 0xFFFFFF)),
            "altitude_m": random.uniform(1000, 12000),
            "lat": random.uniform(-90, 90),
            "lon": random.uniform(-180, 180),
            "timestamp": time.time()
        }
        print(f"[adsb] {msg}")
        return msg


# ============================================================
#  Satellite Tracking Module (NEO-M8T)
# ============================================================

class SatelliteModule(BaseModule):
    def step(self):
        # Dummy GNSS satellite info
        sat_count = random.randint(5, 14)
        sats = [
            {
                "prn": f"G{random.randint(1, 32)}",
                "az": random.uniform(0, 360),
                "el": random.uniform(0, 90),
                "snr": random.uniform(20, 50)
            }
            for _ in range(sat_count)
        ]
        print(f"[satellite] sats={sat_count}")
        return sats


# ============================================================
#  Timing Module (NEO-M8T PPS)
# ============================================================

class TimingModule(BaseModule):
    def step(self):
        # Dummy PPS timing
        msg = {
            "pps_count": int(time.time()),
            "gnss_time": time.time(),
            "mono_time": time.monotonic(),
            "offset_ns": random.randint(-50000, 50000),
            "locked": random.choice([True, True, False])
        }
        print(f"[timing] {msg}")
        return msg


# ============================================================
#  Astral Catalogue Module
# ============================================================

class AstralCatalogueModule(BaseModule):
    def step(self):
        # Dummy star entry
        entry = {
            "name": random.choice(["Vega", "Betelgeuse", "Sirius", "Rigel"]),
            "ra": random.uniform(0, 360),
            "dec": random.uniform(-90, 90),
            "mag": random.uniform(-1, 6)
        }
        print(f"[astral] {entry}")
        return entry


# ============================================================
#  Aircraft Catalogue Module
# ============================================================

class AircraftCatalogueModule(BaseModule):
    def step(self):
        entry = {
            "icao": hex(random.randint(0x100000, 0xFFFFFF)),
            "model": random.choice(["A320", "B737", "C172", "A350"]),
            "operator": random.choice(["BAW", "RYR", "EZY", "DLH"])
        }
        print(f"[aircraft] {entry}")
        return entry


# ============================================================
#  Orchestrator
# ============================================================

class Orchestrator:
    def __init__(self):
        self.modules = []

        # Instantiate modules
        self.modules.append(AdsbModule("adsb", interval=1.0))
        self.modules.append(SatelliteModule("satellite", interval=1.0))
        self.modules.append(TimingModule("timing", interval=0.5))
        self.modules.append(AstralCatalogueModule("astral", interval=5.0))
        self.modules.append(AircraftCatalogueModule("aircraft", interval=10.0))

    def start(self):
        print("[orchestrator] starting modules")
        for m in self.modules:
            m.start()

    def stop(self):
        print("[orchestrator] stopping modules")
        for m in self.modules:
            m.stop()

        for m in self.modules:
            m.join()

    def run(self):
        self.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[orchestrator] shutdown requested")
            self.stop()


# ============================================================
#  Main
# ============================================================

if __name__ == "__main__":
    orch = Orchestrator()
    orch.run()

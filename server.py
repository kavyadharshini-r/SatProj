import json
import time
import math
import numpy as np
import tornado.ioloop
import tornado.web
import tornado.websocket
from rtlsdr import RtlSdr

# --- CONFIGURATION ---
SATELLITE_FREQ = 137.1e6  # Example: NOAA-19 Weather Satellite (137.1 MHz)
PORT = 8082

# Initialize SDR
try:
    print("[*] Initializing NooElec SDR for Satellite Tracking...")
    sdr = RtlSdr()
    sdr.sample_rate = 1_024_000
    sdr.center_freq = SATELLITE_FREQ
    sdr.gain = 'auto'
except Exception as e:
    print(f"[!] SDR Hardware not found, running in SIMULATED mode. Error: {e}")
    sdr = None

# Connected WebSocket Clients
clients = set()

class TelemetryWebSocket(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True  # Allow Open MCT to connect from any local address

    def open(self):
        clients.add(self)
        print(f"[+] Open MCT client connected. Active clients: {len(clients)}")

    def on_close(self):
        clients.remove(self)
        print(f"[-] Client disconnected. Active clients: {len(clients)}")

def capture_satellite_telemetry():
    """Reads SDR data, extracts RSSI, and builds satellite telemetry packets."""
    global sdr
    
    # 1. Read actual signal from the NooElec
    if sdr:
        try:
            samples = sdr.read_samples(256 * 1024)
            # Calculate Received Signal Strength Indicator (RSSI) in dB
            power = np.mean(np.abs(samples)**2)
            rssi = 10 * math.log10(power + 1e-10)
        except Exception:
            rssi = -90.0  # Default noise floor if read fails
    else:
        # Fallback simulator if NooElec is unplugged
        rssi = -50.0 + (math.sin(time.time() / 10.0) * 15.0)

    # 2. Simulate Satellite housekeeping telemetry
    timestamp = int(time.time() * 1000)
    elapsed = time.time()
    
    telemetry_packet = {
        "timestamp": timestamp,
        "rssi": round(rssi, 2),                               # Signal strength
        "battery_voltage": round(3.7 + 0.5 * math.sin(elapsed / 100), 2), # Volts
        "panel_temp": round(25.0 + 5.0 * math.cos(elapsed / 50), 1),    # Celsius
        "altitude": round(850 + 10 * math.sin(elapsed / 300), 2)         # km (LEO Orbit)
    }

    # Broadcast to Open MCT via WebSocket
    for client in list(clients):
        try:
            client.write_message(json.dumps(telemetry_packet))
        except Exception:
            clients.remove(client)

def make_app():
    return tornado.web.Application([
        (r"/telemetry", TelemetryWebSocket),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(PORT)
    print(f"[*] Telemetry server listening on ws://localhost:{PORT}/telemetry")
    
    # Run the loop to collect SDR samples and stream every 100ms (10 times a second)
    periodic_cb = tornado.ioloop.PeriodicCallback(capture_satellite_telemetry, 100)
    periodic_cb.start()
    tornado.ioloop.IOLoop.current().start()

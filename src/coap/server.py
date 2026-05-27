"""
Module 1 Assignment — Task 2.1
CoAP Sensor Resource Server

Complete all TODO sections. The resource classes must match the
URIs and behaviours listed in the assignment spec.

Run with:  python -m src.coap.server
"""

import asyncio
import json
import logging
import random
from datetime import datetime, timezone

import aiocoap
import aiocoap.resource as resource
from aiocoap import Code, Message

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
log = logging.getLogger(__name__)

# ── Sensor simulation helpers ─────────────────────────────────────────────────

SENSOR_CONFIG = {
    "temperature": {"unit": "C",    "base": 70.0, "noise": 3.0},
    "vibration":   {"unit": "mm/s", "base": 1.2,  "noise": 0.3},
    "power":       {"unit": "kW",   "base": 45.0, "noise": 5.0},
}

def _sim(sensor: str) -> dict:
    cfg = SENSOR_CONFIG[sensor]
    return {
        "value": round(cfg["base"] + random.gauss(0, cfg["noise"]), 3),
        "unit":  cfg["unit"],
        "ts":    datetime.now(timezone.utc).isoformat(),
    }

def _json(data: dict) -> bytes:
    return json.dumps(data).encode()


# ── Observable Sensor Resource ────────────────────────────────────────────────

class SensorResource(resource.ObservableResource):
    """
    An observable CoAP resource that represents a single sensor on a line.

    TODO 1: Implement this class.
    Requirements:
      - Accept line and sensor_type in __init__
      - Store the current reading (initially simulated)
      - Start an asyncio background task (_update_loop) that:
          * Simulates a new reading every 5 seconds
          * Calls self.updated_state() to notify observers
      - Implement render_get:
          * Return a 2.05 Content response
          * Content-Format: 50 (application/json)
          * Payload: JSON-encoded current reading
    """

    def __init__(self, line: str, sensor_type: str):
        super().__init__()
        self.line        = line
        self.sensor_type = sensor_type
        self._reading    = _sim(sensor_type)
        asyncio.ensure_future(self._update_loop())

    async def _update_loop(self) -> None:
        """
        TODO 2: Every 5 seconds, simulate a new reading and notify observers.
        """
        while True:
            await asyncio.sleep(5)
            self._reading = _sim(self.sensor_type)
            self.updated_state()

    async def render_get(self, request: Message) -> Message:
        """
        TODO 3: Return the current sensor reading as a JSON response.
        Hint: use aiocoap.numbers.contentformat.ContentFormat.JSON (value 50)
              or pass content_format=50 to Message(...)
        """
        return Message(payload=_json(self._reading), content_format=50)


# ── Actuator Resource ─────────────────────────────────────────────────────────

class ActuatorResource(resource.Resource):
    """
    A CoAP resource representing a controllable fan actuator.

    TODO 4: Implement this class.
    Requirements:
      - Track state: "OFF" initially
      - render_get: return current state as JSON {"state": "ON"|"OFF"}
      - render_put: accept {"state": "ON"} or {"state": "OFF"}
          * Update internal state
          * Return 2.04 Changed on success
          * Return 4.00 Bad Request if payload is malformed or state is invalid
    """

    def __init__(self):
        super().__init__()
        self._state = "OFF"

    async def render_get(self, request: Message) -> Message:
        """TODO 5: Return current fan state as JSON."""
        return Message(payload=_json({"state": self._state}), content_format=50)

    async def render_put(self, request: Message) -> Message:
        """TODO 6: Accept ON/OFF command and update state."""
        try:
            payload_str = request.payload.decode('utf-8')
            data = json.loads(payload_str)
            if "state" in data and data["state"] in ["ON", "OFF"]:
                self._state = data["state"]
                return Message(code=Code.CHANGED)
            else:
                return Message(code=Code.BAD_REQUEST)
        except Exception:
            return Message(code=Code.BAD_REQUEST)


# ── Block-wise Manifest Resource ──────────────────────────────────────────────

class ManifestResource(resource.Resource):
    """
    A large resource that triggers CoAP Block2 transfer.

    TODO 7: Implement this class.
    Requirements:
      - render_get must return a payload of AT LEAST 3072 bytes (3 KB)
      - Content-Format: 50 (application/json)
      - The payload should be a realistic-looking firmware manifest
        (list of sensor firmware versions, checksums, update URLs, etc.)
      - aiocoap handles Block2 fragmentation automatically if the payload
        exceeds the negotiated block size — you just need to return the full payload
    """

    async def render_get(self, request: Message) -> Message:
        """TODO 8: Return a >= 3 KB JSON firmware manifest."""
        manifest = {
            "firmwares": [
                {
                    "sensor_id": f"sensor_{i}",
                    "version": "1.0.0",
                    "checksum": "d41d8cd98f00b204e9800998ecf8427e",
                    "url": f"http://update.server/firmware_{i}.bin"
                }
                for i in range(100)
            ]
        }
        return Message(payload=_json(manifest), content_format=50)


# ── Resource Tree & Server Setup ──────────────────────────────────────────────

async def build_server() -> aiocoap.Context:
    """
    TODO 9: Build the CoAP resource tree and create the server context.

    Register resources at these paths (use colon-separated path segments):
      factory/line1/temperature  → SensorResource("line1", "temperature")
      factory/line1/vibration    → SensorResource("line1", "vibration")
      factory/line1/power        → SensorResource("line1", "power")
      factory/line2/temperature  → SensorResource("line2", "temperature")
      actuator/line1/fan         → ActuatorResource()
      factory/manifest           → ManifestResource()

    Also add a /.well-known/core resource listing using resource.WKCResource.

    Return the created aiocoap.Context.
    """
    root = resource.Site()

    root.add_resource(['factory', 'line1', 'temperature'], SensorResource('line1', 'temperature'))
    root.add_resource(['factory', 'line1', 'vibration'], SensorResource('line1', 'vibration'))
    root.add_resource(['factory', 'line1', 'power'], SensorResource('line1', 'power'))
    root.add_resource(['factory', 'line2', 'temperature'], SensorResource('line2', 'temperature'))
    root.add_resource(['actuator', 'line1', 'fan'], ActuatorResource())
    root.add_resource(['factory', 'manifest'], ManifestResource())

    root.add_resource(['.well-known', 'core'],
                      resource.WKCResource(root.get_resources_as_linkheader))

    context = await aiocoap.Context.create_server_context(root, bind=('127.0.0.1', 5683))
    return context


async def main() -> None:
    context = await build_server()
    log.info("CoAP server running on coap://localhost:5683")
    log.info("Resources: /factory/line{1,2}/{temperature,vibration,power}, /actuator/line1/fan, /factory/manifest")
    await asyncio.get_event_loop().create_future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())

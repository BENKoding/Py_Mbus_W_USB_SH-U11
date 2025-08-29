from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

import serial
from serial import Serial
from serial.tools import list_ports


logger = logging.getLogger(__name__)


@dataclass
class SerialParams:
    port: str
    baudrate: int = 9600
    parity: str = "N"  # 'N', 'E', 'O'
    stopbits: int = 1   # 1 or 2
    bytesize: int = 8
    timeout_s: float = 0.3


PARITY_MAP = {
    "N": serial.PARITY_NONE,
    "E": serial.PARITY_EVEN,
    "O": serial.PARITY_ODD,
}

STOPBITS_MAP = {
    1: serial.STOPBITS_ONE,
    2: serial.STOPBITS_TWO,
}

BYTESIZE_MAP = {
    7: serial.SEVENBITS,
    8: serial.EIGHTBITS,
}


def list_serial_ports() -> List[dict]:
    ports = []
    for p in list_ports.comports():
        ports.append(
            {
                "device": p.device,
                "name": p.name,
                "description": p.description,
                "hwid": p.hwid,
                "vid": getattr(p, "vid", None),
                "pid": getattr(p, "pid", None),
                "manufacturer": getattr(p, "manufacturer", None),
                "serial_number": getattr(p, "serial_number", None),
                "location": getattr(p, "location", None),
            }
        )
    logger.debug("Enumerated serial ports: %s", ports)
    return ports


def open_serial(params: SerialParams) -> Serial:
    logger.info(
        "Opening serial port %s @ %d %s %dN%d",
        params.port,
        params.baudrate,
        params.parity,
        params.stopbits,
        params.bytesize,
    )
    ser = serial.Serial(
        port=params.port,
        baudrate=params.baudrate,
        parity=PARITY_MAP.get(params.parity.upper(), serial.PARITY_NONE),
        stopbits=STOPBITS_MAP.get(params.stopbits, serial.STOPBITS_ONE),
        bytesize=BYTESIZE_MAP.get(params.bytesize, serial.EIGHTBITS),
        timeout=params.timeout_s,
    )
    return ser


def test_loopback(ser: Serial, payload: bytes = b"\x55\xAA") -> bool:
    """Simple loopback test (requires TX-RX short)."""
    try:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        ser.write(payload)
        ser.flush()
        data = ser.read(len(payload))
        ok = data == payload
        logger.debug("Loopback sent=%s recv=%s ok=%s", payload.hex(), data.hex(), ok)
        return ok
    except Exception as exc:
        logger.exception("Loopback test failed: %s", exc)
        return False


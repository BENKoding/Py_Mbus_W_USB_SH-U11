from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, List, Optional

from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusIOException
import serial


logger = logging.getLogger(__name__)


@dataclass
class ModbusParams:
    method: str = "rtu"
    port: str = ""
    baudrate: int = 9600
    parity: str = "N"
    stopbits: int = 1
    bytesize: int = 8
    timeout: float = 0.3


class ModbusRTUClient:
    def __init__(self) -> None:
        self.client: Optional[ModbusSerialClient] = None
        self.last_error: Optional[str] = None

    def connect(self, p: ModbusParams) -> bool:
        self.close()
        self.last_error = None
        logger.info(
            "Connecting Modbus RTU on %s @%d %s %dN%d",
            p.port,
            p.baudrate,
            p.parity,
            p.stopbits,
            p.bytesize,
        )
        self.client = ModbusSerialClient(
            port=p.port,
            baudrate=p.baudrate,
            parity=p.parity,
            stopbits=p.stopbits,
            bytesize=p.bytesize,
            timeout=p.timeout,
        )
        try:
            ok = self.client.connect()
        except Exception as exc:  # noqa: BLE001
            self.last_error = str(exc)
            logger.error("Modbus connection exception: %s", exc)
            return False
        if not ok:
            # Try to probe detailed error via pyserial to surface OS message
            try:
                ser = serial.Serial(
                    port=p.port,
                    baudrate=p.baudrate,
                    parity=p.parity,
                    stopbits=p.stopbits,
                    bytesize=p.bytesize,
                    timeout=p.timeout,
                )
                ser.close()
            except Exception as exc:  # noqa: BLE001
                self.last_error = str(exc)
                logger.error("Failed to open serial port: %s", exc)
            else:
                self.last_error = "Failed to open Modbus serial connection (unknown reason)"
                logger.error(self.last_error)
            return False
        return True

    def close(self) -> None:
        if self.client:
            try:
                self.client.close()
            except Exception:  # noqa: BLE001
                pass
            self.client = None

    # ---- basic operations ----
    def read_holding(self, unit: int, address: int, count: int = 1) -> Optional[List[int]]:
        if not self.client:
            return None
        try:
            rr = self.client.read_holding_registers(address=address, count=count, unit=unit)
            if rr.isError():  # type: ignore[attr-defined]
                logger.debug("FC03 error @%d unit=%d: %s", address, unit, rr)
                return None
            return list(rr.registers)
        except ModbusIOException as exc:
            logger.debug("FC03 IO exception: %s", exc)
            return None

    def read_input(self, unit: int, address: int, count: int = 1) -> Optional[List[int]]:
        if not self.client:
            return None
        try:
            rr = self.client.read_input_registers(address=address, count=count, unit=unit)
            if rr.isError():  # type: ignore[attr-defined]
                logger.debug("FC04 error @%d unit=%d: %s", address, unit, rr)
                return None
            return list(rr.registers)
        except ModbusIOException as exc:
            logger.debug("FC04 IO exception: %s", exc)
            return None

    def write_single_register(self, unit: int, address: int, value: int) -> bool:
        if not self.client:
            return False
        wr = self.client.write_register(address=address, value=value, unit=unit)
        return not getattr(wr, "isError", lambda: True)()

    def write_multiple_registers(self, unit: int, address: int, values: List[int]) -> bool:
        if not self.client:
            return False
        wr = self.client.write_registers(address=address, values=values, unit=unit)
        return not getattr(wr, "isError", lambda: True)()

    # ---- scanning ----
    def scan_units(self, ids: Iterable[int], probe_addr: int = 0, probe_count: int = 1) -> List[int]:
        """Return unit IDs responding to a simple FC03 probe.

        Conservative approach: device is considered present if FC03 @probe_addr returns non-error.
        """
        present: List[int] = []
        for uid in ids:
            regs = self.read_holding(unit=uid, address=probe_addr, count=probe_count)
            if regs is not None:
                present.append(uid)
        logger.info("Scan complete; found units: %s", present)
        return present

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class Access(str, Enum):
    RO = "RO"
    RW = "RW"


class RegType(str, Enum):
    u16 = "u16"
    i16 = "i16"
    u32 = "u32"
    i32 = "i32"
    f32 = "f32"


class Endianness(str, Enum):
    be = "be"  # big endian
    le = "le"  # little endian (word order for 32-bit types)


WORDS_BY_TYPE = {
    RegType.u16: 1,
    RegType.i16: 1,
    RegType.u32: 2,
    RegType.i32: 2,
    RegType.f32: 2,
}


class RegisterDef(BaseModel):
    name: str = Field(..., description="Human-readable register name")
    address: int = Field(..., ge=0, le=65535)
    function: int = Field(3, description="3=holding, 4=input")
    type: RegType
    words: Optional[int] = None
    endianness: Endianness = Endianness.be
    scale: float = 1.0
    unit: Optional[str] = None
    access: Access = Access.RO
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    critical: bool = False
    description: Optional[str] = None

    @model_validator(mode="after")
    def _set_words_and_validate(self):
        if self.words is None:
            self.words = WORDS_BY_TYPE[self.type]
        elif self.words != WORDS_BY_TYPE[self.type]:
            raise ValueError(f"'words' must match type {self.type} -> {WORDS_BY_TYPE[self.type]}")
        if self.minimum is not None and self.maximum is not None:
            if self.minimum >= self.maximum:
                raise ValueError("minimum must be < maximum")
        return self


class Metadata(BaseModel):
    brand: str
    model: str
    protocol_version: Optional[str] = None
    notes: Optional[str] = None


class DeviceProfile(BaseModel):
    meta: Metadata
    registers: List[RegisterDef]
    version: str = "1.0"


from typing import Type
from warnings import warn

from tivars.models import *
from ..data import *
from ..var import TIEntry
from .numeric import *
from .real import *


class RealPart(Converter):
    """
    Converter for the real part of complex numbers

    Real parts are instances of `RealEntry`.
    """

    _T = RealEntry

    @classmethod
    def get(cls, data: bytes, *, instance=None) -> _T:
        """
        Converts `bytes` -> `RealType`

        :param data: The raw bytes to convert
        :param instance: The instance containing the data section
        :return: The real part of `data` converted to the appropriate type
        """

        return instance.real_type.get(data)

    @classmethod
    def set(cls, value: _T, **kwargs) -> bytes:
        """
        Converts `RealEntry` -> `bytes`

        :param value: The value to convert
        :return: The data of `value`
        """

        value.subtype_id = value.imag_subtype_id

        return type(value).set(value)


class ImaginaryPart(Converter):
    """
    Converter for the imaginary part of complex numbers

    Imaginary parts are instances of `RealEntry`.
    """

    _T = RealEntry

    @classmethod
    def get(cls, data: bytes, *, instance=None) -> _T:
        """
        Converts `bytes` -> `RealType`

        :param data: The raw bytes to convert
        :param instance: The instance containing the data section
        :return: The real part of `data` converted to the appropriate type
        """

        return instance.imag_type.get(data)

    @classmethod
    def set(cls, value: _T, *, instance=None, **kwargs) -> bytes:
        """
        Converts `RealEntry` -> `bytes`

        :param value: The value to convert
        :param instance: The instance containing the data section
        :return: The data of `value`
        """

        value.subtype_id = value.imag_subtype_id
        instance.coerce()

        return type(value).set(value)


class ComplexEntry(TIEntry):
    """
    Base class for complex numeric types

    This class handles floating-point types as well as the exact formats for the TI-83PCE and other newer models.
    The format for these types varies and is handled by `real_subtype_id` and `imag_subtype_id`.

    Two `RealEntry` types are used to form a single `ComplexEntry` corresponding to a complex number.
    These types need not be the same, and will have subtype IDs not corresponding to their native type IDs.
    """

    extensions = {
        None: "8xc",
        TI_82: "",
        TI_83: "83c",
        TI_82A: "8xc",
        TI_82P: "8xc",
        TI_83P: "8xc",
        TI_84P: "8xc",
        TI_84T: "8xc",
        TI_84PCSE: "8xc",
        TI_84PCE: "8xc",
        TI_84PCEPY: "8xc",
        TI_83PCE: "8xc",
        TI_83PCEEP: "8xc",
        TI_82AEP: "8xc"
    }

    min_data_length = 18

    is_exact = False
    """
    Whether this numeric type is exact
    """

    real_analogue = TIReal
    """
    The real type corresponding to this complex type used in an imaginary part
    """

    def __init__(self, init=None, *,
                 for_flash: bool = True, name: str = "A",
                 version: bytes = None, archived: bool = None,
                 data: bytearray = None):

        super().__init__(init, for_flash=for_flash, name=name, version=version, archived=archived, data=data)

    def __complex__(self):
        return self.complex()

    def __format__(self, format_spec: str) -> str:
        match format_spec:
            case "":
                return self.string()
            case "t":
                return squash(replacer(self.string(), {"i": "[i]", " 1[i]": "[i]", "+ 0[i]": "", "0 +": "",
                                                       "-": "~"}))
            case _:
                try:
                    return format(self.complex(), format_spec)

                except (TypeError, ValueError):
                    return super().__format__(format_spec)

    @Section(min_data_length)
    def calc_data(self) -> bytearray:
        """
        The data section of the entry

        Contains two real numbers, the real and imaginary parts
        """

    @View(calc_data, RealPart)[0:9]
    def real(self) -> RealEntry:
        """
        The real part of the complex number
        """

    @View(calc_data, ImaginaryPart)[9:18]
    def imag(self) -> RealEntry:
        """
        The imaginary part of the complex number
        """

    @View(calc_data, Bits[0:6])[0:1]
    def real_subtype_id(self) -> bytes:
        """
        The subtype ID of the real part
        """

    @View(calc_data, Bits[6:7])[0:1]
    def real_graph_bit(self) -> int:
        """
        Whether the entry is used during graphing
        """

    @View(calc_data, Bits[7:8])[0:1]
    def real_sign_bit(self) -> int:
        """
        The sign bit for the real part

        If this bit is set, the real part is negative.
        """

    @View(calc_data, Bits[0:6])[9:10]
    def imag_subtype_id(self) -> bytes:
        """
        The subtype ID of the complex part
        """

    @View(calc_data, Bits[6:7])[9:10]
    def imag_graph_bit(self) -> int:
        """
        Whether the entry is used during graphing
        """

    @View(calc_data, Bits[7:8])[9:10]
    def imag_sign_bit(self) -> int:
        """
        The sign bit for the complex part

        If this bit is set, the complex part is negative.
        """

    @property
    def real_type(self) -> Type['RealEntry']:
        """
        :return: The subclass of `RealEntry` corresponding to this entry's `real_subtype_id`.
        """

        return self.get_type(self.real_subtype_id).real_analogue

    @property
    def imag_type(self) -> Type['RealEntry']:
        """
        :return: The subclass of `RealEntry` corresponding to this entry's `imag_subtype_id`.
        """

        return self.get_type(self.imag_subtype_id).real_analogue

    def clear(self):
        super().clear()

        self.real_subtype_id = 0x0C
        self.imag_subtype_id = self.type_id

    def components(self) -> (RealEntry, RealEntry):
        """
        :return: The components of this complex number as a pair of `RealEntry` values
        """

        return self.real, self.imag

    @Loader[complex, float, int]
    def load_complex(self, comp: complex):
        """
        Loads this complex number from a `complex`, upcasting as necessary

        :param comp: The complex number to load
        """

        raise NotImplementedError

    def complex(self):
        """
        :return: The `complex` corresponding to this complex number
        """

        return self.real.float() + 1j * self.imag.float()

    @Loader[str]
    def load_string(self, string: str):
        string = replacer(squash(string), {"*": "", "-": "+-", "[i]": "i", "j": "i"})

        # Split into real and imaginary components
        parts = string.strip("+").split("+")
        if not parts[0]:
            parts = parts[1:]

        # Add missing components
        if len(parts) == 1:
            if "i" in parts[0]:
                parts = ["0", parts[0]]

            else:
                parts = [parts[0], "0i"]

        parts[1] = parts[1].replace("i", "") or "1"

        try:
            self.real = self.real_type(parts[0])

        except (TypeError, ValueError):
            for type_id in [0x00, 0x18, 0x1C, 0x20, 0x21]:
                if type_id == self.real_subtype_id:
                    continue

                try:
                    self.real = self.get_type(type_id)(parts[0])
                    break

                except (TypeError, ValueError):
                    continue

            else:
                raise ValueError(f"could not parse real part '{parts[0]}'")

        self.imag = self.imag_type(parts[1])

    def string(self) -> str:
        match str(self.real), str(self.imag):
            case "0", "0":
                return "0"

            case _, "0":
                return str(self.real)

            case "0", _:
                return f"{self.imag}i"

            case _:
                return replacer(f"{self.real} + {self.imag}i", {"+ -": "- ", " 1i": " i"})

    def coerce(self):
        self.type_id = self.imag_subtype_id
        if subclass := self.get_type(self.type_id):
            self.__class__ = subclass

        else:
            warn(f"Subtype ID 0x{self.type_id:02x} is not recognized; entry will not be coerced to its proper type.",
                 BytesWarning)


class TIComplex(ComplexEntry, register=True):
    """
    Parser for complex entries with floating point imaginary part

    A `TIComplex` has a `TIReal` as its imaginary part.
    """

    real_analogue = TIReal

    _type_id = 0x0C

    @Loader[complex, float, int]
    def load_complex(self, comp: complex):
        real, imag = self.real_type(), self.imag_type()
        comp = complex(comp)

        real.load_float(comp.real)
        imag.load_float(comp.imag)

        self.real, self.imag = real, imag


class TIComplexFraction(TIComplex, register=True):
    """
    Parser for complex entries with fractional imaginary part

    A `TIComplexFraction` has a `TIRealFraction` as its imaginary part.
    """

    is_exact = True

    real_analogue = TIRealFraction

    _type_id = 0x1B

    def __init__(self, init=None, *,
                 for_flash: bool = True, name: str = "A",
                 version: bytes = None, archived: bool = None,
                 data: bytearray = None):

        super().__init__(init, for_flash=for_flash, name=name, version=version, archived=archived, data=data)

        self.version = 0x0B

    def string(self) -> str:
        match str(self.real), str(self.imag):
            case "0", "0":
                return "0"

            case _, "0":
                return str(self.real)

            case "0", _:
                return str(self.imag).replace(' /', 'i /')

            case _:
                return replacer(f"{self.real} + {str(self.imag).replace(' /', 'i /')}", {"+ -": "- ", " 1i": " i"})


class TIComplexRadical(ComplexEntry, register=True):
    r"""
    Parser for complex entries with radical imaginary part

    A `TIComplexRadical` has a `TIRealRadical` as its imaginary part.
    """

    flash_only = True

    is_exact = True

    real_analogue = TIRealRadical

    _type_id = 0x1D

    def __init__(self, init=None, *,
                 for_flash: bool = True, name: str = "A",
                 version: bytes = None, archived: bool = None,
                 data: bytearray = None):

        super().__init__(init, for_flash=for_flash, name=name, version=version, archived=archived, data=data)

    @Loader[complex, float, int]
    def load_complex(self, comp: complex):
        return NotImplemented

    def string(self) -> str:
        return super().string().replace("i", " * i")


class TIComplexPi(TIComplex, register=True):
    """
    Parser for complex entries with imaginary part an integer multiple of π

    A `TIComplexPi` has a `TIRealPi` as its imaginary part.
    """

    flash_only = True

    is_exact = True

    real_analogue = TIRealPi

    _type_id = 0x1E

    def __init__(self, init=None, *,
                 for_flash: bool = True, name: str = "A",
                 version: bytes = None, archived: bool = None,
                 data: bytearray = None):

        super().__init__(init, for_flash=for_flash, name=name, version=version, archived=archived, data=data)

        self.version = 0x10

    @Loader[complex, float, int]
    def load_complex(self, comp: complex):
        return NotImplemented


class TIComplexPiFraction(TIComplexPi, TIComplexFraction, register=True):
    """
    Parser for complex entries with imaginary part a fractional multiple of π

    A `TIComplexPiFraction` has a `TIRealPiFraction` as its imaginary part.
    """

    flash_only = True

    is_exact = True

    real_analogue = TIRealPiFraction

    _type_id = 0x1F

    def __init__(self, init=None, *,
                 for_flash: bool = True, name: str = "A",
                 version: bytes = None, archived: bool = None,
                 data: bytearray = None):

        super().__init__(init, for_flash=for_flash, name=name, version=version, archived=archived, data=data)

        self.version = 0x10

    def string(self) -> str:
        return super(TIComplexPi, self).string()

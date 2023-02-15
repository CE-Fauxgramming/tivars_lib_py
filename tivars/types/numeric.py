from tivars.models import *
from ..data import *
from ..var import TIEntry


def to_bcd(number: int) -> bytes:
    return int.to_bytes(int(str(number), 16), 7, 'big')


def from_bcd(bcd: bytes) -> int:
    number = 0
    for byte in bcd:
        tens, ones = divmod(byte, 16)

        number += 10 * tens + ones
        number *= 100

    return number


Mantissa = (to_bcd, from_bcd)


class TIReal(TIEntry):
    extensions = {
        None: "8xn",
        TI_82: "82n",
        TI_83: "83n",
        TI_82A: "8xn",
        TI_82P: "8xn",
        TI_83P: "8xn",
        TI_84P: "8xn",
        TI_84T: "8xn",
        TI_84PCSE: "8xn",
        TI_84PCE: "8xn",
        TI_84PCEPY: "8xn",
        TI_83PCE: "8xn",
        TI_83PCEEP: "8xn",
        TI_82AEP: "8xn"
    }

    _type_id = b'\x00'

    @Section(9)
    def data(self) -> bytearray:
        """
        The data section of the entry

        Contains flags, a mantissa, and an exponent
        """

    @View(data, Integer)[0:1]
    def flags(self) -> int:
        """
        Flags for the real number

        If bit 1 is set, the number is undefined
        If bits 2 and 3 are set and bit 1 is clear, the number if half of a complex number
        If bit 6 is set, something happened
        If bit 7 is set, the number is negative
        """

    @View(data, Integer)[1:2]
    def exponent(self) -> int:
        """
        The exponent of the real number

        The exponent has a bias of 0x80
        """

    @View(data, Mantissa)[2:9]
    def mantissa(self) -> int:
        """
        The mantissa of the real number

        The mantissa is 14 digits stored in BCD format, two digits per byte
        """

    @property
    def is_complex_component(self) -> bool:
        return self.flags & 1 << 2 & 1 << 3 & ~1 << 1

    @property
    def is_undefined(self) -> bool:
        return self.flags & 1 << 1

    @property
    def sign(self) -> int:
        return -1 if self.flags & 1 << 7 else 1

    def load_string(self, string: str):
        string = string.lower().replace("~", "-").replace("|e", "e")

        if "e" not in string:
            string += "e0"

        if "." not in string:
            string = string.replace("e", ".e")

        neg = string.startswith("-")
        string = string.strip("+-")

        number, exponent = string.split("e")
        integer, decimal = number.split(".")
        integer, decimal = integer or "0", decimal or "0"

        exponent = int(exponent or "0")
        while len(integer) > 1:
            decimal = integer[-1] + decimal
            integer = integer[:-1]
            exponent += 1

        self.mantissa = int((integer + decimal).ljust(14, "0"))
        self.exponent = exponent + 0x80

        if neg:
            self.negate()

    def negate(self):
        self.flags ^= 1 << 7

    def string(self) -> str:
        return f"{self.sign * self.mantissa * 10 ** (self.exponent - 0x80 - 15):-}"


class TIComplex(TIEntry):
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

    _type_id = b'\x0C'


__all__ = ["TIReal", "TIComplex"]
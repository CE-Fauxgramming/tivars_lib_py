from tivars.models import *
from tivars.tokenizer import encode, decode
from tivars.tokenizer.tokens import *
from ..var import TIEntry


class TokenizedVar(TIEntry):
    extensions = {
        None: "8xp",
        TI_82: "82p",
        TI_83: "83p",
        TI_82A: "8xp",
        TI_82P: "8xp",
        TI_83P: "8xp",
        TI_84P: "8xp",
        TI_84T: "8xp",
        TI_84PCSE: "8xp",
        TI_84PCE: "8xp",
        TI_84PCEPY: "8xp",
        TI_83PCE: "8xp",
        TI_83PCEEP: "8xp",
        TI_82AEP: "8xp"
    }

    versions = [
        b'\x00', b'\x01', b'\x02', b'\x03', b'\x04', b'\x05', b'\x06',
        b'\x0A', b'\x0B', b'\x0C',
        b'\x20', b'\x21', b'\x22', b'\x23', b'\x24', b'\x25', b'\x26',
        b'\x2A', b'\x2B', b'\x2C'
    ]

    tokens = {
        TI_82: (TI82_TOKENS, TI82_BYTES),
        TI_83: (TI83_TOKENS, TI83_BYTES),
        TI_82A: (TI83_TOKENS, TI83_BYTES),
        TI_83P: (TI83_TOKENS, TI83_BYTES),
        TI_84P: (TI83_TOKENS, TI83_BYTES),
        TI_84T: (TI83_TOKENS, TI83_BYTES),
        TI_84PCSE: (CSE_TOKENS, CSE_BYTES),
        TI_84PCE: (CE_TOKENS, CE_BYTES),
        TI_84PCEPY: (CE_TOKENS, CE_BYTES),
        TI_83PCE: (CE_TOKENS, CE_BYTES),
        TI_83PCEEP: (CE_TOKENS, CE_BYTES),
        TI_82AEP: (CE_TOKENS, CE_BYTES)
    }

    def load_string(self, string: str):
        token_map = self.tokens[TI_84PCEPY][0]
        self.raw.data = encode(string, token_map)

    def string(self) -> str:
        byte_map = self.tokens[TI_84PCEPY][1]
        return decode(self.data, byte_map)


class TIEquation(TokenizedVar):
    _type_id = b'\x03'


class TIString(TokenizedVar):
    _type_id = b'\x04'


class TIProgram(TokenizedVar):
    _type_id = b'\x05'


class TIProtectedProgram(TIProgram):
    _type_id = b'\x06'


__all__ = ["TIEquation", "TIString", "TIProgram", "TIProtectedProgram"]
from functools import total_ordering

from ..flags import *
from ..tokenizer.tokens.scripts import OsVersion, Tokens, TokenTrie
from ..tokenizer.tokens.scripts.parse import MODEL_ORDER


@total_ordering
class TIModel:
    MODELS = []

    def __init__(self, name: str, flags: 'TIFeature', magic: str, product_id: int, lang: str):
        self._name = name
        self._flags = TIFeature(flags, width=9)
        self._magic = magic
        self._product_id = product_id
        self._lang = lang

        with open("tivars/tokenizer/tokens/8X.xml", encoding="UTF-8") as file:
            self._tokens = Tokens.from_xml_string(file.read(), self.OS())
            self._trie = TokenTrie.from_tokens(self._tokens, "en")

    def __eq__(self, other):
        return str(self) == str(other)

    def __ge__(self, other):
        return self.order >= other.order

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name

    @property
    def flags(self) -> 'TIFeature':
        return self._flags

    @property
    def lang(self) -> str:
        return self._lang

    @property
    def magic(self) -> str:
        return self._magic

    @property
    def name(self) -> str:
        return self._name

    @property
    def order(self) -> int:
        return MODEL_ORDER[self._name]

    @property
    def product_id(self) -> int:
        return self._product_id

    @property
    def tokens(self) -> Tokens:
        return self._tokens

    @property
    def trie(self) -> TokenTrie:
        return self._trie

    def OS(self, version: str = "latest") -> OsVersion:
        return OsVersion(self.name, version)


class TIFeature(Flags):
    Default = {0: 1}
    Complex = {1: 1}
    Flash = {2: 1}
    Apps = {3: 1}
    Clock = {4: 1}
    Color = {5: 1}
    ez80 = {6: 1}
    ExactMath = {7: 1}
    Python = {8: 1}


flags82 = TIFeature.Default
flags83 = flags82 | TIFeature.Complex
flags82a = flags83 | TIFeature.Flash
flags83p = flags82a | TIFeature.Apps
flags84p = flags83p | TIFeature.Clock
flags84pcse = flags84p | TIFeature.Color
flags84pce = flags84pcse | TIFeature.ez80
flags83pce = flags84pce | TIFeature.ExactMath
flags83pceep = flags83pce | TIFeature.Python
flags84pcepy = flags84pce | TIFeature.Python
flags82aep = flags83pceep | {3: 0}

TIModel.MODELS = [
    TI_82 := TIModel("TI-82", flags82, "**TI82**", 0x00, "en"),

    TI_83 := TIModel("TI-83", flags83, "**TI83**", 0x00, "en"),
    TI_82ST := TIModel("TI-82ST", flags83, "**TI83**", 0x00, "en"),
    TI_82ST_fr := TIModel("TI-82ST.fr", flags83, "**TI83**", 0x00, "fr"),
    TI_76_fr := TIModel("TI-76.fr", flags83, "**TI83**", 0x00, "fr"),

    TI_83P := TIModel("TI-83+", flags83p, "**TI83F*", 0x04, "en"),
    TI_83PSE := TIModel("TI-83+SE", flags83p, "**TI83F*", 0x04, "en"),
    TI_83P_fr := TIModel("TI-83+.fr", flags83p, "**TI83F*", 0x04, "fr"),
    TI_82P := TIModel("TI-82+", flags83p, "**TI83F*", 0x04, "fr"),

    TI_84P := TIModel("TI-84+", flags84p, "**TI83F*", 0x0A, "en"),
    TI_84PSE := TIModel("TI-84+SE", flags84p, "**TI83F*", 0x0A, "en"),
    TI_83P_fr_USB := TIModel("TI-83+.fr:USB", flags84p, "**TI83F*", 0x0A, "fr"),
    TI_84P_fr := TIModel("TI-84P.fr", flags84p, "**TI83F*", 0x0A, "fr"),
    TI_84PPSE := TIModel("TI-84+PSE", flags84p, "**TI83F*", 0x0A, "en"),

    TI_82A := TIModel("TI-82A", flags82a, "**TI83F*", 0x0B, "fr"),
    TI_84T := TIModel("TI-84+T", flags84p, "**TI83F*", 0x1B, "en"),

    TI_84PCSE := TIModel("TI-84+CSE", flags84pcse, "**TI83F*", 0x0F, "en"),

    TI_84PCE := TIModel("TI-84+CE", flags84pce, "**TI83F*", 0x13, "en"),
    TI_84PCET := TIModel("TI-84+CET", flags84pce, "**TI83F*", 0x13, "en"),
    TI_83PCE := TIModel("TI-83PCE", flags83pce, "**TI83F*", 0x13, "fr"),
    TI_83PCEEP := TIModel("TI-83PCEEP", flags83pceep, "**TI83F*", 0x13, "fr"),
    TI_84PCEPY := TIModel("TI-84+CEPY", flags84pcepy, "**TI83F*", 0x13, "en"),
    TI_84PCETPE := TIModel("TI-84+CETPE", flags84pcepy, "**TI83F*", 0x13, "en"),
    TI_82AEP := TIModel("TI-82AEP", flags82aep, "**TI83F*", 0x00, "fr"),
]

__all__ = ["TI_82",
           "TI_83", "TI_82ST", "TI_82ST_fr", "TI_76_fr",
           "TI_83P", "TI_83PSE", "TI_83P_fr", "TI_82P",
           "TI_84P", "TI_84PSE", "TI_83P_fr_USB", "TI_84P_fr", "TI_84PPSE",
           "TI_84T", "TI_82A",
           "TI_84PCSE",
           "TI_84PCE", "TI_84PCET", "TI_83PCE", "TI_83PCEEP", "TI_84PCEPY", "TI_84PCETPE", "TI_82AEP",
           "TIFeature", "TIModel"]

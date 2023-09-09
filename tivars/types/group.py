import io

from warnings import warn

from tivars.models import *
from ..data import *
from ..var import TIEntry, SizedEntry
from .gdb import TIGraphedEquation


class TIGroup(SizedEntry, register=True):
    """
    Parser for group objects

    A group is a collection of entries packaged together for easy transfer and saving in the archive.
    Each entry is stored with its entry in the VAT followed by its regular data.

    The VAT information can be safely ignored since it is redetermined when importing back onto a calculator.
    """

    _T = 'TIGroup'

    extensions = {
        None: "8xg",
        TI_82: "82g",
        TI_83: "83g",
        TI_83P: "8xg"
    }

    _type_id = 0x17

    def __init__(self, init=None, *,
                 for_flash: bool = True, name: str = "GROUP",
                 version: int = None, archived: bool = True,
                 data: bytes = None):

        super().__init__(init, for_flash=for_flash, name=name, version=version, archived=archived, data=data)

    @staticmethod
    def group(entries: list[TIEntry], *, name: str = "GROUP") -> 'TIGroup':
        """
        Creates a new `TIGroup` by packaging a ``list`` of entries using defaulted VAT data

        :param entries: The entries to group
        :param name: The name of the group (defaults to ``GROUP``)
        :return: A group containing ``entries``
        """

        if not entries:
            return TIGroup(name=name)

        group = TIGroup(for_flash=entries[0].meta_length > TIEntry.base_meta_length, name=name)

        for entry in entries:
            name = entry.raw.name.rstrip(b'\x00')
            vat = bytearray([entry.type_id, 0, entry.version, 0, 0, entry.archived])

            if isinstance(entry, TIGraphedEquation):
                vat[0] |= entry.raw.flags

            match entry.type_id:
                case 0x05 | 0x06 | 0x15 | 0x17:
                    vat += [len(name), *name]

                case 0x01 | 0x0D:
                    vat += [len(name) + 1, *name, 0]

                case _:
                    vat += name.ljust(3, b'\x00')

            group.data += vat
            group.data += entry.calc_data

        return group

    def get_min_os(self, data: bytes = None) -> OsVersion:
        return max([entry.get_min_os() for entry in self.ungroup()], default=OsVersions.INITIAL)

    def get_version(self, data: bytes = None) -> int:
        return max([entry.get_version() for entry in self.ungroup()], default=0x00)

    def ungroup(self) -> list[TIEntry]:
        """
        :return: A ``list`` of entries stored in this group
        """

        data = io.BytesIO(self.data[:])
        entries = []

        index = 1
        while type_byte := data.read(1):
            _, version = data.read(2)

            match type_id := type_byte[0] & 15:
                case 0x05 | 0x06 | 0x15 | 0x17:
                    *_, page, length = data.read(4)

                    if length > 8:
                        warn(f"The name length of entry #{index} ({length}) exceeds eight.",
                             BytesWarning)

                    name = data.read(length)

                case 0x01 | 0x0D:
                    *_, page, length = data.read(4)

                    if length > 7:
                        warn(f"The name length of entry #{index} ({length - 2}), a list, exceeds five.",
                             BytesWarning)

                    name = data.read(length - 1)
                    data.read(1)

                case _:
                    *_, page = data.read(3)
                    name = data.read(3)

            entry = TIEntry(for_flash=self.meta_length > TIEntry.base_meta_length, version=version, archived=page > 0)
            entry.type_id = type_id
            entry.coerce()

            entry.raw.name = name.ljust(8, b'\x00')
            entry.load_data_section(data)

            if isinstance(entry, TIGraphedEquation):
                entry.raw.flags = type_byte

            entries.append(entry)

        return entries

    @Loader[list]
    def load_from_entries(self, entries: list[TIEntry]):
        """
        Loads a ``list`` of entries into this group

        All VAT data is cleared.

        :param entries: The entries to group
        """

        self.data = self.group(entries).data

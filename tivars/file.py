from io import BytesIO
from pathlib import Path
from typing import BinaryIO, IO, Type
from warnings import warn

from .data import *
from .models import *


def get_extension(extensions: dict[TIModel, str], model: TIModel):
    extension = ""
    for min_model in reversed(TIModel.MODELS):
        if min_model in extensions and min_model <= model:
            extension = extensions[min_model]
            break

    if not extension:
        warn(f"The {model} does not support this type.",
             UserWarning)

        return extensions.get(None)

    return extension


class TIFile(Dock):
    magics = []
    _magics = {}

    def __init__(self, *, name: str = "UNNAMED", data: bytes = None):
        """
        Creates an empty file with a specified name

        :param name: The name of the file (defaults to ``UNNAMED``)
        :param data: The file's data (defaults to empty)
        """

        self.name = name

        if data:
            self.load_bytes(data)

    def __bool__(self) -> bool:
        """
        :return: Whether this file is empty
        """

        return not len(self)

    def __bytes__(self) -> bytes:
        """
        :return: The bytes contained in this file
        """

        return self.bytes()

    def __copy__(self) -> 'TIFile':
        """
        :return: A copy of this var
        """

        new = self.__class__()
        new.load_bytes(self.bytes())
        return new

    def __eq__(self, other: 'TIFile'):
        """
        Determines if two files are identical

        :param other: The file to check against
        :return: Whether this file is equal to ``other``
        """

        try:
            return self.__class__ == other.__class__ and self.bytes() == other.bytes()

        except AttributeError:
            return False

    def __init_subclass__(cls, /, register=False, **kwargs):
        super().__init_subclass__(**kwargs)

        if register:
            TIFile.register(cls)

    def __len__(self):
        """
        :return: The total length of this file in bytes
        """

        return len(self.bytes())

    @property
    def checksum(self) -> bytes:
        """
        The checksum for the file
        """

        raise NotImplementedError

    @property
    def is_empty(self) -> bool:
        """
        :return: Whether this file is empty
        """

        raise NotImplementedError

    @classmethod
    def get_type(cls, magic: bytes) -> Type['TIFile']:
        """
        Gets the subclass corresponding to file magic if one is registered

        :param magic: The file magic to search by
        :return: A subclass of `TIFile` with corresponding file magic or ``None``
        """

        return cls._magics.get(magic)

    @classmethod
    def register(cls, file_type: Type['TIFile']):
        """
        Registers a subtype with this class for coercion

        :param file_type: The `TIFile` subtype to register
        """

        for magic in file_type.magics:
            cls._magics[magic] = file_type

    def get_extension(self, model: TIModel = None) -> str:
        """
        Determines the file extension for a targeted model based on its contents

        :param model: The model to target (defaults to this file's minimum supported model)
        :return: The file's extension
        """

        raise NotImplementedError

    def get_filename(self, model: TIModel = None):
        """
        Determines the filename based on the instance name and targeted model

        The filename is the concatenation of the name and extension (see `.get_extension`).

        :param model: The model to target (defaults to this file's minimum supported model)
        :return: The filename
        """

        return f"{self.name}.{self.get_extension(model)}"

    def supported_by(self, model: TIModel = None) -> bool | set[TIModel]:
        """
        Determines which model(s) can support this file

        See `.targets` to check models this file explicitly targets.

        :param model: The model to check support for
        :return: Whether ``model`` supports this file, or the set of models this file supports
        """

        raise NotImplementedError

    def targets(self, model: TIModel = None) -> bool | set[TIModel]:
        """
        Determines which model(s) this file can target

        See `.supported_by` to check models this file _can_ be sent to.

        :param model: The model to check as a target
        :return: Whether ``model`` is targeted by this file, or the set of models this file targets
        """

        raise NotImplementedError

    @Loader[bytes, bytearray, IO[bytes]]
    def load_bytes(self, data: bytes | IO[bytes]):
        """
        Loads a byte string or bytestream into this file

        :param data: The bytes to load
        """

        if hasattr(data, "read"):
            data = BytesIO(data.read())

        else:
            data = BytesIO(data)

        for magic in self._magics:
            if data.read(len(magic)).decode() == magic:
                self.__class__ = self._magics[magic]
                self.load_bytes(data)

                return

            data.seek(-len(magic), 1)

        raise TypeError("unrecognized file type")

    def bytes(self) -> bytes:
        """
        :return: The bytes contained in this file
        """

        raise NotImplementedError

    @Loader[BinaryIO]
    def load_file(self, file: BinaryIO):
        """
        Loads this file from a file pointer

        :param file: A binary file to read from
        """

        self.load_bytes(file.read())

    @classmethod
    def open(cls, filename: str) -> 'TIFile':
        """
        Creates a new file given a filename

        :param filename: A filename to open
        :return: The file
        """

        with open(filename, 'rb') as file:
            return cls(name=".".join(Path(filename).name.split(".")[:-1]), data=file.read())

    def save(self, filename: str = None, model: TIModel = TI_84PCE):
        """
        Saves this file given a filename

        :param filename: A filename to save to (defaults to the file's name and extension)
        :param model: The model to target
        """

        with open(filename or self.get_filename(model), 'wb+') as file:
            file.write(self.bytes())

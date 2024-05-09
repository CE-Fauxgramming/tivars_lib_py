from zipfile import ZipFile

from .file import *
from .models import *


class TIBundle(TIFile):
    extensions = {
        TI_84PCE: "b84",
        TI_83PCE: "b83"
    }

    metadata = {
        "b83": ("bundle_identifier:TI Bundle\n"
                "bundle_format_version:1\n"
                "bundle_target_device:83CE\n"
                "bundle_target_type:CUSTOM\n"
                "bundle_comments:N/A\n"),
        "b84": ("bundle_identifier:TI Bundle\n"
                "bundle_format_version:1\n"
                "bundle_target_device:84CE\n"
                "bundle_target_type:CUSTOM\n"
                "bundle_comments:N/A\n"),
    }

    magics = ["PK\x03\x04"]

    def __init__(self, *, name: str = "UNNAMED", model: TIModel = TI_84PCE, data: bytes = None):
        self.model = model
        self.files = []

        super().__init__(name=name, data=data)

    @property
    def checksum(self) -> bytes:
        """
        The checksum for the bundle
        """

        return f"{sum(info.CRC for info in self.zip.infolist()) & 0xFFFFFFFFF:x}\r\n".encode()

    @property
    def is_empty(self) -> bool:
        """
        :return: Whether this file is empty
        """

        raise NotImplementedError

    def get_extension(self, model: TIModel = None) -> str:
        """
        Determines the file extension for this bundle

        :param model: The model to target (defaults to this bundle's model)
        :return: The file's extension
        """

        model = model or self.model

        if "84" in model.name:
            return "b84"

        else:
            return "b83"

    def supported_by(self, model: TIModel = None) -> bool | set[TIModel]:
        """
        Determines which model(s) can support this bundle

        A bundle is supported by its stored model, though can be re-exported for a different target.

        :param model: The model to check support for
        :return: Whether ``model`` supports this bundle, or the set of models this bundle supports
        """

        return model == self.model if model is not None else {model}

    def targets(self, model: TIModel = None) -> bool | set[TIModel]:
        """
        Determines which model(s) this bundle can target

        A bundle can target its stored model, though can be re-exported for a different target.

        :param model: The model to check as a target
        :return: Whether ``model`` is targeted by this bundle, or the set of models this bundle targets
        """

        return model == self.model if model is not None else {model}

    def zip(self) -> ZipFile:
        zipfile = ZipFile(self.files[0].bytes(), "w", allowZip64=False)

        for file in self.files[1:]:
            zipfile.writestr(file.name, file.bytes())

        zipfile.writestr("METADATA", self.metadata[self.get_extension()])
        zipfile.writestr("_CHECKSUM", self.checksum)

    @Loader[bytes, bytearray, IO[bytes]]
    def load_bytes(self, data: bytes | IO[bytes]):
        if hasattr(data, "read"):
            zipfile = ZipFile(data, "r")

        else:
            zipfile = ZipFile(BytesIO(data), "r")

        self.load_zip(zipfile)

    def bytes(self) -> bytes:
        raise NotImplementedError

    @Loader[ZipFile]
    def load_zip(self, zipfile: ZipFile):
        files = []
        for info in zipfile.infolist():
            file = TIFile()
            file.load_bytes(zipfile.open(info.filename, "r"))
            files.append(file)

        self.files = files

    @classmethod
    def open(cls, filename: str) -> 'TIBundle':
        *name, ext = filename.split(".")

        with open(filename, 'rb') as file:
            return cls(name=".".join(name), model=TI_84PCE if "84" in ext else TI_83PCE, data=file.read())


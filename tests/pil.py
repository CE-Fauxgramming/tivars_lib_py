import io
import unittest

from tivars.types.picture import *

try:
    from PIL import Image
    from tivars.PIL import *

except ImportError:
    raise unittest.SkipTest("PIL not installed")


try:
    import numpy as np

except ImportError:
    raise unittest.SkipTest("NumPy not installed")


class PILTests(unittest.TestCase):
    def test_8xi(self):
        ti_img = TIMonoPicture()
        ti_img.open("tests/data/var/BartSimpson.8xi")

        arr = np.asarray(ti_img.array(), dtype=np.uint8)
        img = Image.open("tests/data/var/BartSimpson.8xi")

        self.assertEqual((np.asarray(Image.fromarray(arr, mode=ti_img.pil_mode)) ==
                          np.asarray(img)).all(), True)

        img.save(buf := io.BytesIO(), "8xi")
        buf.seek(0)

        self.assertEqual(buf.read()[72:-2], ti_img.calc_data)

    def test_8ci(self):
        def the_palette_is_stinky(byte: int) -> bytes:
            high, low = byte // 16, byte % 16

            high *= high != 11
            low *= low != 11

            return bytes([16 * high + low])

        ti_img = TIPicture()
        ti_img.open("tests/data/var/Pic1.8ci")

        arr = np.asarray(ti_img.array(), dtype=np.uint8)
        img = Image.open("tests/data/var/Pic1.8ci")

        self.assertEqual((np.asarray(Image.fromarray(arr, mode=ti_img.pil_mode)) ==
                          np.asarray(img)).all(), True)

        img.save(buf := io.BytesIO(), "8ci")
        buf.seek(0)

        trans = b"".join(map(the_palette_is_stinky, range(256)))
        self.assertEqual(buf.read()[72:-2].translate(trans), ti_img.calc_data.translate(trans))

    def test_8ca(self):
        ti_img = TIImage()
        ti_img.open("tests/data/var/Image1.8ca")

        arr = np.asarray(ti_img.array(), dtype=np.uint8)
        img = Image.open("tests/data/var/Image1.8ca")

        self.assertEqual((np.asarray(Image.fromarray(arr, mode=ti_img.pil_mode)) ==
                          np.asarray(img)).all(), True)

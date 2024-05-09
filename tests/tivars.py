import json
import unittest

from decimal import Decimal

from tivars.models import *
from tivars.types import *
from tivars import TIHeader, TIVar, TIFlashHeader


class ModelTests(unittest.TestCase):
    def test_all_models(self):
        for model in TIModel.MODELS:
            self.assertEqual(model, eval(model.name.translate({43: "P", 45: "_", 46: "_", 58: "_"})))

        self.assertEqual(TIModel.MODELS, sorted(TIModel.MODELS))


class VarTests(unittest.TestCase):
    def test_all_attributes(self):
        test_var = TIVar.open("tests/data/var/Program.8xp")
        test_header = TIHeader.open("tests/data/var/Program.8xp")

        self.assertEqual(test_var.header, test_header)

        self.assertEqual(test_var.entries[0].meta_length, TIEntry.flash_meta_length)
        self.assertEqual(test_var.entries[0].type_id, 0x05)
        self.assertEqual(test_var.entries[0].name, "SETDATE")
        self.assertEqual(test_var.entries[0].version, 0x04)
        self.assertEqual(test_var.entries[0].archived, False)

        self.assertEqual(str(test_var.entries[0]), "setDate(1")
        self.assertEqual(test_var.checksum, b'M\x03')

    def test_all_sections(self):
        test_var = TIVar.open("tests/data/var/Program.8xp")

        self.assertEqual(test_var.header.raw.magic, b'**TI83F*')
        self.assertEqual(test_var.header.raw.extra, b'\x1A\x0A')
        self.assertEqual(test_var.header.raw.product_id, b'\x0A')
        self.assertEqual(test_var.header.raw.comment, b'Created by TI Connect CE 5.1.0.68'.ljust(42, b'\x00'))

        self.assertEqual(test_var.header.bytes(),
                         test_var.header.raw.magic + test_var.header.raw.extra +
                         test_var.header.raw.product_id + test_var.header.raw.comment)

        self.assertEqual(test_var.entries[0].raw.meta_length, b'\x0D\x00')
        self.assertEqual(test_var.entries[0].raw.type_id, b'\x05')
        self.assertEqual(test_var.entries[0].raw.name, b'SETDATE\x00')
        self.assertEqual(test_var.entries[0].raw.version, b'\x04')
        self.assertEqual(test_var.entries[0].raw.archived, b'\x00')

        self.assertEqual(test_var.entries[0].flash_bytes,
                         test_var.entries[0].raw.version + test_var.entries[0].raw.archived)

        self.assertEqual(test_var.entries[0].meta,
                         test_var.entries[0].raw.calc_data_length + test_var.entries[0].raw.type_id +
                         test_var.entries[0].raw.name + test_var.entries[0].raw.version +
                         test_var.entries[0].raw.archived)

        self.assertEqual(test_var.entries[0].raw.calc_data, bytearray(b'\x03\x00\xef\x001'))
        self.assertEqual(test_var.entries[0].bytes(),
                         test_var.entries[0].raw.meta_length + test_var.entries[0].raw.meta +
                         test_var.entries[0].raw.calc_data_length + test_var.entries[0].raw.calc_data)

        self.assertEqual(test_var.checksum, b'M\x03')

    def test_multiple_entries(self):
        clibs = TIVar.open("tests/data/var/clibs.8xg")

        self.assertEqual(len(clibs.entries), 9)
        self.assertTrue(all(entry.type_id == 0x15 for entry in clibs.entries))

        second = TIEntry()
        with open("tests/data/var/clibs.8xg", 'rb') as file:
            second.load_from_file(file, offset=1)

        self.assertEqual(second, clibs.entries[1])

    def test_save_to_file(self):
        test_var = TIVar.open("tests/data/var/Program.8xp")

        self.assertEqual(test_var.get_extension(), "8xp")
        self.assertEqual(test_var.get_filename(), "UNNAMED.8xp")
        test_var.save("tests/data/var/Program_new.8xp")

        with open("tests/data/var/Program.8xp", 'rb') as orig:
            with open("tests/data/var/Program_new.8xp", 'rb') as new:
                self.assertEqual(new.read(), orig.read())

        self.assertEqual(test_var.supported_by(TI_84P), True)
        self.assertEqual(test_var.supported_by(TI_83), False)

    def test_truthiness(self):
        test_var = TIVar.open("tests/data/var/clibs.8xg")
        self.assertEqual(bool(test_var), True)

        test_var.clear()
        self.assertEqual(bool(test_var), False)


class EntryTests(unittest.TestCase):
    def test_save_to_file(self):
        test_program = TIEntry.open("tests/data/var/Program.8xp")
        test_header = TIHeader.open("tests/data/var/Program.8xp")

        test_program.save("tests/data/var/Program_new.8xp", header=test_header)

        self.assertEqual(test_program.export().get_filename(), "SETDATE.8xp")
        self.assertEqual(test_program.export(model=TI_83).get_filename(), "SETDATE.83p")

        with open("tests/data/var/Program.8xp", 'rb') as orig:
            with open("tests/data/var/Program_new.8xp", 'rb') as new:
                self.assertEqual(new.read(), orig.read())

    def test_form_vars(self):
        test_program = TIProgram()
        test_header = TIHeader()
        test_var = TIVar()

        with open("tests/data/var/Program.8xp", 'rb') as file:
            test_program.load_from_file(file)
            file.seek(0)

            test_header.load_from_file(file)
            file.seek(0)

            test_var.load_file(file)
            self.assertEqual(test_header | [test_program], test_var)

    def test_truthiness(self):
        test_program = TIEntry.open("tests/data/var/Program.8xp")
        self.assertEqual(bool(test_program), True)

        test_program.clear()
        self.assertEqual(bool(test_program), False)


class TokenizationTests(unittest.TestCase):
    def test_load_from_file(self):
        test_var = TIVar.open("tests/data/var/Program.8xp")

        test_program = TIProgram.open("tests/data/var/Program.8xp")

        self.assertEqual(test_program, test_var.entries[0])

        del test_program
        test_program = TIProgram()

        with open("tests/data/var/Program.8xp", 'rb') as file:
            test_program.load_from_file(file)

            file.seek(55)
            self.assertEqual(test_program.bytes(), file.read()[:-2])

        self.assertEqual(test_program, test_var.entries[0])

    def test_load_from_string(self):
        test_program = TIProgram(name="SETDATE")
        test_program.comment = "Created by TI Connect CE 5.1.0.68"

        test_program.load_string(string := "setDate(1")
        self.assertEqual(test_program.string(), string)

        # Version is wrong(?)
        test_program.version = 0x04

        with open("tests/data/var/Program.8xp", 'rb') as file:
            file.seek(55)
            self.assertEqual(test_program.bytes(), file.read()[:-2])

        self.assertEqual(test_program.supported_by(TI_83PCE), True)
        self.assertEqual(test_program.supported_by(TI_83), False)

    def test_all_tokens(self):
        test_program = TIProgram()

        with open("tests/data/var/ALLTOKS.8Xp", 'rb') as file:
            test_program.load_from_file(file)
            file.seek(55)

            self.assertEqual(test_program.bytes(), file.read()[:-2])
            self.assertEqual(test_program.is_protected, False)
            self.assertEqual(test_program.is_tokenized, True)

    def test_protection(self):
        test_program = TIProtectedProgram(name="SETDATE")
        test_program.load_string("setDate(1")
        test_program.unprotect()

        test_program.version = 0x04
        with open("tests/data/var/Program.8xp", 'rb') as file:
            file.seek(55)
            self.assertEqual(test_program.bytes(), file.read()[:-2])

    def test_doors(self):
        test_program = TIProgram.open("tests/data/var/COLORZ.8xp")
        self.assertEqual(type(test_program), TIProtectedAsmProgram)

        self.assertEqual(test_program.decode(test_program.data[:26]), "Disp \"Needs Doors CSE\"")


class NumericTests(unittest.TestCase):
    def real_float_test(self, real_type, filename, name, sign, exponent, mantissa, string, dec):
        test_num = real_type.open(f"tests/data/var/{filename}.8xn")

        self.assertEqual(test_num.name, name)
        self.assertEqual(test_num.sign, sign)
        self.assertEqual(test_num.exponent, exponent)
        self.assertEqual(test_num.mantissa, mantissa)

        self.assertEqual(str(test_num), string)
        self.assertEqual(f"{test_num:.2f}", f"{dec:.2f}")
        self.assertEqual(test_num.decimal(), dec)

        test_num.clear()
        test_num.load_string(string)
        self.assertEqual(test_num.string(), string)

        with open(f"tests/data/var/{filename}.8xn", 'rb') as file:
            file.seek(55)
            self.assertEqual(test_num.bytes(), file.read()[:-2])

    def test_real_number(self):
        self.real_float_test(TIReal, "Real", "A", -1, 129, 42133700000000, "-42.1337",
                             Decimal("-42.1337"))

    def test_real_pi(self):
        self.real_float_test(TIRealPi, "Exact_RealPi", "C", 1, 129, 30000000000000, "30π",
                             Decimal("94.247779607694"))

    def test_real_pi_frac(self):
        self.real_float_test(TIRealPiFraction, "Exact_RealPiFrac", "D", 1, 127, 28571428571429, "2π / 7",
                             Decimal("0.89759790102567"))

    def test_real_radical(self):
        test_radical = TIRealRadical.open("tests/data/var/Exact_RealRadical.8xn")

        self.assertEqual(test_radical.sign_type, 2)
        self.assertEqual(test_radical.left_scalar, 41)
        self.assertEqual(test_radical.left_radicand, 789)
        self.assertEqual(test_radical.right_scalar, 14)
        self.assertEqual(test_radical.right_radicand, 654)
        self.assertEqual(test_radical.denominator, 259)

    def complex_float_test(self, comp_type, filename, name, real_sign, real_exponent, real_mantissa,
                           imag_sign, imag_exponent, imag_mantissa, string, comp):

        test_num = comp_type.open(f"tests/data/var/{filename}.8xc")

        self.assertEqual(test_num.real.sign, real_sign)
        self.assertEqual(test_num.real.exponent, real_exponent)
        self.assertEqual(test_num.real.mantissa, real_mantissa)

        self.assertEqual(test_num.imag.sign, imag_sign)
        self.assertEqual(test_num.imag.exponent, imag_exponent)
        self.assertEqual(test_num.imag.mantissa, imag_mantissa)

        self.assertEqual(str(test_num), string)
        self.assertEqual(f"{test_num:.2f}", f"{comp:.2f}")

        self.assertEqual(test_num.name, name)
        test_components = comp_type(name=name)
        test_components.real, test_components.imag = test_num.real, test_num.imag
        self.assertEqual(test_num, test_components)
        self.assertEqual(test_components.components()[0], test_num.real)
        self.assertEqual(test_components.components()[1], test_num.imag)

        test_num.clear()
        test_num.load_string(string)
        self.assertEqual(test_num.string(), string)

        with open(f"tests/data/var/{filename}.8xc", 'rb') as file:
            file.seek(55)
            self.assertEqual(test_num.bytes(), file.read()[:-2])

    def test_complex_number(self):
        self.complex_float_test(TIComplex, "Complex", "C", -1, 128, 50000000000000,
                                1, 128, 20000000000000, "-5 + 2i", -5 + 2j)

    def test_complex_frac(self):
        self.complex_float_test(TIComplexFraction, "Exact_ComplexFrac", "E", 1, 127, 20000000000000,
                                -1, 127, 40000000000000, "1 / 5 - 2i / 5", 0.2 - 0.4j)

    def test_complex_pi(self):
        self.complex_float_test(TIComplexPi, "Exact_ComplexPi", "H", 1, 127, 20000000000000,
                                -1, 128, 30000000000000, "1 / 5 - 3πi", 0.2 - 9.42j)

    def test_complex_pi_frac(self):
        self.complex_float_test(TIComplexPiFraction, "Exact_ComplexPiFrac", "A", 1, 128, 0,
                                1, 127, 28571428571429, "2πi / 7", 0.90j)

    def test_coercion(self):
        test_num = TIComplexFraction("1 + 3/5i")
        self.assertEqual(test_num.real_type, TIReal)
        self.assertEqual(test_num.imag_type, TIRealFraction)
        self.assertEqual(str(test_num), "1 + 3i / 5")

        test_num.imag = TIReal("0.6")
        self.assertEqual(test_num.real_type, TIReal)
        self.assertEqual(test_num.imag_type, TIReal)
        self.assertEqual(str(test_num), "1 + 0.6i")
        self.assertEqual(type(test_num), TIComplex)


class ArrayTests(unittest.TestCase):
    def test_real_list(self):
        test_real_list = TIRealList.open("tests/data/var/RealList.8xl")

        test_list = [TIReal("-1.0"), TIReal("2.0"), TIReal("999")]

        self.assertEqual(test_real_list.name, "Z")
        self.assertEqual(test_real_list.length, 3)
        self.assertEqual(test_real_list.list(), test_list)
        self.assertEqual(list(iter(test_real_list)), test_list)
        self.assertEqual(str(test_real_list), "[-1, 2, 999]")
        self.assertEqual(f"{test_real_list:t}", "{~1,2,999}")

    def test_complex_list(self):
        test_comp_list = TIComplexList.open("tests/data/var/ComplexList.8xl")

        test_list = [TIComplex(1 + 1j), TIComplex("-3 + 2i"), TIComplex(4 + 0j)]

        self.assertEqual(test_comp_list.name, "I")
        self.assertEqual(test_comp_list.length, 3)
        self.assertEqual(test_comp_list.list(), test_list)
        self.assertEqual(list(iter(test_comp_list)), test_list)
        self.assertEqual(str(test_comp_list), "[1 + i, -3 + 2i, 4]")
        self.assertEqual(f"{test_comp_list:t}", "{1+[i],~3+2[i],4}")

    def test_matrix(self):
        test_matrix = TIMatrix.open("tests/data/var/Matrix_3x3_standard.8xm")

        test_array = [[TIReal(0.5), TIReal(-1.0), TIReal("2.6457513110646")],
                      [TIReal("2.7386127875258"), TIReal("0.5"), TIReal("3.1415926535898")],
                      [TIReal("1"), TIReal(99999999), TIReal(0)]]

        self.assertEqual(test_matrix.name, "[A]")
        self.assertEqual(test_matrix.height, 3)
        self.assertEqual(test_matrix.width, 3)
        self.assertEqual(test_matrix.matrix(), test_array)
        self.assertEqual(list(iter(test_matrix)), [entry for row in test_array for entry in row])

        self.assertEqual(str(test_matrix), "[[0.5, -1, 2.6457513110646],"
                                           " [2.7386127875258, 0.5, 3.1415926535898],"
                                           " [1, 99999999, 0]]")
        self.assertEqual(f"{test_matrix:t}", "[[0.5,~1,2.6457513110646]"
                                             "[2.7386127875258,0.5,3.1415926535898]"
                                             "[1,99999999,0]]")

    def test_exact_matrix(self):
        test_matrix = TIMatrix.open("tests/data/var/Matrix_2x2_exact.8xm")

        test_array = [[TIRealPi("3π"), TIRealRadical("3√10")],
                      [TIRealFraction("1/2"), TIRealRadical("(4√5 + 2√3) / 7")]]

        self.assertEqual(test_matrix.name, "[B]")
        self.assertEqual(test_matrix.height, 2)
        self.assertEqual(test_matrix.width, 2)
        self.assertEqual(test_matrix.matrix(), test_array)
        self.assertEqual(list(iter(test_matrix)), [entry for row in test_array for entry in row])


class SettingsTests(unittest.TestCase):
    def test_window(self):
        test_window = TIWindowSettings.open("tests/data/var/Window.8xw")

        zero, one, undef = TIReal(0), TIReal(1), TIUndefinedReal(1)
        tau, pi_twenty_fourths = TIReal("6.283185307"), TIReal("0.13089969389957")

        self.assertEqual(test_window.name, "Window")
        self.assertEqual(test_window.PlotStart, one)
        self.assertEqual(test_window.PlotStep, one)

        self.assertEqual(test_window.unMin0, undef)
        self.assertEqual(test_window.unMin1, undef)
        self.assertEqual(test_window.vnMin0, undef)
        self.assertEqual(test_window.vnMin1, undef)
        self.assertEqual(test_window.wnMin0, undef)
        self.assertEqual(test_window.wnMin1, undef)

        self.assertEqual(test_window.Thetamax, tau)
        self.assertEqual(test_window.Thetamin, zero)
        self.assertEqual(test_window.Thetastep, pi_twenty_fourths)

        self.assertEqual(test_window.Tmax, tau)
        self.assertEqual(test_window.Tmin, zero)
        self.assertEqual(test_window.Tstep, pi_twenty_fourths)

        self.assertEqual(test_window.Xmax, TIReal("10"))
        self.assertEqual(test_window.Xmin, TIReal("-10"))
        self.assertEqual(test_window.Xres, TIReal(2))
        self.assertEqual(test_window.Xscl, TIReal("1"))

        self.assertEqual(test_window.Ymax, TIReal("20"))
        self.assertEqual(test_window.Ymin, TIReal(-20))
        self.assertEqual(test_window.Yscl, TIReal("2"))

    def test_recall(self):
        test_recall = TIRecallWindow.open("tests/data/var/RecallWindow.8xz")

        zero, one, undef = TIReal("0"), TIReal("1"), TIUndefinedReal("1")
        tau, pi_twenty_fourths = TIReal(6.283185307), TIReal("0.13089969389957")

        self.assertEqual(test_recall.name, "RclWindw")
        self.assertEqual(test_recall.PlotStart, one)
        self.assertEqual(test_recall.PlotStep, one)

        self.assertEqual(test_recall.unMin0, undef)
        self.assertEqual(test_recall.unMin1, undef)
        self.assertEqual(test_recall.vnMin0, undef)
        self.assertEqual(test_recall.vnMin1, undef)
        self.assertEqual(test_recall.wnMin0, undef)
        self.assertEqual(test_recall.wnMin1, undef)

        self.assertEqual(test_recall.Thetamax, tau)
        self.assertEqual(test_recall.Thetamin, zero)
        self.assertEqual(test_recall.Thetastep, pi_twenty_fourths)

        self.assertEqual(test_recall.Tmax, tau)
        self.assertEqual(test_recall.Tmin, zero)
        self.assertEqual(test_recall.Tstep, pi_twenty_fourths)

        self.assertEqual(test_recall.Xmax, TIReal("10"))
        self.assertEqual(test_recall.Xmin, TIReal(-10.0))
        self.assertEqual(test_recall.Xres, TIReal("1"))
        self.assertEqual(test_recall.Xscl, TIReal("1"))

        self.assertEqual(test_recall.Ymax, TIReal("10"))
        self.assertEqual(test_recall.Ymin, TIReal("-10"))
        self.assertEqual(test_recall.Yscl, TIReal(1))

    def test_table(self):
        test_table = TITableSettings.open("tests/data/var/TableRange.8xt")

        self.assertEqual(test_table.name, "TblSet")
        self.assertEqual(test_table.TblMin, TIReal(0.0))
        self.assertEqual(test_table.DeltaTbl, TIReal("1"))


class GDBTests(unittest.TestCase):
    def test_func_gdb(self):
        test_gdb = TIMonoGDB.open("tests/data/var/GraphDataBase.8xd")

        self.assertEqual(type(test_gdb), TIFuncGDB)
        self.assertEqual(test_gdb.name, "GDB1")

        self.assertEqual(test_gdb.Xmax, eleven_pi_over_four := TIReal("8.639379797"))
        self.assertEqual(test_gdb.Xmin, -eleven_pi_over_four)
        self.assertEqual(test_gdb.Xres, TIReal(2))
        self.assertEqual(test_gdb.Xscl, TIReal("1.5707963267949"))

        self.assertEqual(test_gdb.Ymax, TIReal(4.0))
        self.assertEqual(test_gdb.Ymin, TIReal(-4.0))
        self.assertEqual(test_gdb.Yscl, TIReal(1))

        self.assertEqual(test_gdb.Y1.equation(), TIEquation("sin(X", name="Y1"))
        self.assertEqual(test_gdb.Y1.style, GraphStyle.ThickLine)
        self.assertEqual(test_gdb.Y1.color, GraphColor.Blue)
        self.assertEqual(test_gdb.grid_color, GraphColor.MedGray)

        self.assertIn(GraphMode.Connected, test_gdb.mode_flags)
        self.assertIn(GraphMode.AxesOn, test_gdb.mode_flags)
        self.assertIn(GraphMode.ExprOn, test_gdb.extended_mode_flags)
        self.assertIn(GraphMode.DetectAsymptotesOn, test_gdb.color_mode_flags)

    def test_json(self):
        test_gdb = TIParamGDB()

        with open("tests/data/json/param.json") as file:
            param = json.load(file)

        test_gdb.load_dict(param)

        tau, pi_twenty_fourths = TIReal(6.283185307), TIReal("0.13089969389957")
        self.assertEqual(test_gdb.Xmax.bytes(), TIReal(10).bytes())
        self.assertEqual(test_gdb.Xmin, TIReal(-10))
        self.assertEqual(test_gdb.Tmax, tau)
        self.assertEqual(test_gdb.Tstep, pi_twenty_fourths)

        self.assertEqual(test_gdb.X2T.equation(), TIEquation(name="X2T"))
        self.assertEqual(test_gdb.X2T.style, GraphStyle.ThickLine)
        self.assertEqual(test_gdb.X2T.color, GraphColor.Red)
        self.assertEqual(test_gdb.axes_color, GraphColor.Black)

        self.assertIn(GraphMode.Sequential, test_gdb.mode_flags)
        self.assertIn(GraphMode.CoordOn, test_gdb.mode_flags)
        self.assertIn(GraphMode.ExprOn, test_gdb.extended_mode_flags)
        self.assertIn(GraphMode.DetectAsymptotesOn, test_gdb.color_mode_flags)

        self.assertEqual(test_gdb.dict(), param)
        self.assertEqual(dict(test_gdb), param)

        self.assertEqual(test_gdb.length, 142)


class PictureTests(unittest.TestCase):
    def test_mono_picture(self):
        test_picture = TIPicture()

        with open("tests/data/var/BartSimpson.8xi", 'rb') as file:
            test_picture.load_from_file(file)
            file.seek(0)

            self.assertEqual(test_picture.bytes(), file.read()[55:-2])

        self.assertEqual(test_picture.name, "Pic2")

        test_from_array = TIMonoPicture()
        test_from_array.load_array(test_picture.array())
        self.assertEqual(test_from_array.array(), test_picture.array())

    def test_picture(self):
        test_picture = TIPicture()

        with open("tests/data/var/Pic1.8ci", 'rb') as file:
            test_picture.load_from_file(file)
            file.seek(0)

            self.assertEqual(test_picture.bytes(), file.read()[55:-2])

        self.assertEqual(test_picture.name, "Pic1")

        test_from_array = TIPicture()
        test_from_array.load_array(test_picture.array())
        self.assertEqual(test_from_array.array(), test_picture.array())

    def test_image(self):
        test_image = TIImage()

        with open("tests/data/var/Image1.8ca", 'rb') as file:
            test_image.load_from_file(file)
            file.seek(0)

            self.assertEqual(test_image.bytes(), file.read()[55:-2])

        self.assertEqual(test_image.name, "Image1")

        test_from_array = TIImage()
        test_from_array.load_array(test_image.array())
        self.assertEqual(test_from_array.array(), test_image.array())


class AppVarTests(unittest.TestCase):
    def test_app_var(self):
        test_app_var = TIAppVar()

        with open("tests/data/var/AppVar.8xv", 'rb') as file:
            test_app_var.load_from_file(file)
            file.seek(0)

            self.assertEqual(test_app_var.bytes(), file.read()[55:-2])

        self.assertEqual(test_app_var.name, "FILEIOC")
        self.assertEqual(test_app_var.length, 2578)


class GroupTests(unittest.TestCase):
    def test_group(self):
        test_group = TIGroup()

        with open("tests/data/var/Group.8xg", 'rb') as file:
            test_group.load_from_file(file)
            file.seek(0)

            self.assertEqual(test_group.bytes(), file.read()[55:-2])

        ungrouped = test_group.ungroup()

        self.assertEqual(ungrouped[0], TIEquation("10sin(theta", name="R1"))
        self.assertEqual(type(ungrouped[1]), TIWindowSettings)

        self.assertEqual(TIGroup.group(ungrouped).ungroup(), ungrouped)
        self.assertEqual(TIGroup(ungrouped).ungroup(), ungrouped)


class FlashTests(unittest.TestCase):
    def test_app(self):
        test_app = TIFlashHeader()

        with open("tests/data/var/smartpad.8xk", 'rb') as file:
            test_app.load_from_file(file)
            file.seek(0)

            self.assertEqual(test_app.bytes(), file.read())

        self.assertEqual(test_app.object_type, 0x88)
        self.assertEqual(test_app.device_type, DeviceType.TI_83P)
        self.assertEqual(test_app.product_id, 0x00)
        self.assertEqual(type(test_app), TIApp)

        self.assertEqual(test_app.binary_flag, 0x01)
        self.assertEqual(type(test_app.data), list)

    def test_os(self):
        test_os = TIFlashHeader.open("tests/data/var/TI-84_Plus_CE-Python-OS-5.8.0.0022.8eu")

        self.assertEqual(test_os.revision, "5.8")
        self.assertEqual(test_os.object_type, 0x00)
        self.assertEqual(test_os.product_id, 0x13)
        self.assertEqual(type(test_os), TIOperatingSystem)

        self.assertEqual(test_os.binary_flag, 0x00)
        self.assertEqual(type(test_os.data), bytes)

    def test_license(self):
        test_license = TILicense.open("tests/data/var/ti89_2.01_10-13-1999.89u")

        self.assertEqual(test_license.magic, "**TIFL**")
        self.assertEqual(test_license.date, (12, 10, 1999))
        self.assertEqual(test_license.devices, [(0x74, 0x3E), (0x73, 0x3E), (0x98, 0x3E), (0x88, 0x3E)])
        self.assertEqual(test_license.license.split("\r\n")[2], "Texas Instruments License Agreement")

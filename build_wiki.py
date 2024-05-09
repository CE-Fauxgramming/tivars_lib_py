import ast
import os

from functools import total_ordering
from importlib import import_module

from wiki.template import *


@total_ordering
class Section:
    def __init__(self, name, cls, nodes):
        self.name = " ".join(word[0].upper() + word[1:] for word in name.split("_"))
        self.subsections = []

        # There's just no need
        if self.name == "Calc Data":
            self.name = "Data"

        doc = getattr(cls, name).__doc__ or ""
        try:
            self.description = doc.split("\n")[1].strip()
            self.notes = f"\n{20 * ' '}".join("<li>" + note.strip() if note.strip() else ""
                                              for note in doc.split("\n")[2:-1])

        except IndexError:
            self.description, self.notes = doc.strip(), ""

        if len(self.description.split(": ")) == 2:
            self.name, self.description = self.description.split(": ")

        texts[cls.__name__] = cls.__doc__ or ""

        if isinstance(deco := nodes[name].decorator_list[-1], ast.Call):
            if deco.func.id == "Section":
                self.order = 0
                self.offset = 0

                try:
                    self.length = deco.args[0].value

                except IndexError:
                    self.length = None

                except AttributeError:
                    self.length = getattr(cls, deco.args[0].id)

                try:
                    self.get_type(deco.args[1])

                except IndexError:
                    self.type = "Bytes"

                self.parent = None

            else:
                self.order = deco.args[1].slice.value - 2 ** 15

                if deco.args[1].slice.value == 1:
                    self.offset = getattr(cls(), "offset") + getattr(cls(), "num_styles")
                else:
                    self.offset = "..."

                self.length = "..."
                self.type = deco.args[1].value.id
                self.parent = deco.args[0].id

        else:
            self.order = ast.literal_eval(deco.slice.lower or "0")
            self.offset = ast.literal_eval(deco.slice.lower or "0")
            self.length = (ast.literal_eval(deco.slice.upper or "0")) - self.offset
            self.get_type(deco.value.args[1])
            self.parent = deco.value.args[0].id

    def __gt__(self, other):
        return self.order % 2 ** 16 > other.order % 2 ** 16

    @property
    def span(self):
        return len(self.subsections)

    def get_type(self, arg):
        if isinstance(arg, ast.Subscript):
            self.type = f"{arg.value.id}" \
                        f"[{(arg.slice.lower or ast.Constant(0)).value}:{(arg.slice.upper or ast.Constant(8)).value}]"

        else:
            self.type = arg.id


classes = {}
enums = {}
texts = {}
pages = {}


def is_section(attr) -> bool:
    if not isinstance(attr, ast.FunctionDef):
        return False

    if decorator_list := attr.decorator_list:
        if isinstance(first := decorator_list[-1], ast.Call):
            return True

        if isinstance(first, ast.Subscript) and isinstance(first.value, ast.Call):
            return True

    return False


def add_classes(path):
    with open(path, 'r', encoding="utf8") as file:
        node = ast.parse(file.read())

    loc = path.split("/")[-1][:-3]
    module = vars(import_module(".".join(path.split("/")[:-1])))[loc]

    for child in ast.iter_child_nodes(node):
        if not isinstance(child, ast.ClassDef):
            continue

        name = child.name
        if name.startswith("TI") or name.endswith("Entry") and name != "SizedEntry":
            classes[name] = (vars(module)[name], {attr.name: attr for attr in child.body if is_section(attr)})
            pages[loc] = pages.get(loc, []) + [name]

        elif name.endswith("Flags"):
            enums[name] = vars(module)[name]
            pages[loc] = pages.get(loc, []) + [name]


# Grab all the classes
add_classes("tivars/var.py")
for filename in next(os.walk("tivars/types"), (None, None, []))[2]:
    if not filename.startswith("__") and filename.endswith(".py"):
        add_classes("tivars/types/" + filename)


# Inherit ast information from base classes
for tup in classes.values():
    for base in tup[0].mro():
        if base.__name__ != "TIEntry":
            try:
                tup[1].update(classes[base.__name__][1])

            except KeyError:
                pass


# Convert to Section objects
classes = {class_name: {section_name: Section(section_name, *tup) for section_name in tup[1]}
           for class_name, tup in classes.items()}


# Create subsections
for class_name, sections in classes.items():
    for section in sections.values():
        if section.parent is not None:
            sections[section.parent].subsections.append(section)


# Split up GDBs
for class_name in pages["gdb"]:
    match class_name:
        case "TIMonoFuncGDB" | "TIFuncGDB":
            pages["Function-GDBs"] = pages.get("Function-GDBs", []) + [class_name]

        case "TIMonoParamGDB" | "TIParamGDB":
            pages["Parametric-GDBs"] = pages.get("Parametric-GDBs", []) + [class_name]

        case "TIMonoPolarGDB" | "TIPolarGDB":
            pages["Polar-GDBs"] = pages.get("Polar-GDBs", []) + [class_name]

        case "TIMonoSeqGDB" | "TISeqGDB":
            pages["Sequential-GDBs"] = pages.get("Sequential-GDBs", []) + [class_name]

        case _:
            pages["GDB"] = pages.get("GDB", []) + [class_name]

del pages["gdb"]


# Write pages
for page in pages:
    if page == "var":
        continue

    if page.endswith("GDBs"):
        page_name = page + ".md"

    elif page == "GDB":
        page_name = "GDB-Components.md"

    else:
        page_name = page.capitalize() + "-Entries.md"

    content = ""

    for class_name in pages[page]:
        # Lib-specific helper parents
        if class_name.endswith("Entry"):
            continue

        if class_name in classes:
            content += f"### {class_name}\n" + texts.get(class_name, "").rstrip() + "\n\n" + table_header

            for section in classes[class_name].values():
                # Subsections are handled by their parent
                if section.parent:
                    continue

                # TIGraphedEquations are weird
                if class_name == "TIGraphedEquation" and section.name in ("Style", "Color"):
                    continue

                # Name logic changes a lot
                if section.name == "Name":
                    content += name_row.format(section=section, subsection=section)

                else:
                    if not section.subsections:
                        section.subsections = [section]

                    else:
                        section.subsections.sort()

                    content += top_row.format(section=section, subsection=section.subsections[0])

                    for subsection in section.subsections[1:]:
                        if subsection:
                            content += later_row.format(section=section, subsection=subsection)

            content += table_footer

    with open("wiki/" + page_name, "w+", encoding="utf-8") as file:
        file.write(content)

    print(f"Wrote page {page_name}")

import sys
from pathlib import Path

import marko
import marko.block
import marko.inline


def __raise_exception(t: type):
    raise TypeError(f"Unexpected type: {t.__module__}.{t.__qualname__}")


def get_paragraph_text(paragraph: marko.block.Paragraph):
    text = ""

    for children in paragraph.children:
        if isinstance(children, marko.inline.RawText):
            text += children.children
        else:
            __raise_exception(type(children))

    return text


def get_description(doc: marko.block.Document):
    found_heading = False
    description = ""

    for section in doc.children:
        if isinstance(section, marko.block.Heading):
            if found_heading:
                break

            found_heading = True
        elif isinstance(section, marko.block.BlankLine):
            description += "\n\n"
        elif isinstance(section, marko.block.Paragraph):
            description += get_paragraph_text(section)
        elif isinstance(section, marko.block.List):
            new_list = "<ul>"

            for item in section.children:
                new_list += "\n<li>"
                if isinstance(item, marko.block.ListItem):
                    for item_child in item.children:
                        if isinstance(item_child, marko.block.Paragraph):
                            new_list += get_paragraph_text(item_child).strip("\n")
                        else:
                            __raise_exception(type(item_child))
                else:
                    __raise_exception(type(item))
                new_list += "</li>"

            new_list.strip("\n")
            new_list += "\n</ul>"

            description += new_list
        else:
            __raise_exception(type(section))

    return description.strip("\n")


def main():
    path = Path.cwd() / "README.md"

    if not path.is_file():
        sys.exit("README.md does not exists!")

    text = ""

    contents = path.read_text("utf-8")
    parser = marko.Parser()
    doc = parser.parse(contents)

    print("Fetching description...")
    text += get_description(doc)


if __name__ == "__main__":
    main()

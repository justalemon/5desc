import os
import sys
from pathlib import Path

import dulwich.errors
import dulwich.repo
import marko
import marko.block
import marko.inline


def __raise_exception(t: type):
    raise TypeError(f"Unexpected type: {t.__module__}.{t.__qualname__}")


def build_link(link: marko.inline.Link):
    link_href = link.dest
    link_text = get_raw_text(link.children)
    return f"<a href=\"{link_href}\">{link_text}</a>"


def get_raw_text(children: str | list[marko.inline.Element]):
    if isinstance(children, str):
        return children

    text = ""

    for link_children in children:
        if isinstance(link_children, marko.inline.RawText):
            text += link_children.children
        elif isinstance(link_children, marko.inline.Link):
            text += build_link(link_children)
        else:
            __raise_exception(type(link_children))

    return text


def get_paragraph_text(paragraph: marko.block.Paragraph | marko.block.Quote):
    text = ""

    for children in paragraph.children:
        if isinstance(children, marko.inline.RawText):
            text += children.children
        elif isinstance(children, marko.inline.Link):
            text += build_link(children)
        elif isinstance(children, marko.block.Paragraph):
            text += get_paragraph_text(children)
        elif isinstance(children, marko.inline.StrongEmphasis):
            strong = get_raw_text(children.children)
            text += f"<b>{strong}</b>"
        else:
            __raise_exception(type(children))

    return text


def get_text(doc: marko.block.Document, from_heading: str = None):
    heading_level = 0
    description = ""

    for section in doc.children:
        if heading_level == 0 and not isinstance(section, marko.block.Heading):
            continue

        if isinstance(section, marko.block.Heading):
            if from_heading is not None:
                if heading_level > 0:
                    if section.level <= heading_level:
                        break
                    else:
                        description += f"<b>{get_raw_text(list(section.children))}</b>"
                else:
                    for heading_children in section.children:
                        if isinstance(heading_children, marko.inline.RawText):
                            if heading_children.children == from_heading:
                                heading_level = section.level
                                break
            else:
                if heading_level > 0 and heading_level <= section.level:
                    break

                heading_level = section.level
        elif isinstance(section, marko.block.BlankLine):
            description += "\n\n"
        elif isinstance(section, (marko.block.Paragraph, marko.block.Quote)):
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


def get_github_repo():
    if "GITHUB_REPOSITORY" in os.environ:
        return "https://github.com/" + os.environ["GITHUB_REPOSITORY"]

    try:
        repo = dulwich.repo.Repo(".")
    except dulwich.errors.NotGitRepository:
        return None

    config = repo.get_config()
    remote = config.get(("remote", "origin"), "url").decode("utf-8")
    remote = remote.replace("git@github.com:", "https://github.com/")
    remote = remote.rstrip(".git")

    return remote


def main():
    path = Path.cwd() / "README.md"

    if not path.is_file():
        sys.exit("README.md does not exists!")

    print("Fetching Repo...")
    repo = get_github_repo()

    if repo is None:
        sys.exit("Couldn't find GitHub repository!")
    if not repo.startswith("https://github.com"):
        sys.exit("Repository is not a GitHub repository!")

    print(f"Found {repo}")

    contents = path.read_text("utf-8")
    parser = marko.Parser()
    doc = parser.parse(contents)

    print("Fetching Description...")
    description = get_text(doc)
    installation = get_text(doc, "Installation")

    return


if __name__ == "__main__":
    main()

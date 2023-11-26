import os
import sys
from pathlib import Path

import dulwich.errors
import dulwich.repo
import marko
import marko.block
import marko.inline

LICENSES = [
    ("MIT License", "MIT License"),
    ("Apache License", "Apache License", "Version 2.0", "January 2004"),
    ("GNU GPL v3.0", "GNU GENERAL PUBLIC LICENSE", "Version 3", "29 June 2007"),
    ("GNU GPL v2.0", "GNU GENERAL PUBLIC LICENSE", "Version 2", "June 1991")
]


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


def detect_license():
    path = Path.cwd() / "LICENSE"

    if not path.is_file():
        return None

    text = path.read_text("utf-8")

    for license_entry in LICENSES:
        name = license_entry[0]
        matches = license_entry[1:]

        if all(x in text for x in matches):
            return name

    return "Unknown"


def build_footer(links: dict[str, tuple[str, str]], repo: str):
    lines = []

    if "discord-url" in links:
        discord = links["discord-url"][0]
        lines.append(f"<b>Join the Conversation</b>: <a href=\"{discord}\">{discord}</a>")
    if "patreon-url" in links or "paypal-url" in links:
        patreon = links["patreon-url"][0] if  "patreon-url" in links else None
        paypal = links["paypal-url"][0] if  "paypal-url" in links else None
        formatted_links = [f"<a href=\"{x}\">{x}</a>" for x in filter(None, [patreon, paypal])]
        lines.append("<b>Support my Mods</b>: " + " / ".join(formatted_links))

    local_license = detect_license()

    lines.append(f"<b>Source Code</b>: <a href=\"{repo}\">{repo}</a> (under {local_license})")
    lines.append(f"<b>Feature Requests & Bug Reports</b>: <a href=\"{repo}/issues\">{repo}/issues</a>")
    lines.append(f"<b>Full Changelog</b>: <a href=\"{repo}/releases\">{repo}/releases</a>")

    return "\n".join(lines)


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
    print("Fetching Installation Instructions...")
    installation = get_text(doc, "Installation")
    print("Building Footer...")
    footer = build_footer(doc.link_ref_defs, repo)
    print("Constructing final text...")
    text = f"{description}\n<b>Installation Instructions</b>\n{installation}\n\n{footer}"

    print("Saving...")
    destination = Path.cwd() / "README.html"
    destination.write_text(text, "utf-8")

    print("Done 🍋")


if __name__ == "__main__":
    main()

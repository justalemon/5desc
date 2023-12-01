import argparse
import os
import re
import sys
from pathlib import Path

import dulwich.errors
import dulwich.repo
import marko
import marko.block
import marko.inline

RE_GITHUB = re.compile("github.com[/:]([a-zA-Z]+)/([a-zA-Z0-9]+)")
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


def get_github_slug():
    if "GITHUB_REPOSITORY" in os.environ:
        return os.environ["GITHUB_REPOSITORY"]

    try:
        repo = dulwich.repo.Repo(".")
    except dulwich.errors.NotGitRepository:
        return None

    config = repo.get_config()

    for section in config.sections():
        name = section[0].decode("utf-8")

        if name != "remote":
            continue

        remote = config.get(section, "url").decode("utf-8")
        match = RE_GITHUB.search(remote)

        if not match:
            continue

        groups = match.groups()
        owner = groups[0]
        name = groups[1]

        return f"{owner}/{name}"

    return None


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


def build_footer(links: dict[str, tuple[str, str]], repo_slug: str):
    lines = []

    if "discord-url" in links:
        discord = links["discord-url"][0]
        lines.append(f"<b>Join the Conversation</b>: <a href=\"{discord}\">{discord}</a>")
    if "patreon-url" in links or "paypal-url" in links:
        patreon = links["patreon-url"][0] if  "patreon-url" in links else None
        paypal = links["paypal-url"][0] if  "paypal-url" in links else None
        formatted_links = [f"<a href=\"{x}\">{x}</a>" for x in filter(None, [patreon, paypal])]
        lines.append("<b>Support my Mods</b>: " + " / ".join(formatted_links))

    if repo_slug is not None:
        local_license = detect_license()
        repo = f"https://github.com/{repo_slug}"

        lines.append(f"<b>Source Code</b>: <a href=\"{repo}\">{repo}</a> (under {local_license})")
        lines.append(f"<b>Feature Requests & Bug Reports</b>: <a href=\"{repo}/issues\">{repo}/issues</a>")
        lines.append(f"<b>Full Changelog</b>: <a href=\"{repo}/releases\">{repo}/releases</a>")

    return "\n".join(lines)


def parse_params():
    parser = argparse.ArgumentParser(prog="5desc",
                                     description="5desc is a program for generating 5mods descriptions",
                                     epilog="made with ❤️ with 🍋")
    parser.add_argument("input",
                        help="the input markdown file",
                        default="README.md",
                        nargs="?")
    parser.add_argument("output",
                        help="the output html file",
                        nargs="?")

    return parser.parse_args()


def main():
    args = parse_params()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve() if args.output else input_path.with_suffix(".html")

    if not input_path.is_file():
        sys.exit(f"{input_path} does not exists!")

    print(f"Using {input_path} as the input file and {output_path} as the output file")

    print("Fetching Repo...")
    repo_slug = get_github_slug()

    if repo_slug is None:
        print("Warning: Couldn't find GitHub repository, will skip GitHub Links")
    else:
        print(f"Found GitHub Repository: {repo_slug}")

    contents = input_path.read_text("utf-8")
    parser = marko.Parser()
    doc = parser.parse(contents)

    print("Fetching Description...")
    description = get_text(doc)
    print("Fetching Installation Instructions...")
    installation = get_text(doc, "Installation")
    print("Building Footer...")
    footer = build_footer(doc.link_ref_defs, repo_slug)
    print("Constructing final text...")
    text = f"{description}\n\n<b>Installation Instructions</b>\n\n{installation}\n\n{footer}\n"

    print("Saving...")
    output_path.write_text(text, "utf-8")

    print("Done 🍋")


if __name__ == "__main__":
    main()

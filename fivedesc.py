#!/usr/bin/env python

"""
5desc: A tool for generating 5mods descriptions.

(c) 2023 Hannele Ruiz

Under the MIT License.
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Optional

import dulwich
import dulwich.errors
import dulwich.repo
import marko
import marko.block
import marko.inline
import requests

RE_GITHUB = re.compile("github.com[/:]([a-zA-Z]+)/([a-zA-Z0-9]+)")
PARSER = marko.Parser()
LICENSES = [
    ("MIT License", "MIT License"),
    ("Apache License", "Apache License", "Version 2.0", "January 2004"),
    ("GNU GPL v3.0", "GNU GENERAL PUBLIC LICENSE", "Version 3", "29 June 2007"),
    ("GNU GPL v2.0", "GNU GENERAL PUBLIC LICENSE", "Version 2", "June 1991")
]


def __raise_exception(t: type) -> None:
    raise TypeError(f"Unexpected type: {t.__module__}.{t.__qualname__}")


def __build_link(link: marko.inline.Link) -> str:
    link_href = link.dest
    link_text = __get_raw_text(link.children)
    return f'<a href="{link_href}">{link_text}</a>'


def __get_raw_text(children: str | list[marko.inline.Element]) -> str:
    if isinstance(children, str):
        return children

    text = ""

    for link_children in children:
        if isinstance(link_children, marko.inline.RawText):
            text += link_children.children
        elif isinstance(link_children, marko.inline.Link):
            text += __build_link(link_children)
        else:
            __raise_exception(type(link_children))

    return text


def __get_paragraph_text(paragraph: marko.block.Paragraph | marko.block.Quote) -> Optional[str]:
    text = ""

    for children in paragraph.children:
        if isinstance(children, marko.inline.RawText):
            text += children.children
        elif isinstance(children, marko.inline.Link):
            text += __build_link(children)
        elif isinstance(children, marko.block.Paragraph):
            text += __get_paragraph_text(children)
        elif isinstance(children, marko.inline.StrongEmphasis):
            strong = __get_raw_text(children.children)
            text += f"<b>{strong}</b>"
        else:
            __raise_exception(type(children))

    return text


def __get_text(doc: marko.block.Document, from_heading: Optional[str] = None) -> Optional[str]:
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
                    description += f"<b>{__get_raw_text(list(section.children))}</b>"
                else:
                    for h_children in section.children:
                        if isinstance(h_children, marko.inline.RawText) and h_children.children == from_heading:
                            heading_level = section.level
                            break
            else:
                if heading_level > 0 and heading_level <= section.level:
                    break

                heading_level = section.level
        elif isinstance(section, marko.block.BlankLine):
            description += "\n\n"
        elif isinstance(section, (marko.block.Paragraph, marko.block.Quote)):
            description += __get_paragraph_text(section)
        elif isinstance(section, marko.block.List):
            new_list = "<ul>"

            for item in section.children:
                new_list += "\n<li>"
                if isinstance(item, marko.block.ListItem):
                    for item_child in item.children:
                        if isinstance(item_child, marko.block.Paragraph):
                            new_list += __get_paragraph_text(item_child).strip("\n")
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


def __get_github_slug() -> Optional[str]:
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


def __detect_license() -> Optional[str]:
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


def __build_changelog(repo_slug: str) -> Optional[str]:
    if not repo_slug:
        return None

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    if "GITHUB_TOKEN" in os.environ:
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]

    releases_raw = []
    page = 1

    while True:
        resp = requests.get(f"https://api.github.com/repos/{repo_slug}/releases?per_page=100&page={page}",
                            headers=headers)

        if not resp.ok:
            print(f"Unable to fetch Releases from GitHub: Code {resp.status_code}")
            return None

        fetched_releases = resp.json()

        if not fetched_releases:
            break

        releases_raw.extend(fetched_releases)
        page += 1

    if not releases_raw:
        return None

    releases_formatted = []

    for release in releases_raw:
        name = release["name"]
        body = release["body"].replace("\r\n", "\n").strip("\n")
        releases_formatted.append(f"<b>{name}</b>\n\n{body}")

    return "\n\n".join(releases_formatted)


def __build_footer(links: dict[str, tuple[str, str]], repo_slug: str) -> str:
    lines = []

    if "discord-url" in links:
        discord = links["discord-url"][0]
        lines.append(f'<b>Join the Conversation</b>: <a href="{discord}">{discord}</a>')
    if "patreon-url" in links or "paypal-url" in links:
        patreon = links["patreon-url"][0] if "patreon-url" in links else None
        paypal = links["paypal-url"][0] if "paypal-url" in links else None
        formatted_links = [f'<a href="{x}">{x}</a>' for x in filter(None, [patreon, paypal])]
        lines.append("<b>Support my Mods</b>: " + " / ".join(formatted_links))

    if repo_slug is not None:
        local_license = __detect_license()
        repo = f"https://github.com/{repo_slug}"

        lines.append(f'<b>Source Code</b>: <a href="{repo}">{repo}</a> (under {local_license})')
        lines.append(f'<b>Feature Requests & Bug Reports</b>: <a href="{repo}/issues">{repo}/issues</a>')
        lines.append(f'<b>Full Changelog</b>: <a href="{repo}/releases">{repo}/releases</a>')

    return "\n".join(lines)


def __parse_params() -> argparse.Namespace:
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
    parser.add_argument("--no-changelog",
                        help="don't include the changelog from GitHub",
                        action="store_true")

    return parser.parse_args()


def main():  # noqa: ANN201, D103
    args = __parse_params()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve() if args.output else input_path.with_suffix(".html")

    if not input_path.is_file():
        sys.exit(f"{input_path} does not exists!")

    print(f"Using {input_path} as the input file and {output_path} as the output file")

    print("Fetching Repo...")
    repo_slug = __get_github_slug()

    if repo_slug is None:
        print("Warning: Couldn't find GitHub repository, will skip GitHub Links")
    else:
        print(f"Found GitHub Repository: {repo_slug}")

    contents = input_path.read_text("utf-8")
    doc = PARSER.parse(contents)

    print("Fetching Description...")
    description = __get_text(doc)
    print("Fetching Installation Instructions...")
    installation = __get_text(doc, "Installation")
    print("Building Footer...")
    footer = __build_footer(doc.link_ref_defs, repo_slug)

    if not args.no_changelog:
        print("Fetching releases for changelog...")
        changelog = __build_changelog(repo_slug)
    else:
        print("Skipping changelog generation")
        changelog = None

    print("Constructing final text...")
    text = f"{description}\n\n<b>Installation Instructions</b>\n\n{installation}\n\n{footer}\n"

    if changelog:
        text += f"\n<b>Changelog</b>\n\n{changelog}\n"

    print("Saving...")
    output_path.write_text(text, "utf-8")

    print("Done 🍋")


if __name__ == "__main__":
    main()

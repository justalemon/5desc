# 5desc<br>[![GitHub Actions][actions-img]][actions-url] [![Patreon][patreon-img]][patreon-url] [![PayPal][paypal-img]][paypal-url] [![Discord][discord-img]][discord-url]

5desc (codename REGB) is a simple Python tool that can be used standalone or as a GitHub Action to convert a README.md into a format compatible with 5mods html tag limitations (only `<b>`, `<i>`, `<u>`, `<a>`, `<ul>`, `<ol>` and `<li>` is allowed) and that can be copy pasted to avoid the broken input text box ("Invalid character in description").

## Download

* [GitHub Releases](https://github.com/justalemon/5desc/releases)
* [GitHub Actions](https://github.com/justalemon/5desc/actions) (experimental versions)

## Installation

### GitHub Action

To use 5desc in the description, add the step to your job:

```
      - uses: justalemon/5desc@v1.0
        env:
          GITHUB_TOKEN: ${{ github.token }}
```

### Windows Executable

Extract the .exe files from the Windows folder in the compressed file somewhere in your system.

### Python Wheel

Extract the .whl file from the Python folder in the compressed files and then run:

```
pip install 5desc-[VERSION]-py3-none-any.whl
```

That will install the Python Wheel and all of it's requirements.

### Docker Container

Run the following command in a terminal to pull the Docker container:

```
docker pull ghcr.io/justalemon/5desc
```

## Usage

Open a terminal/console and run `5desc`. This will automatically convert your README.md to a README.html compatible with 5mods.

For Docker, you can use the following command to run 5desc in the current working directory in Windows:

```
docker run --rm -it -v "%cd%":/files ghcr.io/justalemon/5desc
```

You can specify the name of the input file as the first parameter and the name of the output file as the second parameter. For GitHub Actions, This would be specified in the `with` key, called input and output respectively.

To list the available command line arguments, run 5desc with the `--help` parameter.

[actions-img]: https://img.shields.io/github/actions/workflow/status/justalemon/5desc/main.yml?branch=master&label=actions
[actions-url]: https://github.com/justalemon/5desc/actions
[patreon-img]: https://img.shields.io/badge/support-patreon-FF424D.svg
[patreon-url]: https://www.patreon.com/lemonchan
[paypal-img]: https://img.shields.io/badge/support-paypal-0079C1.svg
[paypal-url]: https://paypal.me/justalemon
[discord-img]: https://img.shields.io/badge/discord-join-7289DA.svg
[discord-url]: https://discord.gg/Cf6sspj

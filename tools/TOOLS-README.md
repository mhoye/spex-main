# SPEX Tools

This folder is for the various utilities that either build spex files
or replace utilities around them with sqlite-based analogues. 


## Setting up Debian-based systems 

On Debian you'll need to install these packages via apt to build
and install the binary-format loader part of the project.

- gcc,
- sqlite3-dev,
- sqlite3-0 and
- pkg-config packages

To work with the Python part of the project, you'll first need to install

- curl, to install the uv package manager
- pyinstaller to package the tools up into standalone executables,
- pandoc and python3-pandocfilters for the documentation consolidation, and
- sqlite3-tools for exploring and validating the results.


```console

$ sudo apt install gcc pkg-config sqlite3 libsqlite3-dev libsqlite3-0 \
       curl pyinstaller sqlite3-tools pandoc python3-pandocfilters
$ curl -LsSf https://astral.sh/uv/install.sh | sh

```

Note that the Astral installer does not run as root, and is only
available to the installing user in ~/.local/bin/. You should 
restart your terminal session after installing UV to be sure that
your environment includes ~/.local/bin in your $PATH.

## Setting up your Python working environment

```console
# After cloning this respository and cd'ing into its working directory:

$ uv venv                            # once, to create virtual environment
$ source .venv/bin/activate          # to activate the environment each time you start work
$ uv sync                            # to install packages (only needed once)
$ python -m selfconv -h              # each time you want to run the script
```


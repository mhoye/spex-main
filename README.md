# SPEX: SQLite Packaged Executables.

Complexity is a barrier to intention.

In late 2026, Faride Zakaria introduced the **SELF** file, the 
*Structured Executable & Linkable Format*: an SQLite based alternative 
to standard ELF files, including the binfmt_misc machinery required to
run those SELF files on Linux and NixOS. 

SQLite Packaged Executables - SPEX files - take that idea a step
further, integrating information from package managers, documentation
and other executable-adjacent resources to create a unified software
package that is trivial to deploy, explore and audit. 

As well - by taking advantage of the capabilities of SQLite - this
project has two other goals. First, this approach lets us replace a 
set of difficult-to-understand, high-complexity tools with much simpler 
and more easily legible and auditable programs and processes. 

Second - and more importantly - this approach will let creative
developers easily include other useful tools or expressive works 
with the software they ship.

# The longer story.

In a small part of a much longer set of discussions about coding
style and techniques, John Carmack of ID fame (among many other
things) has suggested that "... [If the work is close to purely
functional](https://cbarrete.com/carmack.html), with few references
to global state, try to make it completely functional."

I was thinking of this, and remembering [Greenspun's Tenth
Rule](https://en.wikipedia.org/wiki/Greenspun's_tenth_rule), that
"any sufficiently complicated C or Fortran program contains an ad
hoc, informally-specified, bug-ridden, slow implementation of half
of Common Lisp" - when Zakaria introduced his work.

In terms of the platonic ideal shapes and structures of computer science
the state machines, functional approaches, databases, and so on, these
two ideas resonate.

Should Carmack's idea that if you're almost there consider going
all the way be elevated to a general principle? If something is most
of the way to Being A Thing, then should we as a matter of good
practice try to get it all the way to Being That Thing so that
we can leverage of all the research theory and benefits of That Thing?

And what if every sufficently complex data format is effectively 
an informally specified, bug-ridden, slow implementation of half of
a database? 

If that's the case, if an executable is already most of the way to
being a database, what does getting it all the way to being a
database get us? 

I think we can start answering that question by asking, what else 
do we have lying around next to our executables that's also almost 
a database?

The answer is: a lot.

If your data format is both an executable and a database, installers
barely exist; they're reduced to a download and a symlink. Entire 
toolchains become a small set of legible transactions. Strip(), like 
so many of the tools we use to inspect or modify binaries, stops 
is reduced from a multi-thousand-line exercise in processing hexadecimal
and turns into a single easily understood transaction. We can flatten 
the MxN arch/distro problem with per-arch binaries and per-distro packaging manifests built in, after compilation, the build step becomes transaction
that's not just easy to read and understand but trivial to audit. 

```console
$ file hello
hello: SQLite 3.x database, application id 0x53454c46, user version 1
$ ./hello
Hello, world!
$ sqlite3 hello 'SELECT soname FROM ldd'          # ldd, as a query
$ sqlite3 hello 'DELETE FROM sections; VACUUM'    # strip, as a transaction
$ ./hello                                         # still runs
Hello, world!
```
And data's just data; you can put anything else you want in there with it. 

Sample code, a whole VCS can come built-in. Community contributions,
alternative skins or themes... I mean, why not ship your art-project
software with the inspiring art, all baked into a single container 
that happens to be the thing you run?

While the analysis is pending, I don't think that this comes at the cost 
of ... much of anything. It might even be a performance win overall. 
There's a very modest startup cost to this approach, true, but SQLite
is wildly more reliable than reading or writing text-based data
formats off the metal and - somehow, incredibly - in many cases
[SQLite is 35% faster than
fopen()](https://www3.sqlite.org/matrix/fasterthanfs.html)!

Dr. Hipp has famously said that SQLite3 isn't competing with MySQL
or Postgres; it's competing with fopen().

So what happens if we ... let SQLite win?

# Background 

Zakaria's earlier work in this space -
[sqlelf](https://github.com/fzakaria/sqlelf)
([arXiv:2405.03883](https://arxiv.org/abs/2405.03883)) - introduced
the idea of interrogating the structure of executables via SQL.
SPEX branches off from his subsequent work, turning that idea on
its head; the rows of the database becoming the executable format,
by providing a  a `binfmt_misc` interpreter to execute them on top
of a nixpkgs/NixOS slice.

This project has changed foundations from the nix/guix environment
to Debian Trixie.

# Developing.

This section assumes you're starting from a generally standard
installation of Debian Trixie, like the author. "Works On My Machine",
isn't great, but it's where this project is right now.

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

## Wayfinding - TODO: update/correct this.

- `selfconv/` — the `self` CLI (subcommands include `elf2self`) and `self2elf` (Python + LIEF).
- `loader/` — `self-exec`, the binfmt interpreter, with three modes:
  `memfd` (rebuild ELF → `execveat`), `native` (map segments + hand off to
  ld.so), `selfld` (be the dynamic linker, bind via SQL). Plus
  `libself-audit.so`, an `LD_AUDIT` library that makes **stock glibc** load
  `.self` shared libraries resolved through SQL.
- `nix/` — packages, a `selfify` hook, a NixOS module (`programs.self`), and
  `self-vm`.
- `schema/self.sql` — the format DDL (generated from `selfconv/schema.py`).
- `examples/server/` — **self-httpd**: a webserver whose pages, program and
  visitor log are one file. It opens `argv[0]` as a database and serves out of
  its own `routes` table; editing the live site is an `UPDATE`. Live at
  <https://selfdb.exe.xyz>.
- `bench/`, `tests/` — the evaluation harness and the test suite.

Read [DESIGN.md](./DESIGN.md); §13 tracks implementation status.


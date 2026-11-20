"""deb2spex: unpack a Debian .deb and convert its ELF binaries to SPEX.

Usage: python -m selfconv.deb2spex <package.deb> [--out DIR]

Reads a .deb (an `ar` archive holding `debian-binary`, `control.tar.*` and
`data.tar.*`), extracts the control and data tarballs to a temporary
directory, converts each ELF under usr/bin with elf2spex.convert (imported,
not a subprocess), then stores the Debian `control` fields in each database's
`package` table.

The .deb is assumed already downloaded; this script does not fetch it.
"""

import argparse
import os
import sqlite3
import sys
import tarfile
import tempfile

from .elf2spex import convert as elf2spex_convert

AR_MAGIC = b"!<arch>\n"
ELF_MAGIC = b"\x7fELF"


def _read_ar_members(deb_path: str):
    """Yield (name, bytes) for each member of the `ar` archive at deb_path."""
    with open(deb_path, "rb") as f:
        if f.read(8) != AR_MAGIC:
            raise ValueError(f"{deb_path}: not an ar archive (is it a .deb?)")
        while True:
            header = f.read(60)
            if len(header) < 60:
                break
            # ar file header: name[16] mtime[12] uid[6] gid[6] mode[8]
            #                 size[10] fmag[2] ("`\n")
            name = header[0:16].decode("ascii", "replace").rstrip("\x00 /")
            size = int(header[48:58].decode("ascii", "replace").strip() or "0")
            data = f.read(size)
            if size % 2:
                f.read(1)  # members are 2-byte aligned
            if name:
                yield name, data


def _tar_mode(name: str) -> str:
    if name.endswith(".xz"):
        return "r:xz"
    if name.endswith(".gz"):
        return "r:gz"
    if name.endswith(".bz2"):
        return "r:bz2"
    raise ValueError(
        f"{name}: unsupported compression (zstd .deb members are not supported)")


def _extract_tar(data: bytes, dest: str, name: str, tmpdir: str) -> None:
    tar_path = os.path.join(tmpdir, name)
    with open(tar_path, "wb") as f:
        f.write(data)
    with tarfile.open(tar_path, mode=_tar_mode(name)) as t:
        # filter="data" blocks absolute paths and ../ escapes (Python 3.12+).
        t.extractall(dest, filter="data")


def _parse_control(text: str) -> dict[str, str]:
    """Parse Debian control (RFC822-style) fields, joining continuations."""
    fields: dict[str, str] = {}
    current = None
    for line in text.splitlines():
        if not line.strip():
            continue
        if line[0] in (" ", "\t") and current is not None:
            fields[current] += "\n" + line.strip()
        elif ":" in line:
            key, _, value = line.partition(":")
            current = key.strip()
            fields[current] = value.strip()
    return fields


def _is_elf(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(4) == ELF_MAGIC
    except OSError:
        return False


def _add_package(spex_path: str, fields: dict[str, str]) -> None:
    con = sqlite3.connect(spex_path)
    con.executemany(
        "INSERT INTO package (field, value) VALUES (?,?)", fields.items())
    con.commit()
    con.close()


def _parse_depends(text: str) -> list[tuple[str, str | None]]:
    """Parse a Debian Depends field into (dependency, version) pairs.

    Splits on ',' and '|' (alternatives), then for each entry splits an
    optional "(op version)" constraint from the package name. `version` is
    the descriptor text (e.g. ">= 2.34") or None when there is no constraint.
    """
    rows = []
    for entry in text.replace("|", ",").split(","):
        entry = " ".join(entry.split())
        if not entry:
            continue
        name, version = entry, None
        if "(" in entry and entry.endswith(")"):
            name, rest = entry.split("(", 1)
            version = rest[:-1].strip() or None
        rows.append((name.strip(), version))
    return rows


def _add_depends(spex_path: str, depends_text: str) -> None:
    con = sqlite3.connect(spex_path)
    con.executemany(
        "INSERT INTO depends (dependency, version) VALUES (?,?)",
        _parse_depends(depends_text))
    con.commit()
    con.close()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="deb2spex", description=__doc__)
    ap.add_argument("deb", help="path to a downloaded .deb file")
    ap.add_argument("-o", "--out", default=".",
                    help="directory for the .spex files (default: .)")
    args = ap.parse_args(argv)

    with tempfile.TemporaryDirectory() as tmp:
        members = dict(_read_ar_members(args.deb))
        control_name = next((n for n in members if n.startswith("control.tar")), None)
        data_name = next((n for n in members if n.startswith("data.tar")), None)
        if control_name is None or data_name is None:
            print(f"{args.deb}: missing control.tar.* or data.tar.* member",
                  file=sys.stderr)
            return 1

        control_dir = os.path.join(tmp, "control")
        data_dir = os.path.join(tmp, "data")
        os.makedirs(control_dir)
        os.makedirs(data_dir)
        _extract_tar(members[control_name], control_dir, control_name, tmp)
        _extract_tar(members[data_name], data_dir, data_name, tmp)

        control_path = os.path.join(control_dir, "control")
        with open(control_path, encoding="utf-8", errors="replace") as f:
            fields = _parse_control(f.read())

        os.makedirs(args.out, exist_ok=True)
        bin_dir = os.path.join(data_dir, "usr", "bin")
        if not os.path.isdir(bin_dir):
            print(f"{args.deb}: no usr/bin in data.tar; nothing to convert",
                  file=sys.stderr)
            return 0

        for entry in sorted(os.listdir(bin_dir)):
            elf_path = os.path.join(bin_dir, entry)
            if not os.path.isfile(elf_path) or not _is_elf(elf_path):
                continue
            out_path = os.path.join(args.out, entry + ".spex")
            elf2spex_convert(elf_path, out_path)
            _add_package(out_path, fields)
            if "Depends" in fields:
                _add_depends(out_path, fields["Depends"])
            print(f"{entry} -> {out_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Publish a freshly built pvr.eon zip into this repository's catalog.

Usage: publish_pvr_eon.py <path-to-pvr.eon-VERSION.zip>

Runs create_repository.py against the zip (alongside the unchanged
repository.eon source, since create_repository.py only lists whatever
add-ons are passed to it), archives an android-armv7 copy into source/,
prunes to the last KEEP published versions, and rewrites the hand-written
index.html listings that make "Install from zip file" browsable (GitHub
Pages' Jekyll rendering can't produce real directory listings; see the
README's ".nojekyll" section).
"""
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET

KEEP = 5
REPO_ROOT = pathlib.Path(__file__).resolve().parent
ADDON_DIR = REPO_ROOT / "pvr.eon"
SOURCE_DIR = REPO_ROOT / "source"


def addon_version(zip_path):
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if name.endswith("addon.xml"):
                return ET.fromstring(zf.read(name)).get("version")
    raise RuntimeError(f"No addon.xml found in {zip_path}")


def version_key(v):
    return tuple(int(p) for p in v.split("."))


def prune(directory, pattern, keep=KEEP):
    versions = sorted(
        {m.group(1) for f in directory.iterdir() if (m := pattern.match(f.name))},
        key=version_key,
        reverse=True,
    )
    for old in versions[keep:]:
        for f in directory.glob(f"*{old}*"):
            f.unlink()
    return versions[:keep]


def rewrite_pvr_eon_index(kept_versions):
    lines = [
        "<!DOCTYPE html>",
        "<html>",
        "<head><title>Index of /pvr.eon/</title></head>",
        "<body>",
        "<h1>Index of /pvr.eon/</h1>",
        "<pre>",
        '<a href="addon.xml">addon.xml</a>',
    ]
    for i, v in enumerate(kept_versions):
        tag = "" if i == 0 else " (previous version)"
        if i == 0:
            lines += [
                f'<a href="changelog-{v}.txt">changelog-{v}.txt</a>',
                '<a href="icon.png">icon.png</a>',
                '<a href="fanart.jpg">fanart.jpg</a>',
                '<a href="LICENSE.txt">LICENSE.txt</a>',
            ]
        else:
            lines.append(f'<a href="changelog-{v}.txt">changelog-{v}.txt{tag}</a>')
        lines.append(f'<a href="pvr.eon-{v}.zip">pvr.eon-{v}.zip{tag}</a>')
        lines.append(f'<a href="pvr.eon-{v}.zip.md5">pvr.eon-{v}.zip.md5{tag}</a>')
    lines += ["</pre>", "</body>", "</html>", ""]
    (ADDON_DIR / "index.html").write_text("\n".join(lines))


def main():
    if len(sys.argv) != 2:
        sys.exit(f"Usage: {sys.argv[0]} <path-to-pvr.eon-VERSION.zip>")
    zip_path = pathlib.Path(sys.argv[1]).resolve()
    version = addon_version(zip_path)
    print(f"Publishing pvr.eon {version}")

    SOURCE_DIR.mkdir(exist_ok=True)
    (SOURCE_DIR / f"pvr.eon.{version}.android.armv7.zip").write_bytes(zip_path.read_bytes())

    # create_repository.py re-zips whatever it's pointed at, so pass a clean
    # copy of repository.eon's *source* (no previously built zip/md5 inside)
    # rather than the live folder, or each run would nest the prior zip
    # inside the new one.
    with tempfile.TemporaryDirectory() as tmp:
        repo_eon_src = pathlib.Path(tmp) / "repository.eon"
        shutil.copytree(
            REPO_ROOT / "repository.eon",
            repo_eon_src,
            ignore=shutil.ignore_patterns("*.zip", "*.zip.md5"),
        )
        subprocess.run(
            [sys.executable, "create_repository.py", "--datadir=.", "--no-parallel",
             str(zip_path), str(repo_eon_src)],
            cwd=REPO_ROOT,
            check=True,
        )

    kept = prune(ADDON_DIR, re.compile(r"^pvr\.eon-([0-9.]+)\.zip$"))
    prune(SOURCE_DIR, re.compile(r"^pvr\.eon\.([0-9.]+)\.android\.armv7\.zip$"))
    rewrite_pvr_eon_index(kept)
    print(f"Kept versions: {kept}")


if __name__ == "__main__":
    main()

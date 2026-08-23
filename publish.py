#!/usr/bin/env python3
"""Publish this repository's full add-on catalog from source.

create_repository.py rewrites addons.xml from ONLY the add-ons passed on
its command line, so every publish must pass every add-on we ever want
listed -- a run that publishes just one add-on would silently drop the
others out of the catalog. ADDONS below is that single source of truth;
running this script with no arguments re-emits the whole catalog from
current sources, and passing --pvr-zip additionally ingests a freshly
built pvr.eon release.

Usage:
    publish.py                                  # re-emit catalog as-is
    publish.py --pvr-zip /path/to/pvr.eon-X.Y.Z.zip
"""
import argparse
import contextlib
import hashlib
import dataclasses
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

REPO_ROOT = pathlib.Path(__file__).resolve().parent
SOURCE_DIR = REPO_ROOT / "source"

ASSET_ORDER = ("addon.xml", "icon.png", "fanart.jpg", "LICENSE.txt")


@dataclasses.dataclass
class Addon:
    id: str
    keep: int
    locate: "callable"  # (args) -> pathlib.Path (a folder or a zip file)
    ignore: tuple = ()  # shutil.ignore_patterns() patterns, folders only


def version_key(v):
    """Sort key for 'MAJOR.MINOR.PATCH[-~+SUFFIX]' versions, newest first
    with reverse=True. A prerelease sorts just below its matching final
    release rather than crashing int() on the suffix."""
    core = re.split(r"[-~+]", v, 1)[0]
    is_final = core == v
    return tuple(int(p) for p in core.split(".")) + (1 if is_final else 0,)


def locate_repository_eon(args):
    return REPO_ROOT / "repository.eon"


def locate_skin_eon(args):
    return REPO_ROOT / "src" / "skin.eon"


def _pvr_source_version(path):
    m = re.match(r"^pvr\.eon\.(.+)\.android\.armv7\.zip$", path.name)
    return m.group(1) if m else None


def locate_pvr_eon(args):
    if args.pvr_zip:
        zip_path = pathlib.Path(args.pvr_zip).expanduser().resolve()
        version = addon_version(zip_path)
        SOURCE_DIR.mkdir(exist_ok=True)
        archived = SOURCE_DIR / f"pvr.eon.{version}.android.armv7.zip"
        if not archived.exists():
            archived.write_bytes(zip_path.read_bytes())
        return zip_path
    candidates = [
        p for p in SOURCE_DIR.glob("pvr.eon.*.android.armv7.zip")
        if _pvr_source_version(p)
    ]
    if not candidates:
        sys.exit("No pvr.eon zip in source/ and no --pvr-zip given")
    return max(candidates, key=lambda p: version_key(_pvr_source_version(p)))


# Every entry here is passed to create_repository.py on EVERY run. Adding
# an add-on: append it here. Nothing else needs to change to keep it in
# the published catalog going forward.
ADDONS = [
    Addon(id="repository.eon", keep=2, locate=locate_repository_eon,
          ignore=("*.zip", "*.zip.md5")),
    Addon(id="pvr.eon", keep=5, locate=locate_pvr_eon),
    # The skin is built from source in src/skin.eon (a candidate for its own
    # repository later); skin.eon/ holds only what gets published. tools/ is
    # developer scripts, not part of the add-on.
    Addon(id="skin.eon", keep=2, locate=locate_skin_eon,
          ignore=("tools", "__pycache__", "*.zip", "*.zip.md5")),
]


def addon_version(location):
    if location.is_dir():
        return ET.parse(location / "addon.xml").getroot().get("version")
    import zipfile
    with zipfile.ZipFile(location) as zf:
        for name in zf.namelist():
            if name.endswith("addon.xml"):
                return ET.fromstring(zf.read(name)).get("version")
    raise RuntimeError(f"No addon.xml found in {location}")


def prepare_location(addon, args, stack):
    """Resolve an Addon's source to a path safe to hand to
    create_repository.py -- for folders, that means a clean tempdir copy
    with build/VCS cruft stripped, since fetch_addon_from_folder() zips
    everything under the folder with no ignore list of its own."""
    location = addon.locate(args)
    if location.is_dir() and addon.ignore:
        tmp = pathlib.Path(stack.enter_context(tempfile.TemporaryDirectory()))
        dest = tmp / addon.id
        shutil.copytree(location, dest, ignore=shutil.ignore_patterns(*addon.ignore))
        return dest
    return location


def normalise_catalog():
    """Re-indent addons.xml and refresh its checksum.

    create_repository.py appends each add-on's addon.xml verbatim, so the
    catalog inherits whatever indentation each source file used and gets no
    line break between </addon> and the next <addon>. Kodi does not care, but
    anyone reading the file does -- and the checksum has to be recomputed
    afterwards, because that is what devices compare against.
    """
    path = REPO_ROOT / "addons.xml"
    tree = ET.parse(path)
    ET.indent(tree, space="  ")
    tree.write(path, encoding="UTF-8", xml_declaration=True)
    digest = hashlib.md5(path.read_bytes()).hexdigest()
    # Same layout as create_repository.py's generate_checksum() for a text file.
    with open(REPO_ROOT / "addons.xml.md5", "w", newline="\n") as fh:
        fh.write(f"{digest}  addons.xml\n")
    print(f"addons.xml: re-indented, md5 {digest}")


def prune(addon):
    """Delete this add-on's published files beyond the last `keep`
    versions. Returns the kept versions, newest first."""
    directory = REPO_ROOT / addon.id
    if not directory.is_dir():
        return []
    pattern = re.compile(rf"^{re.escape(addon.id)}-(.+)\.zip$")
    versions = sorted(
        {m.group(1) for f in directory.iterdir() if (m := pattern.match(f.name))},
        key=version_key,
        reverse=True,
    )
    for old in versions[addon.keep:]:
        for name in (f"{addon.id}-{old}.zip", f"{addon.id}-{old}.zip.md5",
                     f"changelog-{old}.txt"):
            (directory / name).unlink(missing_ok=True)
    return versions[:addon.keep]


def prune_pvr_source(kept_versions):
    if not SOURCE_DIR.is_dir():
        return
    keep = set(kept_versions)
    for f in list(SOURCE_DIR.glob("pvr.eon.*.android.armv7.zip")):
        version = _pvr_source_version(f)
        if version is not None and version not in keep:
            f.unlink()


def rewrite_index(addon_id, kept_versions):
    directory = REPO_ROOT / addon_id
    lines = [
        "<!DOCTYPE html>", "<html>",
        f"<head><title>Index of /{addon_id}/</title></head>",
        "<body>", f"<h1>Index of /{addon_id}/</h1>", "<pre>",
        '<a href="addon.xml">addon.xml</a>',
    ]
    for asset in ("icon.png", "fanart.jpg", "LICENSE.txt"):
        if (directory / asset).exists():
            lines.append(f'<a href="{asset}">{asset}</a>')
    for i, v in enumerate(kept_versions):
        tag = "" if i == 0 else " (previous version)"
        changelog = f"changelog-{v}.txt"
        if (directory / changelog).exists():
            lines.append(f'<a href="{changelog}">{changelog}{tag}</a>')
        lines.append(f'<a href="{addon_id}-{v}.zip">{addon_id}-{v}.zip{tag}</a>')
        lines.append(f'<a href="{addon_id}-{v}.zip.md5">{addon_id}-{v}.zip.md5{tag}</a>')
    lines += ["</pre>", "</body>", "</html>", ""]
    (directory / "index.html").write_text("\n".join(lines))


def rewrite_root_index(repo_eon_version):
    lines = [
        "<!DOCTYPE html>", "<html>",
        "<head><title>Index of /</title></head>",
        "<body>", "<h1>Index of /</h1>", "<pre>",
        f'<a href="repository.eon-{repo_eon_version}.zip">'
        f'repository.eon-{repo_eon_version}.zip</a>',
        '<a href="addons.xml">addons.xml</a>',
        '<a href="addons.xml.md5">addons.xml.md5</a>',
    ]
    for addon in ADDONS:
        if addon.id != "repository.eon":
            lines.append(f'<a href="{addon.id}/">{addon.id}/</a>')
    lines += ["</pre>", "</body>", "</html>", ""]
    (REPO_ROOT / "index.html").write_text("\n".join(lines))

    for old in REPO_ROOT.glob("repository.eon-*.zip"):
        if old.name != f"repository.eon-{repo_eon_version}.zip":
            old.unlink()
    for old in REPO_ROOT.glob("repository.eon-*.zip.md5"):
        if old.name != f"repository.eon-{repo_eon_version}.zip.md5":
            old.unlink()
    shutil.copyfile(REPO_ROOT / "repository.eon" / f"repository.eon-{repo_eon_version}.zip",
                     REPO_ROOT / f"repository.eon-{repo_eon_version}.zip")
    shutil.copyfile(REPO_ROOT / "repository.eon" / f"repository.eon-{repo_eon_version}.zip.md5",
                     REPO_ROOT / f"repository.eon-{repo_eon_version}.zip.md5")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pvr-zip", help="Path to a freshly built pvr.eon zip to publish")
    args = parser.parse_args()

    with contextlib.ExitStack() as stack:
        locations = [str(prepare_location(a, args, stack)) for a in ADDONS]
        subprocess.run(
            [sys.executable, "create_repository.py", "--datadir=.", "--no-parallel",
             *locations],
            cwd=REPO_ROOT, check=True,
        )

    normalise_catalog()

    for addon in ADDONS:
        kept = prune(addon)
        rewrite_index(addon.id, kept)
        print(f"{addon.id}: kept {kept}")
        if addon.id == "pvr.eon":
            prune_pvr_source(kept)

    repo_eon_version = ET.parse(REPO_ROOT / "repository.eon" / "addon.xml").getroot().get("version")
    rewrite_root_index(repo_eon_version)


if __name__ == "__main__":
    main()

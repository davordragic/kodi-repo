# EON Add-on Repository

A personal Kodi add-on repository, served via GitHub Pages at:

**https://davordragic.github.io/kodi-repo**

## What's in here

| Add-on | Description |
|---|---|
| [`pvr.eon`](pvr.eon) | EON.tv PVR client (live TV, EPG, replay/catchup) |
| [`skin.eon`](skin.eon) | EON skin -- a minimal, PVR-first interface built to pair with it |

Check the current live version at any time:
- Full catalog: https://davordragic.github.io/kodi-repo/addons.xml
- Checksum only: https://davordragic.github.io/kodi-repo/addons.xml.md5

## Installing on Kodi (once, per device)

This installs the **repository** add-on itself, which then lets Kodi discover
and update everything listed above. Do this on the actual device (e.g. your
Android TV), not on this machine.

1. **Enable installs from zip files**
   Settings → System → Add-ons → turn on **"Unknown sources"** (confirm the warning).

2. **Add this repo as a file source**
   Settings → Media → File manager → **Add source** → enter:
   `https://davordragic.github.io/kodi-repo/`
   Give it any name, e.g. `eon-repo`.

3. **Install the repository add-on from the zip**
   Add-ons → the box icon (bottom left) → **Install from zip file** → select
   the `eon-repo` source → `repository.eon-1.0.2.zip`.
   Wait for the "Add-on installed" notification.

4. **Install add-ons from the repository**
   Add-ons → the box icon → **Install from repository** → **EON Add-on
   Repository** → PVR clients → **EON PVR Client** → **Install**.

5. **Configure the EON PVR Client**
   Open its settings and fill in: service provider, username, password, and
   platform (leave as default unless told otherwise). Then enable it under
   Settings → Player → TV.

   **For seeking/rewind (live TV and replay/catchup) to work**, set
   **"Select Inputstream"** to **`inputstream.ffmpegdirect`** (it defaults to
   `inputstream.adaptive`, which doesn't support seeking with this add-on).
   Make sure the `inputstream.ffmpegdirect` add-on is installed and enabled
   too (Kodi should offer to install it automatically when you switch to it).

6. **Optional: install the EON skin**
   Add-ons → the box icon → **Install from repository** → **EON Add-on
   Repository** → **Look and feel** → **Skin** → **EON** → **Install**, then
   confirm "Keep this skin?" when Kodi switches to it.

   It is a small live-TV-first skin: the home screen is the channel list with
   a live preview and now/next info, the guide is Kodi's own EPG grid, and the
   accent colour is switchable under Settings → Interface → Skin →
   **Colours** (teal, blue, amber, violet). Channel numbers, logos, the
   progress bars and the clock can each be turned off for slower boxes under
   Settings → **Skin settings**.

   To go back to the stock skin: Settings → Interface → Skin → Estuary.

## Getting updates / auto-update

Kodi periodically checks `addons.xml` on its own and installs updates for
anything from this repository — no need to repeat the install steps above.
Whether that happens *automatically* vs. just *notifying* you is a **Kodi
device setting**, not something a repository can force from the server side:

- Settings → Add-ons → **"Update add-ons automatically"** — set to "Install
  updates automatically" (this is Kodi's default; check it hasn't been
  changed to "notify only" or "never").
- You can also check per-add-on: Add-ons → My add-ons → PVR clients → EON PVR
  Client → the info panel has its own auto-update toggle, which should be on.

To check immediately instead of waiting for the periodic check:
- Add-ons → My add-ons → PVR clients → EON PVR Client → **Check for update**,
  or restart Kodi, or Settings → Add-ons → **"Check for updates"**.

## Publishing an update (maintainer notes)

`publish.py` is the entry point and always re-emits the **whole** catalog
(`repository.eon`, `pvr.eon`, `skin.eon`), because `create_repository.py`
rewrites `addons.xml` from only the add-ons it is given -- publishing one
add-on on its own would silently drop the others:

```
python3 publish.py                                   # re-emit catalog as-is
python3 publish.py --pvr-zip ~/pvr.eon-21.8.5.zip    # ingest a new pvr.eon build
```

The skin's source lives in its own folder **next to this repository**, at
`../skin.eon`, laid out as a skin repository in its own right so it can be
split out entirely later -- the same arrangement `pvr.eon`'s source has. So
nothing in this repository is a working copy of the skin: `skin.eon/` here
holds only published files, the same as `pvr.eon/`. `publish.py` reads the
source from that sibling folder and stops with a clear message if it is
missing.

To release a skin change, bump `version` in `../skin.eon/addon.xml`, add an
entry at the top of `../skin.eon/changelog.txt`, then run `publish.py`. It
zips the source (skipping `tools/`), writes
`skin.eon/skin.eon-<version>.zip` + `.md5`, copies the changelog and rewrites
`addons.xml` / `addons.xml.md5` and the `index.html` listings.

Before publishing a skin change, run its two dev scripts from `../skin.eon/`:

```
python3 tools/validate.py [path/to/kodi/en_gb/strings.po]   # static checks
python3 tools/make_textures.py                             # regenerate media/
```

`validate.py` is the substitute for a Kodi run: it resolves every include,
texture, font, colour, variable, constant and `$LOCALIZE` id, because Kodi
fails soft on all of those (a typo just leaves part of the screen blank).
`make_textures.py` regenerates every PNG in `../skin.eon/media/`, plus
`icon.png` and `fanart.png`, from the vector definitions in that script -- the
artwork is never hand-edited.

### Forcing a full re-sync on already-installed devices

If you ever need every device to re-fetch the whole repository (not just pick
up a new add-on version), bump `repository.eon`'s own `version` in
`repository.eon/addon.xml` and run `publish.py`. Kodi treats a version bump of
the repository add-on itself as a reason to re-fetch and re-parse everything
from scratch, which a same-version content edit alone does not reliably
trigger.

### Why there's a `.nojekyll` file and hand-written `index.html` files

GitHub Pages runs everything through Jekyll by default, which auto-renders
`README.md` as the site's `index.html` if no other index file exists — that
replaces the real file listing with rendered prose that has no genuine links,
which makes Kodi's HTTP directory browsing (Add source → Install from zip
file) show up empty. `.nojekyll` disables that, and the `index.html` files at
the root and in each add-on folder provide real `<a href>` listings that
Kodi's file manager can actually parse and browse. `publish.py` rewrites all
of them, so they never need editing by hand.

### Why the repository add-on is `repository.eon` (not `repository.davor`)

The previous `repository.davor.org` add-on ID got stuck: on both a fresh
Android TV and a fresh desktop install, Kodi would fetch `addons.xml`
successfully but consistently end up with zero add-ons parsed into its local
database for that repository ID — even after a full uninstall/reinstall.
Renaming to a fresh add-on ID (`repository.eon`) means Kodi has no prior
history at all for it, which sidesteps whatever cached/broken state that was
attached to the old ID.

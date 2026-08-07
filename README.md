# EON Kodi Repository

A personal Kodi add-on repository, served via GitHub Pages at:

**https://davordragic.github.io/kodi-repo**

## What's in here

| Add-on | Description |
|---|---|
| [`pvr.eon`](pvr.eon) | EON.tv PVR client (live TV, EPG, replay/catchup) |

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
   the `eon-repo` source → `repository.eon-1.0.0.zip`.
   Wait for the "Add-on installed" notification.

4. **Install add-ons from the repository**
   Add-ons → the box icon → **Install from repository** → **EON Kodi
   Repository** → PVR clients → **EON PVR Client** → **Install**.

5. **Configure the EON PVR Client**
   Open its settings and fill in: service provider, username, password, and
   platform (leave as default unless told otherwise). Then enable it under
   Settings → Player → TV.

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

1. Build the add-on (see `pvr.eon`'s own `README.md` / `tools/docker/*`) for
   the target platform(s).
2. From this repo's root, regenerate the catalog:
   ```
   python3 create_repository.py --datadir=. --no-parallel <path-to-built-addon-folder>
   ```
   This creates/updates `pvr.eon/pvr.eon-<version>.zip` (+ `.md5`), copies
   `changelog-<version>.txt`, and rewrites `addons.xml` / `addons.xml.md5`.
3. Commit and push to `main`. GitHub Pages redeploys automatically; there's
   no manual "publish" step beyond the push.
4. `addons.xml.md5` changing is the signal the update actually went live —
   check it at the URL above if in doubt.
5. Update the zip filename referenced in `pvr.eon/index.html` to match the
   new version. GitHub Pages doesn't generate real directory listings, so
   this hand-written `index.html` (and the root one) is what makes "Install
   from zip file" browsable in Kodi's file manager — see below.
6. If you ever need to force every device to fully re-sync the repository
   (not just get a new add-on version), bump `repository.eon`'s own
   `version` in `repository.eon/addon.xml`, rebuild its zip, and update the
   filename referenced in `index.html`. Kodi treats a version bump of the
   repository add-on itself as a reason to re-fetch and re-parse everything
   from scratch, which a same-version content edit alone does not reliably
   trigger on already-installed devices.

### Why there's a `.nojekyll` file and hand-written `index.html` files

GitHub Pages runs everything through Jekyll by default, which auto-renders
`README.md` as the site's `index.html` if no other index file exists — that
replaces the real file listing with rendered prose that has no genuine links,
which makes Kodi's HTTP directory browsing (Add source → Install from zip
file) show up empty. `.nojekyll` disables that, and `index.html` /
`pvr.eon/index.html` provide real `<a href>` listings that Kodi's file
manager can actually parse and browse.

### Why the repository add-on is `repository.eon` (not `repository.davor`)

The previous `repository.davor.org` add-on ID got stuck: on both a fresh
Android TV and a fresh desktop install, Kodi would fetch `addons.xml`
successfully but consistently end up with zero add-ons parsed into its local
database for that repository ID — even after a full uninstall/reinstall.
Renaming to a fresh add-on ID (`repository.eon`) means Kodi has no prior
history at all for it, which sidesteps whatever cached/broken state that was
attached to the old ID.

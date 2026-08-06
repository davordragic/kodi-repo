# Davor's Kodi Add-on Repository

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
and auto-update everything listed above. Do this on the actual device
(e.g. your Android TV), not on this machine.

1. **Enable installs from zip files**
   Settings → System → Add-ons → turn on **"Unknown sources"** (confirm the warning).

2. **Add this repo as a file source**
   Settings → Media → File manager → **Add source** → enter:
   `https://davordragic.github.io/kodi-repo/`
   Give it any name, e.g. `davor-repo`.

3. **Install the repository add-on from the zip**
   Add-ons → the box icon (bottom left) → **Install from zip file** → select
   the `davor-repo` source → `repository.davor-1.0.0.zip`.
   Wait for the "Add-on installed" notification.

4. **Install add-ons from the repository**
   Add-ons → the box icon → **Install from repository** → **Davor Add-on
   repository** → PVR clients → **EON PVR Client** → **Install**.

5. **Configure the EON PVR Client**
   Open its settings and fill in: service provider, username, password, and
   platform (leave as default unless told otherwise). Then enable it under
   Settings → Player → TV.

## Getting updates

Once the repository add-on is installed, Kodi periodically checks
`addons.xml` on its own and offers/auto-installs updates — no need to repeat
the steps above. To check immediately instead of waiting:

- Add-ons → My add-ons → PVR clients → EON PVR Client → **Check for update**,
  or just restart Kodi.

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

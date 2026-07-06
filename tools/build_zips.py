#!/usr/bin/env python3
"""Build Kodi addon zips (Unix paths) and refresh chaturbatetv-addons.xml.md5."""

from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def addon_version(addon_dir: Path) -> str:
    text = (addon_dir / 'addon.xml').read_text(encoding='utf-8')
    match = re.search(r'<addon[^>]*\bversion="([^"]+)"', text)
    if not match:
        raise SystemExit('addon version not found in {0}'.format(addon_dir / 'addon.xml'))
    return match.group(1)


def zip_addon_folder(addon_dir: Path, dest_zip: Path) -> None:
    addon_id = addon_dir.name
    with zipfile.ZipFile(dest_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(addon_dir.rglob('*')):
            if not path.is_file():
                continue
            arcname = '{0}/{1}'.format(addon_id, path.relative_to(addon_dir).as_posix())
            zf.write(path, arcname)
    print('wrote {0} ({1} bytes)'.format(dest_zip.name, dest_zip.stat().st_size))


def write_md5(xml_path: Path) -> None:
    digest = hashlib.md5(xml_path.read_bytes()).hexdigest()
    (ROOT / 'chaturbatetv-addons.xml.md5').write_text(digest, encoding='ascii')
    print('md5 {0}'.format(digest))


def main() -> None:
    plugin_dir = ROOT / 'plugin.video.chaturbate'
    repo_dir = ROOT / 'repository.chaturbatetv'

    plugin_ver = addon_version(plugin_dir)
    repo_ver = addon_version(repo_dir)

    zip_addon_folder(plugin_dir, ROOT / 'plugin.video.chaturbate-{0}.zip'.format(plugin_ver))
    zip_addon_folder(repo_dir, ROOT / 'repository.chaturbatetv-{0}.zip'.format(repo_ver))

    write_md5(ROOT / 'chaturbatetv-addons.xml')


if __name__ == '__main__':
    main()

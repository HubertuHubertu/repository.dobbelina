# -*- coding: utf-8 -*-
"""Install Dobbelina repository and optional dependencies from Kodi."""

import os

import xbmc
from kodi_six import xbmcaddon
from six.moves import urllib_parse

from resources.lib import utils
from resources.lib.basics import rootDir, TRANSLATEPATH
from resources.lib.url_dispatcher import URL_Dispatcher

url_dispatcher = URL_Dispatcher('utils')

REPO_ID = 'repository.dobbelina'
REPO_ZIP_NAME = 'repository.dobbelina-1.0.4.zip'
REPO_URL = 'https://dobbelina.github.io/{0}'.format(REPO_ZIP_NAME)

# Hard deps from addon.xml (Kodi should pull these on install; helper for manual repair)
HARD_DEPS = (
    'script.module.six',
    'script.module.kodi-six',
    'inputstream.adaptive',
    'script.module.inputstreamhelper',
)
OPTIONAL_DEPS = (
    'script.common.plugin.cache',
)


def _is_installed(addon_id):
    try:
        xbmcaddon.Addon(addon_id)
        return True
    except Exception:
        return False


def _bundled_repo_zip():
    return os.path.join(rootDir, 'resources', 'packages', REPO_ZIP_NAME)


@url_dispatcher.register()
def install_dobbelina_repo():
    if _is_installed(REPO_ID):
        utils.dialog.ok('ChaturbateTV', 'Dobbelina Repository is already installed.')
        return

    if not utils.dialog.yesno(
        'Dobbelina Repository',
        'Install Dobbelina Repository from dobbelina.github.io?[CR][CR]'
        'It provides dependency modules and add-on updates.[CR][CR]'
        'Confirm any Kodi security prompts.',
        nolabel='Cancel',
        yeslabel='Install',
    ):
        return

    local_zip = _bundled_repo_zip()
    if os.path.isfile(local_zip):
        target = TRANSLATEPATH(local_zip)
    else:
        target = REPO_URL

    try:
        if target.startswith('http'):
            xbmc.executebuiltin('InstallZip({0})'.format(urllib_parse.quote(target, safe='')))
        else:
            xbmc.executebuiltin('InstallZip({0})'.format(target))
        utils.dialog.ok(
            'ChaturbateTV',
            'Repository install started.[CR][CR]'
            'After it finishes: Add-ons → My add-ons → Download → Install from repository → Dobbelina.',
        )
    except Exception as exc:
        xbmc.log('ChaturbateTV repo install: {0}'.format(exc), xbmc.LOGERROR)
        utils.dialog.ok('ChaturbateTV', 'Could not start repository install. Try manually from https://dobbelina.github.io/')


@url_dispatcher.register()
def install_missing_deps():
    missing_hard = [aid for aid in HARD_DEPS if not _is_installed(aid)]
    missing_opt = [aid for aid in OPTIONAL_DEPS if not _is_installed(aid)]
    missing = missing_hard + missing_opt

    if not missing:
        utils.dialog.ok('ChaturbateTV', 'All dependencies are already installed.')
        return

    if not _is_installed(REPO_ID) and missing_opt:
        if utils.dialog.yesno(
            'Dependencies',
            'Some optional modules need Dobbelina Repository.[CR]Install it now?',
            nolabel='Skip',
            yeslabel='Install repo',
        ):
            install_dobbelina_repo()

    still_missing = [aid for aid in missing if not _is_installed(aid)]
    if not still_missing:
        return

    labels = ', '.join(still_missing)
    if not utils.dialog.yesno(
        'Install dependencies',
        'Install missing add-ons?[CR][CR]{0}'.format(labels),
        nolabel='Cancel',
        yeslabel='Install',
    ):
        return

    failed = []
    for addon_id in still_missing:
        try:
            xbmc.executebuiltin('InstallAddon({0})'.format(addon_id))
        except Exception:
            failed.append(addon_id)

    if failed:
        utils.dialog.ok(
            'ChaturbateTV',
            'Started install for most dependencies.[CR][CR]'
            'If something failed, install Dobbelina Repository first, then retry.[CR][CR]'
            'Failed: {0}'.format(', '.join(failed)),
        )
    else:
        utils.notify('ChaturbateTV', 'Dependency install started — confirm Kodi prompts if shown.')

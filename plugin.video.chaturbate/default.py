'''
    ChaturbateTV for Kodi
    Fork of Cumination (GPL 2.0) — Chaturbate module only
'''

import os.path
import sys
import socket
import traceback

from kodi_six import xbmc, xbmcplugin, xbmcaddon, xbmcvfs

from resources.lib import basics
from resources.lib.url_dispatcher import URL_Dispatcher
from resources.lib import utils
from resources.lib import favorites  # noqa: F401 — registers favorites.* modes
from resources.lib import repo_install  # noqa: F401 — repository / dependency install
from resources.lib import pin
from resources.lib import miami_theme as mt
from resources.lib.adultsite import AdultSite
from resources.lib.sites import chaturbate  # noqa: F401

socket.setdefaulttimeout(60)

addon = basics.addon
content = 'videos'
xbmcplugin.setContent(basics.addon_handle, content)
addon = xbmcaddon.Addon()
TRANSLATEPATH = xbmcvfs.translatePath
dialog = utils.dialog

url_dispatcher = URL_Dispatcher('main')


@url_dispatcher.register()
def INDEX():
    chaturbate.Main()


@url_dispatcher.register()
def about_site(name, about, custom):
    heading = '{0} {1}'.format(utils.i18n('about'), name)
    with open(TRANSLATEPATH(os.path.join(basics.aboutDir, '{}.txt'.format(about)))) as f:
        announce = f.read()
    utils.textBox(heading, announce)


def change():
    version = addon.getAddonInfo('version')
    if addon.getSetting('changelog_seen_version') == version or not os.path.isfile(basics.changelog):
        return
    addon.setSetting('changelog_seen_version', version)
    heading = '[B]{0} {1}[/B]'.format(mt.c(mt.CYAN, 'Chaturbate'), mt.c(mt.PINK, 'TV Changelog'))
    with open(basics.changelog) as f:
        cl_lines = f.readlines()
    announce = ''
    for line in cl_lines:
        if not line.strip():
            break
        announce += line
    utils.textBox(heading, announce)


def age_confirmed():
    if addon.getSetting('chaturbateage') == 'true':
        return True
    ok = dialog.yesno(
        utils.i18n('warn'), utils.i18n('warn_msg'),
        nolabel=utils.i18n('exit'), yeslabel=utils.i18n('enter')
    )
    if ok:
        addon.setSetting('chaturbateage', 'true')
    return ok


def process_queries(argv):
    argv = argv or sys.argv
    query = argv[2] if len(argv) > 2 else ''
    queries = utils.parse_query(query or '')
    mode = queries.get('mode', None)
    if not mode:
        mode = 'main.INDEX'
    widget = bool(queries.get('widget', ''))
    if widget:
        ins = AdultSite.get_site_by_name(mode.split('.')[0])
        if ins:
            ins.widget = True
    url_dispatcher.dispatch(mode, queries)


def main(argv=None):
    try:
        if not age_confirmed():
            return
        if not pin.CheckPin():
            return
        utils.refresh_assets_if_needed()
        change()
        if addon.getSetting('enh_debug') == 'true':
            from resources.lib import exception_logger
            with exception_logger.log_exception():
                process_queries(argv)
        else:
            process_queries(argv)
    except Exception:
        err = traceback.format_exc()
        xbmc.log('ChaturbateTV startup error:\n' + err, xbmc.LOGERROR)
        dialog.ok('ChaturbateTV', 'Startup error. Enable Debug in addon settings and check Kodi log.')


if __name__ == '__main__':
    main()

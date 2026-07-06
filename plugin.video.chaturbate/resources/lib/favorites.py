# -*- coding: utf-8 -*-
"""ChaturbateTV favorites — Chaturbate models only."""

import sqlite3
import datetime
import os
import json

import xbmc
import six
from kodi_six import xbmcaddon

from resources.lib import basics
from resources.lib import utils
from resources.lib import miami_theme as mt
from resources.lib.url_dispatcher import URL_Dispatcher
from resources.lib.adultsite import AdultSite

url_dispatcher = URL_Dispatcher('favorites')

dialog = utils.dialog
favoritesdb = basics.favoritesdb
FAV_MODE = 'chaturbate.Playvid'
LEGACY_MODES = frozenset((FAV_MODE, '222'))
BACKUP_TYPE = 'chaturbatetv-favorites'
LEGACY_BACKUP_TYPES = frozenset((BACKUP_TYPE, 'cumination-favorites', 'uwc-favorites'))

orders = {
    'random': 'RANDOM()',
    'date added': 'ROWID DESC',
    'name': 'NAME COLLATE NOCASE',
}

conn = sqlite3.connect(favoritesdb)
c = conn.cursor()
try:
    c.executescript(
        'CREATE TABLE IF NOT EXISTS favorites '
        '(name, url, mode, image, duration, quality);'
    )
    c.execute('PRAGMA table_info(favorites);')
    res = c.fetchall()
    if len(res) == 4:
        c.execute('ALTER TABLE favorites ADD COLUMN duration')
        c.execute('ALTER TABLE favorites ADD COLUMN quality')
except Exception:
    pass
conn.close()


def _is_cb_mode(mode):
    return str(mode) in LEGACY_MODES


def _normalize_mode(mode):
    return FAV_MODE if _is_cb_mode(mode) else None


@url_dispatcher.register()
def Refresh_images():
    utils.clear_cache()
    connfav = sqlite3.connect(favoritesdb)
    connfav.text_factory = str
    db_dir = utils.TRANSLATEPATH('special://database/')
    conn = None
    for db_name in os.listdir(db_dir) if os.path.isdir(db_dir) else []:
        if db_name.startswith('Textures') and db_name.endswith('.db'):
            conn = sqlite3.connect(os.path.join(db_dir, db_name))
            break
    if not conn:
        xbmc.executebuiltin('Container.Refresh')
        return
    c = connfav.cursor()
    c.execute('SELECT * FROM favorites WHERE mode = ?', (FAV_MODE,))
    for (_name, _url, _mode, img, _duration, _quality) in c.fetchall():
        try:
            with conn:
                rows = conn.execute(
                    'SELECT id, cachedurl FROM texture WHERE url = ?;', (img,)
                ).fetchall()
                for tex_id, cachedurl in rows:
                    conn.execute('DELETE FROM sizes WHERE idtexture = ?', (tex_id,))
                    if cachedurl:
                        try:
                            os.remove(utils.TRANSLATEPATH('special://thumbnails/' + cachedurl))
                        except OSError:
                            pass
                conn.execute("DELETE FROM texture WHERE url LIKE '%highwebmedia.com%';")
        except Exception:
            pass
    xbmc.executebuiltin('Container.Refresh')


@url_dispatcher.register()
def List(url=1):
    page = int(url)
    items_per_page = utils.addon.getSetting('item.limit')
    items_per_page = 1000000 if items_per_page == '0' else int(items_per_page)
    offset = (page - 1) * items_per_page
    favorder = utils.addon.getSetting('favorder') or 'date added'
    if favorder not in orders:
        favorder = 'date added'

    if page == 1:
        basics.addDir(
            mt.c(mt.ORANGE, utils.i18n('fav_refresh')), '', 'favorites.Refresh_images', mt.img('refresh'), Folder=False
        )
        basics.addDir(
            mt.c(mt.CYAN, utils.i18n('fav_sort').format(favorder)), '', 'favorites.Favorder', mt.img('list'), Folder=False
        )
        if utils.addon.getSetting('chaturbate') == 'true':
            for f in AdultSite.clean_functions:
                f(False)

    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    try:
        sql = (
            'SELECT name, url, mode, image, duration, quality FROM favorites '
            'WHERE mode = ? ORDER BY {} LIMIT ? OFFSET ?'
        ).format(orders[favorder])
        c.execute(sql, (FAV_MODE, items_per_page, offset))
        rows = c.fetchall()
        for (name, url, mode, img, duration, quality) in rows:
            duration = '' if duration is None else duration
            quality = '' if quality is None else quality
            basics.addDownLink(
                name, url, mode, img, desc='', stream='', fav='del', duration=duration, quality=quality
            )
        c.execute('SELECT COUNT(*) FROM favorites WHERE mode = ?', (FAV_MODE,))
        total_items = c.fetchone()[0]
        pages = max(1, (total_items - 1) // items_per_page + 1)
        if total_items > offset + items_per_page:
            basics.addDir(
                mt.c(mt.ORANGE, utils.i18n('fav_next').format(page + 1, pages)),
                str(page + 1), 'favorites.List', mt.img('next'),
            )
        conn.close()
        utils.eod(utils.addon_handle)
    except Exception:
        conn.close()
        utils.notify('ChaturbateTV', utils.i18n('fav_none'))


@url_dispatcher.register()
def Favorder():
    keys = list(orders.keys())
    idx = utils.selector('Sort favorites by', keys, sort_by=lambda x: x[1], show_on_one=False)
    if idx is not None:
        utils.addon.setSetting('favorder', keys[idx])
        xbmc.executebuiltin('Container.Refresh')


@url_dispatcher.register()
def Favorites(fav, favmode, name, url, img, duration='', quality=''):
    favmode = _normalize_mode(favmode) or FAV_MODE
    if fav == 'add':
        existing_favorite = select_favorite(url)
        if existing_favorite:
            if (
                existing_favorite[0] == name
                and existing_favorite[3] == img
                and existing_favorite[2] == favmode
                and existing_favorite[4] == duration
                and existing_favorite[5] == quality
            ):
                utils.notify('ChaturbateTV', utils.i18n('fav_already'))
            elif dialog.yesno(
                'ChaturbateTV',
                utils.i18n('fav_update_confirm').format(existing_favorite[0]),
            ):
                update_favorite(favmode, name, url, img, duration, quality)
                utils.notify('ChaturbateTV', utils.i18n('fav_updated'))
        else:
            addFav(favmode, name, url, img, duration, quality)
            utils.notify('ChaturbateTV', utils.i18n('fav_added'))
        return
    if fav == 'del':
        delFav(url)
        utils.notify('ChaturbateTV', utils.i18n('fav_removed'))
    elif fav == 'move_to_top':
        move_fav_to_top(url)
        utils.notify('ChaturbateTV', utils.i18n('fav_moved_top'))
    elif fav == 'move_down':
        move_fav_down(url)
        utils.notify('ChaturbateTV', utils.i18n('fav_moved_down'))
    elif fav == 'move_up':
        move_fav_up(url)
        utils.notify('ChaturbateTV', utils.i18n('fav_moved_up'))
    elif fav == 'move_to_bottom':
        move_fav_to_bottom(url)
        utils.notify('ChaturbateTV', utils.i18n('fav_moved_bottom'))
    xbmc.executebuiltin('Container.Refresh')


def select_favorite(url):
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute('SELECT name, url, mode, image, duration, quality FROM favorites WHERE url = ?', (url,))
    row = c.fetchone()
    conn.close()
    return row


def update_favorite(mode, name, url, img, duration, quality):
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()
    c.execute(
        'UPDATE favorites SET name=?, mode=?, image=?, duration=?, quality=? WHERE url=?',
        (name, mode, img, duration, quality, url),
    )
    conn.commit()
    conn.close()


def addFav(mode, name, url, img, duration, quality):
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()
    c.execute(
        'INSERT INTO favorites VALUES (?,?,?,?,?,?)',
        (name, url, mode, img, duration, quality),
    )
    conn.commit()
    conn.close()


def delFav(url):
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()
    c.execute('DELETE FROM favorites WHERE url = ?', (url,))
    conn.commit()
    conn.close()


def move_fav_to_top(url):
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()
    c.execute('SELECT name, url, mode, image, duration, quality FROM favorites WHERE url = ?', (url,))
    row = c.fetchone()
    if row:
        c.execute('DELETE FROM favorites WHERE url = ?', (url,))
        c.execute('INSERT INTO favorites VALUES (?,?,?,?,?,?)', row)
    conn.commit()
    conn.close()


def _all_favorites():
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute(
        'SELECT name, url, mode, image, duration, quality FROM favorites WHERE mode = ? ORDER BY rowid',
        (FAV_MODE,),
    )
    rows = c.fetchall()
    conn.close()
    return rows


def _rewrite_favorites(rows):
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()
    c.execute('DELETE FROM favorites WHERE mode = ?', (FAV_MODE,))
    for row in rows:
        c.execute('INSERT INTO favorites VALUES (?,?,?,?,?,?)', row)
    conn.commit()
    conn.close()


def move_fav_down(url):
    rows = _all_favorites()
    idx = next((i for i, r in enumerate(rows) if r[1] == url), None)
    if idx is None or idx >= len(rows) - 1:
        return
    rows[idx], rows[idx + 1] = rows[idx + 1], rows[idx]
    _rewrite_favorites(rows)


def move_fav_up(url):
    rows = _all_favorites()
    idx = next((i for i, r in enumerate(rows) if r[1] == url), None)
    if idx is None or idx <= 0:
        return
    rows[idx], rows[idx - 1] = rows[idx - 1], rows[idx]
    _rewrite_favorites(rows)


def move_fav_to_bottom(url):
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()
    c.execute('SELECT name, url, mode, image, duration, quality FROM favorites WHERE url = ?', (url,))
    row = c.fetchone()
    if row:
        c.execute('DELETE FROM favorites WHERE url = ?', (url,))
        c.execute('INSERT INTO favorites VALUES (?,?,?,?,?,?)', row)
    conn.commit()
    conn.close()


@url_dispatcher.register()
def clear_fav():
    if not dialog.yesno('ChaturbateTV', utils.i18n('fav_clear_confirm'), nolabel='No', yeslabel='Yes'):
        return
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()
    c.execute('DELETE FROM favorites WHERE mode = ?', (FAV_MODE,))
    conn.commit()
    conn.close()
    xbmc.executebuiltin('Container.Refresh')
    utils.notify('ChaturbateTV', utils.i18n('fav_cleared'))


@url_dispatcher.register()
def migrate_from_cumination():
    try:
        cum = xbmcaddon.Addon('plugin.video.cumination')
        src_profile = utils.TRANSLATEPATH(cum.getAddonInfo('profile'))
    except Exception:
        dialog.ok('ChaturbateTV', utils.i18n('migrate_no_cumination'))
        return

    if cum.getSetting('custom_favorites') == 'true':
        fav_path = cum.getSetting('favorites_path')
        src_db = os.path.join(utils.TRANSLATEPATH(fav_path or src_profile), 'favorites.db')
    else:
        src_db = os.path.join(src_profile, 'favorites.db')

    if not os.path.isfile(src_db):
        dialog.ok('ChaturbateTV', utils.i18n('migrate_no_db'))
        return

    if not dialog.yesno('ChaturbateTV', utils.i18n('migrate_confirm'), nolabel='Cancel', yeslabel='Migrate'):
        return

    imported = skipped = 0
    src = sqlite3.connect(src_db)
    src.text_factory = str
    cur = src.cursor()
    try:
        cur.execute('SELECT name, url, mode, image, duration, quality FROM favorites')
        rows = cur.fetchall()
    except sqlite3.OperationalError:
        cur.execute('SELECT name, url, mode, image FROM favorites')
        rows = [(n, u, m, i, '', '') for n, u, m, i in cur.fetchall()]

    for name, url, mode, img, duration, quality in rows:
        if not _is_cb_mode(mode):
            continue
        if select_favorite(url):
            skipped += 1
            continue
        addFav(FAV_MODE, name, url, img or '', duration or '', quality or '')
        imported += 1
    src.close()
    utils.notify('ChaturbateTV', utils.i18n('migrate_done').format(imported, skipped))


@url_dispatcher.register()
def import_from_cumination():
    migrate_from_cumination()


@url_dispatcher.register()
def backup_fav():
    path = utils.xbmcgui.Dialog().browseSingle(0, utils.i18n('bkup_dir'), 'myprograms')
    if not path:
        return
    progress = utils.progress
    progress.create(utils.i18n('backing_up'), utils.i18n('init'))
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute('SELECT * FROM favorites WHERE mode = ?', (FAV_MODE,))
    favorites = [
        {'name': name, 'url': url, 'mode': mode, 'img': img, 'duration': duration, 'quality': quality}
        for (name, url, mode, img, duration, quality) in c.fetchall()
    ]
    conn.close()
    if not favorites:
        progress.close()
        utils.notify('ChaturbateTV', utils.i18n('fav_no_backup'))
        return
    time = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    backup_content = {
        'meta': {'type': BACKUP_TYPE, 'version': 1, 'datetime': time},
        'data': favorites,
    }
    filename = 'chaturbatetv-favorites_{0}.bak'.format(time)
    compress = utils.addon.getSetting('compressbackup') == 'true'
    if not path.endswith('/') and not path.endswith('\\'):
        path = path + os.sep
    full_path = path + filename
    try:
        if compress:
            import gzip
            opener = gzip.open(full_path, 'wt', encoding='utf-8') if utils.PY3 else gzip.open(full_path, 'wb')
        else:
            opener = open(full_path, 'wt', encoding='utf-8') if utils.PY3 else open(full_path, 'wb')
        with opener as fav_file:
            json.dump(backup_content, fav_file)
    except IOError:
        progress.close()
        utils.notify('ChaturbateTV', utils.i18n('write_permission'))
        return
    progress.close()
    dialog.ok('ChaturbateTV', '{0}[CR]{1}'.format(utils.i18n('bkup_complete'), full_path))


@url_dispatcher.register()
def restore_fav():
    path = dialog.browseSingle(1, utils.i18n('slct_file'), 'myprograms')
    if not path:
        return
    compress = utils.addon.getSetting('compressbackup') == 'true'
    try:
        if compress:
            import gzip
            if utils.PY3:
                with gzip.open(path, 'rt', encoding='utf-8') as fav_file:
                    backup_content = json.load(fav_file)
            else:
                with gzip.open(path, 'rb') as fav_file:
                    backup_content = json.load(fav_file)
        else:
            if utils.PY3:
                with open(path, 'rt', encoding='utf-8') as fav_file:
                    backup_content = json.load(fav_file)
            else:
                with open(path, 'rb') as fav_file:
                    backup_content = json.load(fav_file)
    except (ValueError, IOError):
        utils.notify('ChaturbateTV', utils.i18n('invalid_bkup'))
        return

    meta_type = backup_content.get('meta', {}).get('type', '')
    if meta_type == 'uwc-favorites':
        from resources.lib.convertfav import convertfav
        backup_content = convertfav(backup_content)
    elif meta_type not in LEGACY_BACKUP_TYPES:
        utils.notify('ChaturbateTV', utils.i18n('invalid_bkup'))
        return

    favorites = backup_content.get('data') or []
    if not favorites:
        utils.notify('ChaturbateTV', utils.i18n('empty_bkup'))
        return

    added = skipped = 0
    for favorite in favorites:
        mode = _normalize_mode(favorite.get('mode'))
        if not mode:
            skipped += 1
            continue
        if select_favorite(favorite['url']):
            skipped += 1
            continue
        duration = favorite.get('duration') or ''
        quality = favorite.get('quality') or ''
        addFav(mode, favorite['name'], favorite['url'], favorite.get('img') or '', duration, quality)
        added += 1
    xbmc.executebuiltin('Container.Refresh')
    dialog.ok(
        utils.i18n('rstr_cmpl'),
        utils.i18n('rstr_msg').format(added, skipped),
    )

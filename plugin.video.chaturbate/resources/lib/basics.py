import os.path
import re
import sqlite3
import six
from six.moves import urllib_parse
import shutil
from kodi_six import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs
import os
import sys

__scriptname__ = "ChaturbateTV"
__author__ = "Cumination fork"
__scriptid__ = "plugin.video.chaturbate"

addon_handle = int(sys.argv[1])
addon_sys = sys.argv[0]
addon = xbmcaddon.Addon()
TRANSLATEPATH = xbmcvfs.translatePath if six.PY3 else xbmc.translatePath

rootDir = addon.getAddonInfo('path')
if rootDir[-1] == ';':
    rootDir = rootDir[0:-1]
rootDir = TRANSLATEPATH(rootDir)
resDir = os.path.join(rootDir, 'resources')
imgDir = os.path.join(resDir, 'images')
aboutDir = os.path.join(resDir, 'about')
profileDir = addon.getAddonInfo('profile')
profileDir = TRANSLATEPATH(profileDir)
cookiePath = os.path.join(profileDir, 'cookies.lwp')
if addon.getSetting('custom_favorites') == 'true':
    fav_path = addon.getSetting('favorites_path')
    if fav_path == '':
        fav_path = profileDir
    favoritesdb = os.path.join(fav_path, 'favorites.db')
else:
    favoritesdb = os.path.join(profileDir, 'favorites.db')
customSitesDir = os.path.join(profileDir, 'custom_sites')
tempDir = os.path.join(profileDir, 'temp')

addonicon = TRANSLATEPATH(os.path.join(rootDir, 'icon-chaturbatetv.png'))
if not os.path.isfile(addonicon):
    addonicon = TRANSLATEPATH(os.path.join(rootDir, 'icon.png'))
cuminationicon = addonicon
changelog = TRANSLATEPATH(os.path.join(rootDir, 'changelog.txt'))


if not os.path.exists(profileDir):
    os.makedirs(profileDir)

if not os.path.exists(customSitesDir):
    os.makedirs(customSitesDir)

if not os.path.exists(tempDir):
    os.makedirs(tempDir)

def _kodi_version():
    try:
        ver = xbmcaddon.Addon('xbmc.addon').getAddonInfo('version')
        m = re.match(r'[\d.]+', ver or '')
        return float((m.group(0) if m else '20.0')[:4])
    except Exception:
        return 20.0


KODIVER = _kodi_version()


def cum_image(filename, custom=False):
    if filename.startswith('http'):
        return filename
    else:
        img = os.path.join(customSitesDir if custom else imgDir, filename)
        return img


def eod(handle=addon_handle, cache=True):
    if addon.getSetting('customview') == 'true':
        skin = xbmc.getSkinDir().lower()
        viewtype = 55 if 'estuary' in skin else 50
        setview = addon.getSetting('setview')
        if ';' in setview:
            currentskin, viewno = setview.split(';')
            if currentskin == skin:
                viewtype = viewno
        xbmc.executebuiltin("Container.SetViewMode(%s)" % str(viewtype))
    xbmcplugin.endOfDirectory(handle, cacheToDisc=cache)


def addImgLink(name, url, mode):
    u = (sys.argv[0]
         + "?url=" + urllib_parse.quote_plus(url)
         + "&mode=" + str(mode)
         + "&name=" + urllib_parse.quote_plus(name))
    liz = xbmcgui.ListItem(name)
    if KODIVER < 19.8:
        liz.setInfo(type='pictures', infoLabels={'title': name})
    liz.setArt({'thumb': url, 'icon': url, 'poster': url})
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz, isFolder=False)
    return ok


def addDownLink(name, url, mode, iconimage, desc='', stream=None, fav='add', noDownload=False, contextm=None, fanart=None, duration='', quality=''):
    contextMenuItems = []
    favtext = "Remove from" if fav == 'del' else "Add to"  # fav == 'add' or 'del'
    dname = desc == name
    u = (sys.argv[0]
         + "?url=" + urllib_parse.quote_plus(url)
         + "&mode=" + str(mode)
         + "&name=" + urllib_parse.quote_plus(name))
    dwnld = (sys.argv[0]
             + "?url=" + urllib_parse.quote_plus(url)
             + "&mode=" + str(mode)
             + "&download=" + str(1)
             + "&name=" + urllib_parse.quote_plus(name))
    favorite = (sys.argv[0]
                + "?url=" + urllib_parse.quote_plus(url)
                + "&fav=" + fav
                + "&favmode=" + str(mode)
                + "&mode=" + str('favorites.Favorites')
                + "&img=" + urllib_parse.quote_plus(iconimage)
                + "&name=" + urllib_parse.quote_plus(name)
                + "&duration=" + duration
                + "&quality=" + quality)
    ok = True
    if not iconimage:
        iconimage = cuminationicon
    if duration:
        if addon.getSetting('duration_in_name') == 'true':
            duration = " [COLOR deeppink]" + duration + "[/COLOR]"
            name = name + duration if six.PY3 else (name.decode('utf-8') + duration).encode('utf-8')
        else:
            secs = 0
            try:
                duration = duration.upper().replace('H', ':').replace('M', ':').replace('S', '').replace('EC', '').replace(' ', '').replace('IN', '0').replace('::', ':').strip()
                if ':' in duration:
                    if duration.endswith(':'):
                        duration += '0'
                    if duration.startswith(':'):
                        duration = '0' + duration
                    secs = sum(int(x) * 60 ** i for i, x in enumerate(reversed(duration.split(':'))))
                elif duration.isdigit():
                    secs = int(duration)
                if secs is None and len(duration) > 0:
                    xbmc.log("ChaturbateTV: Duration format error: " + str(duration), xbmc.LOGERROR)
            except:
                xbmc.log("ChaturbateTV: Duration format error: " + str(duration), xbmc.LOGERROR)
    width = None
    if quality:
        if addon.getSetting('quality_in_name') == 'true':
            quality = " [COLOR orange]" + quality + "[/COLOR]"
            name = name + quality if six.PY3 else (name.decode('utf-8') + quality).encode('utf-8')
        else:
            width, height = get_resolution(quality)
    if dname:
        desc = name
    liz = xbmcgui.ListItem(name)
    if KODIVER > 19.8:
        vtag = liz.getVideoInfoTag()
        vtag.setMediaType('movie')
        vtag.setTitle(name)
        vtag.setGenres(['Porn'])
        if duration and addon.getSetting('duration_in_name') != 'true':
            vtag.setDuration(secs)
        if desc:
            vtag.setPlot(desc)
            vtag.setPlotOutline(desc)
        if width:
            vtag.addVideoStream(xbmc.VideoStreamDetail(width=width, height=height, codec='h264'))
        else:
            vtag.addVideoStream(xbmc.VideoStreamDetail(codec='h264'))
    else:
        if duration and addon.getSetting('duration_in_name') != 'true':
            liz.setInfo(type="Video", infoLabels={"Duration": secs})
        if desc:
            liz.setInfo(type="Video", infoLabels={"Title": name, "plot": desc, "plotoutline": desc})
        else:
            liz.setInfo(type="Video", infoLabels={"Title": name})
        if width:
            video_streaminfo = {'codec': 'h264', 'width': width, 'height': height}
        else:
            video_streaminfo = {'codec': 'h264'}
        liz.addStreamInfo('video', video_streaminfo)

    if not fanart:
        fanart = os.path.join(rootDir, 'fanart.jpg')
        if addon.getSetting('posterfanart') == 'true':
            fanart = iconimage

    liz.setArt({'thumb': iconimage, 'icon': "DefaultVideo.png", 'poster': iconimage, 'fanart': fanart})

    if stream:
        liz.setProperty('IsPlayable', 'true')

    if contextm:
        if isinstance(contextm, list):
            for i in contextm:
                if isinstance(i, tuple):
                    contextMenuItems.append(i)
        else:
            if isinstance(contextm, tuple):
                contextMenuItems.append(contextm)
    favorder = addon.getSetting("favorder") or 'date added'
    if fav == 'del' and favorder == 'date added':
        favorite_move_to_top = (sys.argv[0]
                                + "?url=" + urllib_parse.quote_plus(url)
                                + "&fav=" + 'move_to_top'
                                + "&favmode=" + str(mode)
                                + "&mode=" + str('favorites.Favorites')
                                + "&img=" + urllib_parse.quote_plus(iconimage)
                                + "&name=" + urllib_parse.quote_plus(name)
                                + "&duration=" + urllib_parse.quote_plus(duration)
                                + "&quality=" + urllib_parse.quote_plus(quality))
        contextMenuItems.append(('[COLOR hotpink]Move favorite to Top[/COLOR]', 'RunPlugin(' + favorite_move_to_top + ')'))
        favorite_move_up = (sys.argv[0]
                            + "?url=" + urllib_parse.quote_plus(url)
                            + "&fav=" + 'move_up'
                            + "&favmode=" + str(mode)
                            + "&mode=" + str('favorites.Favorites')
                            + "&img=" + urllib_parse.quote_plus(iconimage)
                            + "&name=" + urllib_parse.quote_plus(name)
                            + "&duration=" + urllib_parse.quote_plus(duration)
                            + "&quality=" + urllib_parse.quote_plus(quality))
        contextMenuItems.append(('[COLOR hotpink]Move favorite Up[/COLOR]', 'RunPlugin(' + favorite_move_up + ')'))
        favorite_move_down = (sys.argv[0]
                              + "?url=" + urllib_parse.quote_plus(url)
                              + "&fav=" + 'move_down'
                              + "&favmode=" + str(mode)
                              + "&mode=" + str('favorites.Favorites')
                              + "&img=" + urllib_parse.quote_plus(iconimage)
                              + "&name=" + urllib_parse.quote_plus(name)
                              + "&duration=" + urllib_parse.quote_plus(duration)
                              + "&quality=" + urllib_parse.quote_plus(quality))
        contextMenuItems.append(('[COLOR hotpink]Move favorite Down[/COLOR]', 'RunPlugin(' + favorite_move_down + ')'))
        favorite_move_to_bottom = (sys.argv[0]
                                   + "?url=" + urllib_parse.quote_plus(url)
                                   + "&fav=" + 'move_to_bottom'
                                   + "&favmode=" + str(mode)
                                   + "&mode=" + str('favorites.Favorites')
                                   + "&img=" + urllib_parse.quote_plus(iconimage)
                                   + "&name=" + urllib_parse.quote_plus(name)
                                   + "&duration=" + urllib_parse.quote_plus(duration)
                                   + "&quality=" + urllib_parse.quote_plus(quality))
        contextMenuItems.append(('[COLOR hotpink]Move favorite to Bottom[/COLOR]', 'RunPlugin(' + favorite_move_to_bottom + ')'))
    contextMenuItems.append(('[COLOR hotpink]' + favtext + ' favorites[/COLOR]', 'RunPlugin(' + favorite + ')'))
    if not noDownload:
        contextMenuItems.append(('[COLOR hotpink]Download Video[/COLOR]', 'RunPlugin(' + dwnld + ')'))
    settings_url = (sys.argv[0]
                    + "?mode=" + str('utils.openSettings'))
    contextMenuItems.append(
        ('[COLOR hotpink]Addon settings[/COLOR]', 'RunPlugin(' + settings_url + ')'))
    setview = (sys.argv[0]
               + "?mode=" + str('utils.setview'))
    contextMenuItems.append(
        ('[COLOR hotpink]Set this view as default[/COLOR]', 'RunPlugin(' + setview + ')'))
    liz.addContextMenuItems(contextMenuItems, replaceItems=False)
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz, isFolder=False)
    return ok


def get_resolution(quality):
    resolution = (None, None)
    try:
        quality = str(quality).upper()

        if quality.endswith('P'):
            quality = quality[:-1]
        if quality.isdigit():
            resolution = (int(quality) * 16 // 9, int(quality))
        resolutions = {'SD': (640, 480), 'FULLHD': (1920, 1080), 'FHD': (1920, 1080), '2K': (2560, 1440), '4K': (3840, 2160), 'UHD': (3840, 2160), 'HD': (1280, 720), '8K': (7680, 4320)}
        for x in resolutions.keys():
            if x in quality:
                quality = x
                break

        if quality in resolutions.keys():
            resolution = resolutions[quality]
        if len(quality) > 0 and resolution == (None, None):
            xbmc.log("ChaturbateTV: Quality format error: " + str(quality), xbmc.LOGERROR)
    except:
        xbmc.log("ChaturbateTV: Quality format error: " + str(quality), xbmc.LOGERROR)
    return resolution


def addDir(name, url, mode, iconimage=None, page=None, channel=None, section=None, keyword='', Folder=True, about=None,
           custom=False, list_avail=True, listitem_id=None, custom_list=False, contextm=None, desc=''):
    u = (sys.argv[0]
         + "?url=" + urllib_parse.quote_plus(url)
         + "&mode=" + str(mode)
         + "&page=" + str(page)
         + "&channel=" + str(channel)
         + "&section=" + str(section)
         + "&keyword=" + urllib_parse.quote_plus(keyword)
         + "&name=" + urllib_parse.quote_plus(name))
    ok = True
    if not iconimage:
        iconimage = cuminationicon
    liz = xbmcgui.ListItem(name)
    fanart_bg = os.path.join(rootDir, 'fanart.jpg')
    art = {'thumb': iconimage, 'icon': 'DefaultFolder.png', 'fanart': fanart_bg}
    if addon.getSetting('posterfanart') == 'true':
        art.update({'poster': iconimage})
    liz.setArt(art)
    if KODIVER > 19.8:
        vtag = liz.getVideoInfoTag()
        vtag.setTitle(name)
        if desc:
            vtag.setPlot(desc)
            vtag.setPlotOutline(desc)
    else:
        liz.setInfo(type="Video", infoLabels={"Title": name})
        if desc:
            liz.setInfo(type="Video", infoLabels={"Title": name, "plot": desc, "plotoutline": desc})
    contextMenuItems = []
    if contextm:
        if isinstance(contextm, list):
            for i in contextm:
                if isinstance(i, tuple):
                    contextMenuItems.append(i)
        else:
            if isinstance(contextm, tuple):
                contextMenuItems.append(contextm)
    if about:
        about_url = (sys.argv[0]
                     + "?mode=" + str('main.about_site')
                     + "&img=" + urllib_parse.quote_plus(iconimage)
                     + "&name=" + urllib_parse.quote_plus(name)
                     + "&about=" + str(about)
                     + "&custom=" + str(custom))
        contextMenuItems.append(
            ('[COLOR hotpink]About site[/COLOR]', 'RunPlugin(' + about_url + ')'))
    if list_avail:
        list_item_name = 'Add item to ...'
        list_url = (sys.argv[0]
                    + "?url=" + urllib_parse.quote_plus(url)
                    + "&favmode=" + str(mode)
                    + "&mode=" + str('favorites.add_listitem')
                    + "&img=" + urllib_parse.quote_plus(iconimage)
                    + "&name=" + urllib_parse.quote_plus(name))
        contextMenuItems.append(('[COLOR hotpink]%s[/COLOR]' % list_item_name, 'RunPlugin(' + list_url + ')'))
    if listitem_id:
        move_listitem_url = (sys.argv[0]
                             + "?mode=" + str('favorites.move_listitem')
                             + "&listitem_id=" + str(listitem_id))
        contextMenuItems.append(('[COLOR hotpink]Move item to ...[/COLOR]', 'RunPlugin(' + move_listitem_url + ')'))
        listitem_url = (sys.argv[0]
                        + "?mode=" + str('favorites.remove_listitem')
                        + "&listitem_id=" + str(listitem_id))
        contextMenuItems.append(('[COLOR hotpink]Remove from list[/COLOR]', 'RunPlugin(' + listitem_url + ')'))
        moveupitem_url = (sys.argv[0]
                          + "?mode=" + str('favorites.moveup_listitem')
                          + "&listitem_id=" + str(listitem_id))
        contextMenuItems.append(('[COLOR hotpink]Move item Up[/COLOR]', 'RunPlugin(' + moveupitem_url + ')'))
        movedownitem_url = (sys.argv[0]
                            + "?mode=" + str('favorites.movedown_listitem')
                            + "&listitem_id=" + str(listitem_id))
        contextMenuItems.append(('[COLOR hotpink]Move item Down[/COLOR]', 'RunPlugin(' + movedownitem_url + ')'))

    if custom_list:
        editlist_url = (sys.argv[0]
                        + "?mode=" + str('favorites.edit_list')
                        + "&rowid=" + str(url))
        contextMenuItems.append(('[COLOR hotpink]Edit name[/COLOR]', 'RunPlugin(' + editlist_url + ')'))
        dellist_url = (sys.argv[0]
                       + "?mode=" + str('favorites.remove_list')
                       + "&rowid=" + str(url))
        contextMenuItems.append(('[COLOR hotpink]Remove list[/COLOR]', 'RunPlugin(' + dellist_url + ')'))
        moveuplist_url = (sys.argv[0]
                          + "?mode=" + str('favorites.moveup_list')
                          + "&rowid=" + str(url))
        contextMenuItems.append(('[COLOR hotpink]Move list Up[/COLOR]', 'RunPlugin(' + moveuplist_url + ')'))
        movedownlist_url = (sys.argv[0]
                            + "?mode=" + str('favorites.movedown_list')
                            + "&rowid=" + str(url))
        contextMenuItems.append(('[COLOR hotpink]Move list Down[/COLOR]', 'RunPlugin(' + movedownlist_url + ')'))

    settings_url = (sys.argv[0]
                    + "?mode=" + str('utils.openSettings'))
    contextMenuItems.append(
        ('[COLOR hotpink]Addon settings[/COLOR]', 'RunPlugin(' + settings_url + ')'))
    setview = (sys.argv[0]
               + "?mode=" + str('utils.setview'))
    contextMenuItems.append(
        ('[COLOR hotpink]Set this view as default[/COLOR]', 'RunPlugin(' + setview + ')'))
    liz.addContextMenuItems(contextMenuItems, replaceItems=False)
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz, isFolder=Folder)
    return ok


def clean_temp():
    shutil.rmtree(tempDir)
    os.makedirs(tempDir)

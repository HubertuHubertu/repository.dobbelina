# Miami Nights palette — Kodi named colors (reliable across skins/versions)


def c(color, text):
    return '[COLOR {0}]{1}[/COLOR]'.format(color, text)


# Primary accents
CYAN = 'cyan'
PINK = 'hotpink'
ORANGE = 'orange'
VIOLET = 'violet'
WHITE = 'white'
DIM = 'grey'
FAV = 'gold'


def img(name):
    from resources.lib.basics import cum_image
    return cum_image('miami-{0}.png'.format(name))

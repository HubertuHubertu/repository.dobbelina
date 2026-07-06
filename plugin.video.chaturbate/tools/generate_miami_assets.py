"""Generate Miami Nights menu thumbnails with visible labels."""
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, 'resources', 'images')
W, H = 512, 288

# label, top_rgb, bottom_rgb, accent_rgb
TILES = {
    'featured': ('FEATURED', (255, 110, 199), (255, 158, 68), (0, 212, 255)),
    'search': ('SEARCH', (0, 212, 255), (26, 10, 46), (255, 110, 199)),
    'top': ('TOP CAMS', (255, 158, 68), (255, 110, 199), (255, 255, 255)),
    'favorites': ('FAVORITES', (255, 215, 0), (255, 110, 199), (255, 255, 255)),
    'follow': ('FOLLOWED', (185, 103, 255), (0, 212, 255), (255, 255, 255)),
    'female': ('FEMALE', (255, 110, 199), (185, 103, 255), (0, 212, 255)),
    'male': ('MALE', (0, 212, 255), (26, 10, 46), (255, 110, 199)),
    'couple': ('COUPLES', (255, 158, 68), (255, 110, 199), (255, 255, 255)),
    'trans': ('TRANS', (185, 103, 255), (255, 110, 199), (0, 212, 255)),
    'tags': ('TAGS', (0, 212, 255), (185, 103, 255), (255, 110, 199)),
    'list': ('BROWSE', (40, 20, 70), (255, 110, 199), (0, 212, 255)),
    'refresh': ('REFRESH', (255, 80, 100), (255, 158, 68), (255, 255, 255)),
    'brand': ('CB TV', (255, 110, 199), (0, 212, 255), (255, 255, 255)),
    'next': ('NEXT', (0, 212, 255), (26, 10, 46), (255, 110, 199)),
    'cat': ('CATEGORY', (185, 103, 255), (255, 158, 68), (255, 255, 255)),
    'saved': ('SAVED', (255, 215, 0), (185, 103, 255), (0, 212, 255)),
    'deps': ('SETUP', (0, 212, 255), (40, 20, 70), (255, 215, 0)),
}

# Simple glyph hints per tile (drawn above label)
GLYPHS = {
    'search': 'search',
    'favorites': 'star',
    'saved': 'star',
    'refresh': 'sync',
    'deps': 'gear',
    'featured': 'play',
    'top': 'trophy',
}


def _lerp(a, b, t):
    return int(a + (b - a) * t)


def _draw_glyph(draw, kind, cx, cy, accent, size=36):
    s = size
    if kind == 'search':
        draw.ellipse((cx - s, cy - s, cx + s, cy + s), outline=accent, width=3)
        draw.line((cx + int(s * 0.65), cy + int(s * 0.65), cx + s + 14, cy + s + 14), fill=accent, width=4)
    elif kind == 'star':
        pts = []
        for i in range(10):
            ang = 3.14159 / 2 + i * 3.14159 / 5
            r = s if i % 2 == 0 else s // 2
            pts.append((cx + int(r * math.cos(ang)), cy - int(r * math.sin(ang))))
        draw.polygon(pts, outline=accent, fill=None)
    elif kind == 'sync':
        draw.arc((cx - s, cy - s, cx + s, cy + s), 30, 300, fill=accent, width=4)
        draw.polygon([(cx + s - 4, cy - 8), (cx + s + 10, cy), (cx + s - 4, cy + 8)], fill=accent)
    elif kind == 'gear':
        draw.ellipse((cx - s // 2, cy - s // 2, cx + s // 2, cy + s // 2), outline=accent, width=3)
        for i in range(8):
            ang = i * 3.14159 / 4
            x1 = cx + int((s // 2 + 6) * math.cos(ang))
            y1 = cy + int((s // 2 + 6) * math.sin(ang))
            x2 = cx + int((s // 2 + 16) * math.cos(ang))
            y2 = cy + int((s // 2 + 16) * math.sin(ang))
            draw.line((x1, y1, x2, y2), fill=accent, width=3)
    elif kind == 'play':
        draw.polygon([(cx - s // 2, cy - s), (cx + s, cy), (cx - s // 2, cy + s)], fill=accent)
    elif kind == 'trophy':
        draw.rectangle((cx - s // 2, cy - s // 3, cx + s // 2, cy + s // 4), outline=accent, width=3)
        draw.rectangle((cx - s // 4, cy + s // 4, cx + s // 4, cy + s), outline=accent, width=3)


def main():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        raise SystemExit('Install Pillow: pip install pillow')

    os.makedirs(IMG, exist_ok=True)
    font_lg = None
    font_sm = None
    for path in (
        'C:/Windows/Fonts/impact.ttf',
        'C:/Windows/Fonts/arialbd.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    ):
        if os.path.isfile(path):
            try:
                font_lg = ImageFont.truetype(path, 46)
                font_sm = ImageFont.truetype(path, 22)
                break
            except Exception:
                pass
    if font_lg is None:
        font_lg = ImageFont.load_default()
        font_sm = font_lg

    for name, (label, top, bottom, accent) in TILES.items():
        img = Image.new('RGB', (W, H), (26, 10, 46))
        px = img.load()
        for y in range(H):
            t = y / float(H - 1)
            r = _lerp(top[0], bottom[0], t)
            g = _lerp(top[1], bottom[1], t)
            b = _lerp(top[2], bottom[2], t)
            for x in range(W):
                px[x, y] = (r, g, b)

        draw = ImageDraw.Draw(img)
        glyph = GLYPHS.get(name)
        if glyph:
            _draw_glyph(draw, glyph, W // 2, int(H * 0.28), accent)
        # neon frame
        for i in range(4):
            draw.rectangle((8 + i, 8 + i, W - 9 - i, H - 9 - i), outline=accent)
        # perspective grid
        for x in range(0, W, 48):
            draw.line((x, int(H * 0.72), W // 2, H - 12), fill=accent, width=1)
        for y in range(int(H * 0.72), H, 18):
            draw.line((0, y, W, y), fill=accent, width=1)

        tw, th = draw.textbbox((0, 0), label, font=font_lg)[2:]
        draw.text(((W - tw) // 2, (H - th) // 2 - 8), label, fill=(255, 255, 255), font=font_lg)
        draw.text((18, H - 36), 'ChaturbateTV', fill=accent, font=font_sm)

        out = os.path.join(IMG, 'miami-{0}.png'.format(name))
        img.save(out, 'PNG')
        print('wrote', out)


if __name__ == '__main__':
    main()

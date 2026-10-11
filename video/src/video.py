import sys, math, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

MEDIA = sys.argv[1]
W, H, FPS = 1920, 1080, 30
NAVY = (39, 43, 96); RED = (227, 6, 19); BG2 = (241, 242, 249); TX2 = (75, 79, 107)
A4 = (219, 221, 236); A5 = (142, 147, 181); A3 = (108, 118, 201); GREEN = (30, 158, 90); WHITE = (255, 255, 255)
FD = '/usr/share/fonts/truetype/crosextra/'
_fc = {}
def F(sz, b=False, i=False):
    k = (sz, b, i)
    if k not in _fc:
        n = 'Carlito-' + ('Bold' if b else '') + ('Italic' if i else '')
        if n == 'Carlito-': n = 'Carlito-Regular'
        _fc[k] = ImageFont.truetype(FD + n + '.ttf', sz)
    return _fc[k]

def med(n): return MEDIA + '/' + n
_ic = {}
def icon(n, sz, color=None):
    k = (n, sz, color)
    if k not in _ic:
        im = Image.open(med(n)).convert('RGBA').resize((sz, sz), Image.LANCZOS)
        if color:
            c = Image.new('RGBA', im.size, color + (255,)); c.putalpha(im.getchannel('A')); im = c
        _ic[k] = im
    return _ic[k]

def eo(p): return 1 - (1 - p) ** 3
def eio(p): return 3 * p * p - 2 * p * p * p
def back(p, s=1.6): p -= 1; return 1 + p * p * ((s + 1) * p + s)
def cl(x): return max(0.0, min(1.0, x))

def wrap(text, f, mw):
    out = []
    for para in text.split('\n'):
        line = ''
        for w in para.split(' '):
            t = (line + ' ' + w).strip()
            if f.getlength(t) <= mw: line = t
            else:
                if line: out.append(line)
                line = w
        out.append(line)
    return out

def mtext(d, xy, text, f, fill, mw, lh=None, anchor_center=False):
    x, y = xy; lh = lh or int(f.size * 1.2)
    for ln in wrap(text, f, mw):
        if anchor_center: d.text((x - f.getlength(ln) / 2, y), ln, font=f, fill=fill)
        else: d.text((x, y), ln, font=f, fill=fill)
        y += lh
    return y

def spaced(d, xy, text, f, fill, sp=2, center=False):
    x, y = xy
    tw = sum(f.getlength(c) + sp for c in text) - sp
    if center: x -= tw / 2
    for c in text:
        d.text((x, y), c, font=f, fill=fill); x += f.getlength(c) + sp
    return tw

M = 20
def card(w, h, fill=WHITE, r=12, border=A4, shadow=True):
    im = Image.new('RGBA', (w + 2 * M, h + 2 * M), (0, 0, 0, 0))
    if shadow:
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((M, M + 6, M + w, M + h + 6), r, fill=(39, 43, 96, 40))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((M, M, M + w - 1, M + h - 1), r, fill=fill, outline=border, width=2 if border else 0)
    return im, d

def circ_icon(d, img, cx, cy, dia, fill, iname, isz=None):
    d.ellipse((cx - dia / 2, cy - dia / 2, cx + dia / 2, cy + dia / 2), fill=fill)
    if iname:
        isz = isz or int(dia * 0.52); ic = icon(iname, isz)
        img.paste(ic, (int(cx - isz / 2), int(cy - isz / 2)), ic)

_lut = {}
def paste(frame, img, x, y, a=1.0):
    if a <= 0.01: return
    if a >= 0.99: frame.paste(img, (int(x), int(y)), img); return
    q = round(a * 40)
    if q not in _lut: _lut[q] = [int(v * q / 40) for v in range(256)]
    frame.paste(img, (int(x), int(y)), img.getchannel('A').point(_lut[q]))

class El:
    def __init__(s, img, x, y, t0, anim='up', dur=0.5, dist=40, off=M):
        s.img, s.x, s.y, s.t0, s.anim, s.dur, s.dist, s.off = img, x - off, y - off, t0, anim, dur, dist, off
    def draw(s, fr, t):
        p = (t - s.t0) / s.dur
        if p <= 0: return
        p = min(1, p); e = eo(p); x, y, img = s.x, s.y, s.img
        if s.anim == 'up': y += (1 - e) * s.dist
        elif s.anim == 'down': y -= (1 - e) * s.dist
        elif s.anim == 'left': x -= (1 - e) * s.dist
        elif s.anim == 'right': x += (1 - e) * s.dist
        elif s.anim == 'pop' and p < 1:
            sc = 0.5 + 0.5 * back(p)
            w, h = img.size; nw, nh = max(1, int(w * sc)), max(1, int(h * sc))
            img = img.resize((nw, nh), Image.BILINEAR); x += (w - nw) / 2; y += (h - nh) / 2
        paste(fr, img, x, y, min(1, p * 1.8))

def text_el(text, f, color, t0, x, y, anim='up', dur=0.5, dist=40, center=False, sp=None):
    w = int((f.getlength(text) if sp is None else sum(f.getlength(c) + sp for c in text))) + 8
    im = Image.new('RGBA', (w, int(f.size * 1.4)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if sp is None: d.text((2, 0), text, font=f, fill=color)
    else: spaced(d, (2, 0), text, f, color, sp)
    if center: x -= w / 2
    return El(im, x, y, t0, anim, dur, dist, off=0)

def bandeau(text, t0, y=690, x=70, w=1780, h=64):
    im, d = card(w, h, fill=NAVY, r=10, border=None)
    f = F(26, True); d.text((M + 28, M + h / 2 - 15), text, font=f, fill=WHITE)
    return El(im, x, y, t0, 'up', 0.6, 30)

# ---------------- backgrounds ----------------
_bg = {}
def bg(name):
    if name not in _bg: _bg[name] = Image.open(med(name)).convert('RGB').resize((W, H), Image.LANCZOS)
    return _bg[name]
_src = {}
def kenburns(name, t, dur, z0=1.0, z1=1.06, ax=0.5, ay=0.5):
    if name not in _src: _src[name] = Image.open(med(name)).convert('RGB')
    s = _src[name]; sw, sh = s.size
    z = z0 + (z1 - z0) * eio(cl(t / dur)); cw, ch = sw / z, sh / z
    x0 = (sw - cw) * ax; y0 = (sh - ch) * ay
    return s.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))

def title_el(prefix, rest, t0=0.05):
    f = F(46, True)
    w = int(f.getlength(prefix + rest)) + 80
    im = Image.new('RGBA', (w, 70), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    fl = icon('image-1007-1.png', 30); im.paste(fl, (0, 14), fl)
    x = 46
    if prefix:
        d.text((x, 4), prefix, font=f, fill=RED); x += f.getlength(prefix)
    d.text((x, 4), rest, font=f, fill=NAVY)
    return El(im, 66, 36, t0, 'left', 0.6, 60, off=0)

def pill(text, fill, f=None, fg=WHITE, padx=18, h=40, sp=2):
    f = f or F(20, True)
    tw = sum(f.getlength(c) + sp for c in text) - sp
    im = Image.new('RGBA', (int(tw + 2 * padx), h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, im.width - 1, h - 1), h // 2, fill=fill)
    spaced(d, (padx, h / 2 - f.size * 0.62), text, f, fg, sp)
    return im

# ---------------- scenes ----------------
class Scene:
    bgname = 'CONTENU-image-2.jpeg'
    def __init__(s, dur): s.dur = dur; s.els = None
    def build(s): return []
    def base(s, t): return bg(s.bgname).copy()
    def extra(s, fr, t): pass
    def render(s, t):
        if s.els is None: s.els = s.build()
        fr = s.base(t)
        s.extra(fr, t)
        for e in s.els: e.draw(fr, t)
        s.post(fr, t)
        return fr
    def post(s, fr, t): pass

class Intro(Scene):
    def base(s, t): return kenburns('COUVERTURE-image-1.jpeg', t, s.dur, 1.0, 1.05, 0.0, 0.0)
    def build(s):
        e = [text_el('OUTILS MÉTIER', F(64, True), NAVY, 0.6, 70, 330, 'left', 0.7, 80),
             text_el('N4 · N5 · N7', F(64, True), NAVY, 0.9, 70, 405, 'left', 0.7, 80),
             text_el('Présentation à la Direction Générale', F(28, True, True), NAVY, 1.6, 72, 520, 'up', 0.6, 20),
             text_el('Romain Couchez', F(28, True, True), NAVY, 1.8, 72, 556, 'up', 0.6, 20)]
        e.append(El(pill('AVANT  /  APRÈS', RED, F(26, True), h=52, padx=24), 70, 650, 3.0, 'pop', 0.5, off=0))
        e.append(text_el('Études, plans, DOE : ce qui change avec nos outils', F(30, False, True), TX2, 3.5, 72, 720, 'up', 0.6, 20))
        return e
    def extra(s, fr, t):
        p = eo(cl((t - 1.2) / 0.8))
        if p > 0: ImageDraw.Draw(fr).rectangle((72, 488, 72 + 360 * p, 494), fill=RED)

class Divider(Scene):
    def __init__(s, dur, img, num, lines): super().__init__(dur); s.img, s.num, s.lines = img, num, lines
    def base(s, t): return kenburns(s.img, t, s.dur, 1.0, 1.04, 0.0, 0.5)
    def build(s):
        cx = int(W * 0.75)
        e = [text_el(s.num, F(110, True), RED, 0.15, cx, 300, 'pop', 0.5, center=True)]
        for i, l in enumerate(s.lines):
            e.append(text_el(l, F(58, True), NAVY, 0.45 + 0.18 * i, cx, 460 + 70 * i, 'up', 0.6, 50, center=True))
        return e

class Origine(Scene):
    D = [('image-3-1.png', 'DEPUIS 3 ANS', 'Une idée née du terrain', 'Les problématiques rencontrées au quotidien chez Eurofeu'),
         ('image-3-2.png', 'LE DÉVELOPPEMENT', 'Sur mon temps personnel', 'Des outils réalisés principalement par mes soins'),
         ('image-3-3.png', 'LES RENFORTS', 'Deux appuis précieux', 'Mon cousin, développeur, pour corriger les bugs tenaces ; mon beau-frère pour la phase de test'),
         ('image-3-4.png', "AUJOURD'HUI", 'Trois outils opérationnels', "N4, N5 et N7, aujourd'hui commercialisés par mon beau-frère")]
    X = [110, 560, 1010, 1460]
    def build(s):
        e = [title_el('', "D'où viennent ces outils ?")]
        for i, (ic, lab, ti, tx) in enumerate(s.D):
            t0 = 0.6 + 1.0 * i; x = s.X[i]
            im = Image.new('RGBA', (110, 110), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
            d.ellipse((5, 5, 105, 105), fill=WHITE); circ_icon(d, im, 55, 55, 92, RED if i == 3 else NAVY, ic)
            e.append(El(im, x - 5, 205, t0, 'pop', 0.5, off=0))
            im = Image.new('RGBA', (400, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
            spaced(d, (0, 0), lab, F(19, True), RED, 2)
            y = mtext(d, (0, 34), ti, F(32, True), NAVY, 380)
            mtext(d, (0, y + 10), tx, F(23), TX2, 370)
            e.append(El(im, x, 340, t0 + 0.15, 'up', 0.6, 30, off=0))
        e.append(bandeau("Des outils conçus par quelqu'un du métier, pour répondre à nos besoins réels", 5.0, 760))
        return e
    def extra(s, fr, t):
        p = eo(cl((t - 0.4) / 3.6))
        if p > 0: ImageDraw.Draw(fr).rectangle((150, 257, 150 + (1360) * p, 263), fill=A4)

def std_card(w, h, ic, title, text, icol=RED, horiz=False):
    im, d = card(w, h)
    if horiz:
        circ_icon(d, im, M + 62, M + h / 2, 76, icol, ic)
        y = mtext(d, (M + 124, M + 30), title, F(28, True), NAVY, w - 150)
        mtext(d, (M + 124, y + 6), text, F(22), TX2, w - 150)
    else:
        circ_icon(d, im, M + 66, M + 70, 80, icol, ic)
        y = mtext(d, (M + 30, M + 140), title, F(30, True), NAVY, w - 56)
        mtext(d, (M + 30, y + 14), text, F(23), TX2, w - 56)
    return im

class Constat5(Scene):
    def build(s):
        e = [title_el('N5 · RIA', '  –  Les difficultés rencontrées'),
             El(pill('AVANT', RED), 1730, 46, 0.3, 'pop', 0.4, off=0)]
        cs = [('image-5-1.png', 'Implantation approximative', 'Couverture des RIA vérifiée à la ficelle ou à la règle, directement sur le plan'),
              ('image-5-2.png', 'DOE long à réaliser', 'Un temps important passé à constituer le dossier en fin de chantier'),
              ('image-5-3.png', 'Notes de calcul complexes', 'Fathom est peu intuitif et difficile à utiliser')]
        for i, c in enumerate(cs):
            e.append(El(std_card(400, 420, *c), 70 + 430 * i, 200, 0.3 + 0.35 * i, 'up', 0.55, 50))
        im, d = card(500, 420, fill=NAVY, border=None)
        spaced(d, (M + 36, M + 40), 'LICENCE FATHOM', F(20, True), A4, 3)
        d.text((M + 36, M + 230), 'par an', font=F(34, True), fill=WHITE)
        mtext(d, (M + 36, M + 300), 'Le coût de la licence utilisée pour nos notes de calcul', F(24), A4, 430)
        e.append(El(im, 1360, 200, 1.3, 'up', 0.55, 50))
        e.append(bandeau('Résultat : une précision limitée, du temps perdu et un coût de licence récurrent', 3.6))
        return e
    def post(s, fr, t):
        if t < 1.5: return
        v = int(4000 * eo(cl((t - 1.5) / 1.4)) / 10) * 10
        ImageDraw.Draw(fr).text((1396, 300), f'{v:,} €'.replace(',', ' '), font=F(96, True), fill=WHITE)

class Constat7(Scene):
    def build(s):
        e = [title_el('N7 · Détection', '  –  Les difficultés rencontrées'),
             El(pill('AVANT', RED), 1730, 46, 0.3, 'pop', 0.4, off=0)]
        st = [('1 · ÉTUDE', 'image-6-1.png', 'Une étude longue', "L'étude est réalisée à la main, directement sur plan"),
              ('2 · CHANTIER', 'image-6-3.png', 'Un plan dessiné sur PowerPoint', 'Le plan remis au client en phase chantier est redessiné sur PowerPoint'),
              ('3 · DOE', 'image-6-5.png', 'Des plans DOE longs à réaliser', 'Les plans sont repris une nouvelle fois pour le dossier final')]
        for i, (h, ic, ti, tx) in enumerate(st):
            x = 70 + 620 * i; t0 = 0.3 + 0.7 * i
            im, d = card(540, 54, fill=NAVY, r=8, border=None, shadow=False)
            spaced(d, (M + 270, M + 13), h, F(24, True), WHITE, 2, center=True)
            e.append(El(im, x, 190, t0, 'down', 0.5, 30))
            e.append(El(std_card(540, 360, ic, ti, tx), x, 264, t0 + 0.15, 'up', 0.55, 50))
            if i < 2:
                ch = icon('image-10-1.png', 40); e.append(El(ch, x + 556, 420, t0 + 0.5, 'left', 0.4, 30, off=0))
        e.append(bandeau('Résultat : les plans sont refaits à chaque étape, avec des outils qui ne sont pas faits pour cela', 3.6))
        return e

class Constat4(Scene):
    def build(s):
        e = [title_el('N4 · Extincteurs', '  –  Les difficultés rencontrées'),
             El(pill('AVANT', RED), 1730, 46, 0.3, 'pop', 0.4, off=0)]
        cs = [('image-7-1.png', 'Un dossier long à réaliser', 'Beaucoup de temps passé sur chaque étude N4'),
              ('image-7-2.png', 'Une présentation inégale', 'Des plans « light », aux gommettes ou au fluo selon les commerciaux'),
              ('image-7-3.png', 'Un technicien qui cherche', 'Difficile de retrouver sur site les extincteurs à remplacer ou à ajouter après la commande'),
              ('image-7-4.png', 'Un dossier Excel à remplir', "Un classeur à compléter à la main pour le chef d'agence")]
        for i, c in enumerate(cs):
            e.append(El(std_card(870, 200, *c, horiz=True), 70 + 910 * (i % 2), 200 + 230 * (i // 2), 0.3 + 0.35 * i, 'up', 0.55, 50))
        e.append(bandeau("Résultat : des dossiers inégaux et du temps perdu, du bureau jusqu'au chantier", 3.4))
        return e

class Freins(Scene):
    def build(s):
        e = [title_el('', 'Trois métiers, les mêmes freins')]
        bl = [('image-8-1.png', 'Du temps', 'Études, plans et DOE réalisés à la main, parfois plusieurs fois pour un même dossier'),
              ('image-8-2.png', "De l'homogénéité", "Un rendu qui varie d'un collaborateur à l'autre et d'une agence à l'autre"),
              ('image-8-3.png', 'Des outils adaptés', 'PowerPoint, Excel, Fathom : des outils génériques, pas pensés pour nos dossiers')]
        for i, (ic, ti, tx) in enumerate(bl):
            im, d = card(560, 400, fill=NAVY, border=None)
            circ_icon(d, im, M + 76, M + 80, 84, RED, ic)
            spaced(d, (M + 36, M + 160), 'IL NOUS MANQUE', F(19, True), A5, 3)
            d.text((M + 36, M + 192), ti, font=F(40, True), fill=WHITE)
            mtext(d, (M + 36, M + 256), tx, F(25), A4, 490)
            e.append(El(im, 70 + 600 * i, 190, 0.3 + 0.45 * i, 'up', 0.6, 60))
        ar = icon('image-8-4.png', 46)
        e.append(El(ar, 70, 668, 2.6, 'left', 0.5, 40, off=0))
        f = F(38, True)
        im = Image.new('RGBA', (1600, 60), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.text((0, 0), "D'où l'idée :", font=f, fill=RED); d.text((f.getlength("D'où l'idée : "), 0), 'créer des outils pensés pour nos métiers', font=f, fill=NAVY)
        e.append(El(im, 134, 666, 2.8, 'left', 0.6, 40, off=0))
        return e

class Logique(Scene):
    def build(s):
        e = [title_el('', 'Une même logique pour les trois métiers')]
        st = [('Le plan du client', "PDF ou image, chargé tel quel dans l'outil"),
              ("La mise à l'échelle", 'Une cote connue suffit pour calibrer le plan'),
              ("L'implantation", 'Règles APSAD intégrées, contrôles en direct'),
              ('Les livrables', 'Plans, DOE, notes de calcul et dossiers générés')]
        for i, (ti, tx) in enumerate(st):
            im, d = card(380, 270)
            d.ellipse((M + 28, M + 28, M + 88, M + 88), fill=RED if i == 3 else NAVY)
            f = F(32, True); d.text((M + 58 - f.getlength(str(i + 1)) / 2, M + 38), str(i + 1), font=f, fill=WHITE)
            y = mtext(d, (M + 28, M + 112), ti, F(30, True), NAVY, 330)
            mtext(d, (M + 28, y + 10), tx, F(23), TX2, 330)
            x = 70 + 470 * i; t0 = 0.3 + 0.7 * i
            e.append(El(im, x, 180, t0, 'up', 0.55, 50))
            if i < 3: e.append(El(icon('image-10-1.png', 40), x + 405, 290, t0 + 0.4, 'left', 0.4, 30, off=0))
        tl = [('N4 · EXTINCTEURS', 'N4 Conceptor', 'Référentiel APSAD R4'),
              ('N5 · RIA', 'Implantation RIA Pro + HydraRIA', 'Référentiel APSAD R5'),
              ('N7 · DÉTECTION', 'DetectR7', 'Référentiel APSAD R7')]
        for i, (la, na, re) in enumerate(tl):
            im, d = card(570, 200, fill=BG2, border=None, shadow=False)
            spaced(d, (M + 34, M + 30), la, F(20, True), RED, 3)
            y = mtext(d, (M + 34, M + 70), na, F(34, True), NAVY, 500)
            d.text((M + 34, M + 150), re, font=F(23), fill=TX2)
            e.append(El(im, 70 + 605 * i, 520, 3.4 + 0.3 * i, 'pop', 0.5))
        return e

# ---------------- plans ----------------
PW, PH = 1060, 740
OX0, OY0, OX1, OY1 = 60, 100, 1000, 650
CY0, CY1 = 345, 415
TOPX = [330, 580, 800]; BOTX = [430, 720]
ROOMS = [('Bureau 1', (OX0, OY0, 330, CY0)), ('Bureau 2', (330, OY0, 580, CY0)), ('Sanitaires', (580, OY0, 800, CY0)),
         ('Local technique', (800, OY0, OX1, CY0)), ('Atelier', (OX0, CY1, 430, OY1)), ('Stockage', (430, CY1, 720, OY1)),
         ('Accueil', (720, CY1, OX1, OY1)), ('Dégagement', (OX0, CY0, OX1, CY1))]

def walls():
    segs = []
    def hs(y, x0, x1, gaps):
        x = x0
        for g in sorted(gaps): segs.append(((x, y), (g, y))); x = g + 55
        segs.append(((x, y), (x1, y)))
    def vs(x, y0, y1, gaps):
        y = y0
        for g in sorted(gaps): segs.append(((x, y), (x, g))); y = g + 55
        segs.append(((x, y), (x, y1)))
    hs(OY0, OX0, OX1, []); hs(OY1, OX0, OX1, [880])
    vs(OX0, OY0, OY1, [CY0 + 8]); vs(OX1, OY0, OY1, [])
    hs(CY0, OX0, OX1, [170, 430, 660, 870]); hs(CY1, OX0, OX1, [240, 540, 790])
    for x in TOPX: vs(x, OY0, CY0, [])
    for x in BOTX: vs(x, CY1, OY1, [])
    return segs

def jitline(d, p0, p1, rnd, col, w=2, amp=1.6):
    (x0, y0), (x1, y1) = p0, p1
    n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 18))
    pts = [(x0 + (x1 - x0) * k / n + rnd.gauss(0, amp), y0 + (y1 - y0) * k / n + rnd.gauss(0, amp)) for k in range(n + 1)]
    d.line(pts, fill=col, width=w)

def paper(col, seed, amp=7):
    rng = np.random.default_rng(seed)
    a = np.array(col, float)[None, None, :] + rng.normal(0, amp, (PH, PW, 1))
    return Image.fromarray(a.clip(0, 255).astype('uint8')).filter(ImageFilter.GaussianBlur(0.6)).convert('RGBA')

def panel_mask():
    m = Image.new('L', (PW, PH), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, PW - 1, PH - 1), 16, fill=255); return m

def finish(im, label, fill, side):
    p = pill(label, fill, F(20, True), h=42)
    x = 24 if side == 'l' else PW - p.width - 24
    im.paste(p, (x, 26), p)
    out = Image.new('RGBA', (PW, PH), (0, 0, 0, 0)); out.paste(im, (0, 0), panel_mask())
    ImageDraw.Draw(out).rounded_rectangle((0, 0, PW - 1, PH - 1), 16, outline=A4, width=2)
    return out

def hand_plan(base_col, seed, pen=(70, 70, 70)):
    im = paper(base_col, seed); d = ImageDraw.Draw(im, 'RGBA'); rnd = random.Random(seed)
    for a, b in walls():
        jitline(d, a, b, rnd, pen + (210,), 3); jitline(d, a, b, rnd, pen + (110,), 2)
    for n, (x0, y0, x1, y1) in ROOMS[:-1]:
        d.text((x0 + 16, y0 + 12), n, font=F(19, False, True), fill=pen + (200,))
    return im, d, rnd

def clean_plan(tool):
    im = Image.new('RGBA', (PW, PH), WHITE + (255,)); d = ImageDraw.Draw(im, 'RGBA')
    for x in range(0, PW, 20): d.line((x, 0, x, PH), fill=BG2 + (255,))
    for y in range(0, PH, 20): d.line((0, y, PW, y), fill=BG2 + (255,))
    d.rectangle((OX0, OY0, OX1, OY1), fill=WHITE)
    return im, d

def clean_walls(d):
    for a, b in walls(): d.line((a, b), fill=NAVY, width=7)
    for a, b in walls():
        for p in (a, b): d.rectangle((p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3), fill=NAVY)

def room_labels(d, extra=None):
    for i, (n, (x0, y0, x1, y1)) in enumerate(ROOMS[:-1]):
        spaced(d, (x0 + 16, y0 + 14), n.upper(), F(16, True), A5, 1)
        if extra: d.text((x0 + 16, y0 + 36), extra[i], font=F(16), fill=A3)

def cartouche(d, tool, legend=None):
    y = 678
    d.line((60, y - 10, 1000, y - 10), fill=A4, width=2)
    d.line((60, y + 20, 260, y + 20), fill=NAVY, width=3)
    for k, x in enumerate((60, 160, 260)):
        d.line((x, y + 12, x, y + 28), fill=NAVY, width=3); d.text((x - 6, y + 30), ('0', '5', '10 m')[k], font=F(15), fill=TX2)
    if legend:
        x = 330
        for draw_sym, lab in legend:
            draw_sym(d, x + 12, y + 26); d.text((x + 32, y + 16), lab, font=F(18), fill=TX2); x += 52 + F(18).getlength(lab)
    t = tool + '  ·  RDC  ·  éch. 1:200'
    d.text((1000 - F(18, True).getlength(t), y + 16), t, font=F(18, True), fill=NAVY)

def badge(im, text, y=26):
    f = F(20, True); w = int(f.getlength(text)) + 64
    b = Image.new('RGBA', (w, 42), (0, 0, 0, 0)); d = ImageDraw.Draw(b)
    d.rounded_rectangle((0, 0, w - 1, 41), 21, fill=(232, 246, 238), outline=GREEN, width=2)
    d.ellipse((8, 7, 36, 35), fill=GREEN); ck = icon('image-11-2.png', 18); b.paste(ck, (13, 12), ck)
    d.text((46, 9), text, font=f, fill=GREEN)
    im.paste(b, (306, y), b)

def clip_building(layer):
    m = Image.new('L', (PW, PH), 0); ImageDraw.Draw(m).rectangle((OX0, OY0, OX1, OY1), fill=255)
    from PIL import ImageChops
    out = layer.copy(); out.putalpha(ImageChops.multiply(layer.getchannel('A'), m)); return out

# --- N5
RIAS = [(250, 362), (600, 362), (930, 362)]
def n5_avant():
    im, d, rnd = hand_plan((246, 242, 230), 5)
    for i, (x, y) in enumerate(RIAS):
        for k in range(2):
            r = 13 + rnd.random() * 3; d.ellipse((x - r + rnd.gauss(0, 2), y - r, x + r, y + r + rnd.gauss(0, 2)), outline=(200, 30, 30, 220), width=3)
        d.text((x - 12, y + 18), 'RIA', font=F(18, True, True), fill=(200, 30, 30, 230))
        for tx, ty in [(x - 160 + rnd.randint(-40, 40), OY0 + 40 + rnd.randint(0, 60)), (x + 140, OY1 - 40 - rnd.randint(0, 60)), (x - 120, OY1 - 70)]:
            pts = [(x + (tx - x) * k / 12 + rnd.gauss(0, 2), y + (ty - y) * k / 12 + rnd.gauss(0, 2)) for k in range(13)]
            for k in range(0, 12, 2): d.line(pts[k:k + 2], fill=(150, 105, 50, 220), width=2)
        rr = 230 + rnd.randint(-30, 30)
        d.arc((x - rr, y - rr, x + rr, y + rr), rnd.randint(190, 220), rnd.randint(300, 340), fill=(90, 90, 90, 150), width=2)
    for x, y in [(110, 160), (990 - 40, 600), (520, 610), (700, 150)]:
        d.text((x, y), '?', font=F(44, True), fill=(200, 30, 30, 200))
    ru = Image.new('RGBA', (460, 46), (232, 214, 160, 235)); rd = ImageDraw.Draw(ru)
    rd.rectangle((0, 0, 459, 45), outline=(160, 130, 70, 255), width=2)
    for k in range(0, 460, 12): rd.line((k, 0, k, 10 if k % 60 else 20), fill=(90, 70, 30, 255), width=2)
    ru = ru.rotate(17, expand=True, resample=Image.BICUBIC); im.paste(ru, (420, 450), ru)
    d.text((80, 690), 'couverture à vérifier...  à la ficelle', font=F(24, False, True), fill=(60, 60, 120, 220))
    return finish(im, 'AVANT  ·  À LA FICELLE', RED, 'r')

def n5_apres():
    im, d = clean_plan('n5')
    cov = Image.new('RGBA', (PW, PH), (0, 0, 0, 0)); cd = ImageDraw.Draw(cov, 'RGBA')
    for x, y in RIAS:
        cd.ellipse((x - 300, y - 300, x + 300, y + 300), fill=RED + (40,), outline=RED + (150,), width=2)
    im.alpha_composite(clip_building(cov)); d = ImageDraw.Draw(im, 'RGBA')
    clean_walls(d); room_labels(d)
    d.line((90, 395, 930, 395), fill=A3, width=5)
    for x, y in RIAS: d.line((x, 395, x, y + 14), fill=A3, width=5)
    d.ellipse((74, 379, 106, 411), fill=NAVY); d.text((80, 386), 'CS', font=F(15, True), fill=WHITE)
    pr = ['3,4 bar', '2,9 bar', '2,6 bar']
    for i, (x, y) in enumerate(RIAS):
        d.rounded_rectangle((x - 18, y - 16, x + 18, y + 16), 5, fill=RED)
        f = F(13, True); d.text((x - f.getlength('RIA') / 2, y - 8), 'RIA', font=f, fill=WHITE)
        lab = f'RIA {i + 1}  ·  {pr[i]}'; lw = F(17, True).getlength(lab)
        lx = x + 24 if i < 2 else x - 34 - lw
        d.rounded_rectangle((lx, y - 36, lx + lw + 10, y - 10), 6, fill=WHITE, outline=A4)
        d.text((lx + 5, y - 34), lab, font=F(17, True), fill=NAVY)
    badge(im, 'Couverture 100 %  ·  RIA défavorisé 2,6 bar')
    def s_ria(d, x, y): d.rounded_rectangle((x - 10, y - 9, x + 10, y + 9), 3, fill=RED)
    def s_cov(d, x, y): d.rectangle((x - 10, y - 9, x + 10, y + 9), fill=RED + (50,), outline=RED + (140,))
    def s_net(d, x, y): d.line((x - 12, y, x + 12, y), fill=A3, width=5)
    cartouche(d, 'Implantation RIA Pro', [(s_ria, 'RIA'), (s_cov, 'Zone couverte'), (s_net, 'Réseau')])
    return finish(im, "APRÈS  ·  AVEC L'OUTIL", NAVY, 'l')

# --- N7
DET = [(195, 222), (455, 222), (690, 222), (900, 222), (160, 520), (330, 520), (575, 520), (860, 520), (230, 380), (560, 380), (860, 380)]
def n7_avant():
    im = Image.new('RGBA', (PW, PH), WHITE + (255,)); d = ImageDraw.Draw(im, 'RGBA'); rnd = random.Random(3)
    for a, b in walls(): d.line((a[0] + rnd.randint(-3, 3), a[1] + rnd.randint(-3, 3), b[0] + rnd.randint(-3, 3), b[1] + rnd.randint(-3, 3)), fill=(0, 0, 0), width=4)
    f = F(40, True); d.text((63, 33), 'PLAN DÉTECTION', font=f, fill=(160, 160, 160)); d.text((60, 30), 'PLAN DÉTECTION', font=f, fill=(68, 114, 196))
    for i, (x, y) in enumerate(DET[:9]):
        x += rnd.randint(-40, 40); y += rnd.randint(-30, 30); r = rnd.choice([14, 18, 22])
        d.ellipse((x - r, y - r, x + r, y + r), fill=(68, 114, 196), outline=(47, 82, 143), width=2)
    pts = [(110, 380), (330, 250), (480, 470), (700, 260), (880, 480), (960, 300)]
    d.line(pts, fill=(255, 0, 0), width=3)
    d.rectangle((90, 360, 160, 400), fill=(112, 173, 71), outline=(80, 130, 50), width=2); d.text((97, 369), 'CMSI', font=F(20, True), fill=WHITE)
    for (bx, by, tx, ax, ay) in [(600, 440, 'Détecteur ici ?', 700, 300), (150, 560, 'câble à voir', 300, 470)]:
        w = F(20).getlength(tx) + 20
        d.line((bx + w / 2, by, ax, ay), fill=(0, 0, 0), width=2)
        d.polygon([(ax, ay), (ax - 8, ay + 12), (ax + 6, ay + 12)], fill=(0, 0, 0))
        d.rectangle((bx, by, bx + w, by + 34), fill=(255, 230, 153), outline=(191, 144, 0), width=2); d.text((bx + 10, by + 6), tx, font=F(20), fill=(0, 0, 0))
    d.rectangle((60, 672, 1000, 718), outline=(170, 170, 170), width=1)
    d.text((76, 684), 'Cliquez pour ajouter des notes', font=F(20), fill=(150, 150, 150))
    return finish(im, 'AVANT  ·  SUR POWERPOINT', RED, 'r')

def n7_apres():
    im, d = clean_plan('n7'); clean_walls(d)
    room_labels(d, ['DO · h 2,7 m', 'DO · h 2,7 m', 'DO · h 2,5 m', 'DOT · h 3,0 m', 'DO · h 6,0 m', 'DOT · h 6,0 m', 'DO · h 3,2 m'])
    d.line((140, 395, 930, 395), fill=RED, width=3)
    for x, y in DET:
        if y != 380: d.line((x, 395 if y > 380 else 395, x, y), fill=RED, width=3)
    d.line((860, 395, 860, 380), fill=RED, width=3)
    d.rounded_rectangle((80, 372, 150, 410), 5, fill=NAVY); d.text((91, 380), 'CMSI', font=F(18, True), fill=WHITE)
    for x, y in DET:
        d.ellipse((x - 16, y - 16, x + 16, y + 16), fill=WHITE, outline=NAVY, width=3)
        f = F(13, True); d.text((x - f.getlength('DO') / 2, y - 8), 'DO', font=f, fill=NAVY)
    for x, y in [(120, 330), (930, 630), (990, 380)]:
        d.rectangle((x - 12, y - 12, x + 12, y + 12), fill=RED); f = F(11, True); d.text((x - f.getlength('DM') / 2, y - 6), 'DM', font=f, fill=WHITE)
    badge(im, 'Boucle 1  ·  14 points  ·  R7 conforme')
    def s_do(d, x, y): d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=WHITE, outline=NAVY, width=3)
    def s_dm(d, x, y): d.rectangle((x - 9, y - 9, x + 9, y + 9), fill=RED)
    def s_ca(d, x, y): d.line((x - 12, y, x + 12, y), fill=RED, width=3)
    cartouche(d, 'DetectR7', [(s_do, 'Détecteur'), (s_dm, 'DM'), (s_ca, 'Câblage')])
    return finish(im, "APRÈS  ·  AVEC L'OUTIL", NAVY, 'l')

# --- N4
EXT = [(130, 380, 'EP6', 0), (330, 300, 'EP6', 0), (520, 380, 'EP6', 1), (760, 300, 'EP6', 0), (850, 160, 'CO2', 2), (960, 250, 'CO2', 0),
       (110, 600, 'EP9', 0), (390, 470, 'EP9', 2), (680, 600, 'EP6', 1), (960, 470, 'EP6', 0)]
def n4_avant():
    im, d, rnd = hand_plan((236, 236, 234), 9, (90, 90, 90))
    fl = Image.new('RGBA', (PW, PH), (0, 0, 0, 0)); fd = ImageDraw.Draw(fl)
    fd.line((90, 380, 980, 372), fill=(250, 240, 40, 120), width=34)
    fd.rectangle((810, 115, 990, 335), fill=(255, 80, 180, 70))
    fd.line((120, 560, 400, 610), fill=(120, 240, 90, 110), width=26)
    im.alpha_composite(fl); d = ImageDraw.Draw(im, 'RGBA')
    cols = [(220, 40, 40), (40, 160, 70), (240, 200, 30), (40, 100, 210)]
    for i, (x, y, ty, s) in enumerate(EXT[:8]):
        x += rnd.randint(-25, 25); y += rnd.randint(-25, 25); c = rnd.choice(cols)
        d.ellipse((x - 14, y - 14, x + 14, y + 14), fill=c + (255,)); d.ellipse((x - 8, y - 9, x - 2, y - 3), fill=(255, 255, 255, 120))
        if rnd.random() < 0.5: d.text((x + 16, y - 26), rnd.choice(['6L ?', 'à chg.', 'EP ?', 'CO2']), font=F(20, False, True), fill=(30, 50, 160, 220))
    d.text((80, 690), 'gommettes : rouge = ?  vert = ok ?  jaune = à voir', font=F(24, False, True), fill=(30, 50, 160, 220))
    return finish(im, 'AVANT  ·  GOMMETTES & FLUO', RED, 'r')

def n4_apres():
    im, d = clean_plan('n4')
    d.rectangle((800, OY0, OX1, CY0), fill=(253, 236, 214))
    for k in range(-300, 300, 22): d.line((800 + k, OY0, 800 + k + 245, CY0), fill=(245, 180, 110, 90), width=2)
    im2 = Image.new('RGBA', (PW, PH), (0, 0, 0, 0)); im2.paste(im, (0, 0)); im = im2; d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle((OX0, OY0, 800, OY1), outline=None); clean_walls(d); room_labels(d)
    d.text((816, 300), 'Risque électrique', font=F(17, True), fill=(200, 110, 30))
    for i, (x, y, ty, s) in enumerate(EXT):
        if s == 2:
            d.ellipse((x - 17, y - 17, x + 17, y + 17), fill=WHITE, outline=GREEN, width=4)
            d.line((x - 8, y, x + 8, y), fill=GREEN, width=4); d.line((x, y - 8, x, y + 8), fill=GREEN, width=4)
        else:
            d.ellipse((x - 17, y - 17, x + 17, y + 17), fill=RED if s == 0 else (170, 170, 180))
            f = F(17, True); n = str(i + 1); d.text((x - f.getlength(n) / 2, y - 10), n, font=f, fill=WHITE)
            if s == 1:
                d.ellipse((x + 8, y - 22, x + 26, y - 4), fill=(240, 140, 30)); d.line((x + 12, y - 18, x + 22, y - 8), fill=WHITE, width=3); d.line((x + 22, y - 18, x + 12, y - 8), fill=WHITE, width=3)
        d.text((x - F(14, True).getlength(ty) / 2, y + 20), ty, font=F(14, True), fill=NAVY)
    badge(im, 'Dotation R4 conforme  ·  règle des 15 m')
    def s_ok(d, x, y): d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=RED)
    def s_ref(d, x, y): d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=(170, 170, 180)); d.ellipse((x + 3, y - 13, x + 13, y - 3), fill=(240, 140, 30))
    def s_add(d, x, y): d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=WHITE, outline=GREEN, width=3)
    cartouche(d, 'N4 Conceptor', [(s_ok, 'En place'), (s_ref, 'À réformer'), (s_add, 'À ajouter')])
    return finish(im, "APRÈS  ·  AVEC L'OUTIL", NAVY, 'l')

class BA(Scene):
    PX, PY = 50, 135
    def __init__(s, dur, prefix, label, name, ref, rows, extras, plans):
        super().__init__(dur); s.prefix, s.label, s.name, s.ref, s.rows, s.extras, s.plans = prefix, label, name, ref, rows, extras, plans
        s.pa = s.pb = None
    def build(s):
        s.pa, s.pb = s.plans[0](), s.plans[1]()
        e = [title_el(s.prefix, '  –  Avant / Après')]
        X0 = 1140
        im, d = card(740, 128, fill=NAVY, border=None)
        p = pill(s.label, RED, F(16, True), h=32); im.paste(p, (M + 26, M + 18), p)
        d.text((M + 26 + p.width + 18, M + 18), s.ref, font=F(21), fill=A4)
        d.text((M + 26, M + 62), s.name, font=F(38, True), fill=WHITE)
        e.append(El(im, X0, 140, 0.4, 'up', 0.55, 40))
        e.append(text_el("AUJOURD'HUI", F(17, True), A5, 0.9, X0, 296, sp=3))
        e.append(text_el("AVEC L'OUTIL", F(17, True), RED, 4.6, X0 + 290, 296, sp=3))
        n = len(s.rows); rh = 118 if n == 3 else 96; gap = 14 if n == 3 else 12
        for i, (av, ti, tx) in enumerate(s.rows):
            y = 326 + i * (rh + gap)
            im, d = card(240, rh, fill=BG2, border=None, shadow=False)
            yy = M + rh / 2 - len(wrap(av, F(21), 205)) * 13
            mtext(d, (M + 18, yy), av, F(21), TX2, 205, 26)
            e.append(El(im, X0, y, 1.0 + 0.3 * i, 'left', 0.5, 40))
            t0 = 5.0 + (0.9 if n == 3 else 0.75) * i
            e.append(El(icon('image-11-1.png', 32), X0 + 246, y + rh / 2 - 16, t0, 'left', 0.35, 20, off=0))
            im, d = card(450, rh)
            d.ellipse((M + 16, M + rh / 2 - 19, M + 54, M + rh / 2 + 19), fill=NAVY)
            ck = icon('image-11-2.png', 20); im.paste(ck, (M + 25, int(M + rh / 2 - 10)), ck)
            fs = 22 if n == 3 else 21; ft = 18 if n == 3 else 17
            tl = wrap(tx, F(ft), 368); th = fs + 6 + len(tl) * (ft + 3)
            yy = M + (rh - th) / 2
            d.text((M + 68, yy), ti, font=F(fs, True), fill=NAVY)
            mtext(d, (M + 68, yy + fs + 6), tx, F(ft), TX2, 368, ft + 3)
            e.append(El(im, X0 + 290, y, t0 + 0.1, 'right', 0.55, 50))
        yb = 326 + n * (rh + gap) + 14
        e.append(text_el('ET AUSSI', F(17, True), RED, 8.6, X0, yb, sp=3))
        x, y = X0, yb + 32
        for i, c in enumerate(s.extras):
            p = pill(c, WHITE, F(19, True), fg=NAVY, padx=16, h=40, sp=0)
            ImageDraw.Draw(p).rounded_rectangle((0, 0, p.width - 1, 39), 20, outline=A4, width=2)
            if x + p.width > 1880: x = X0; y += 50
            e.append(El(p, x, y, 8.8 + 0.18 * i, 'pop', 0.4, off=0)); x += p.width + 10
        return e
    def wipe(s, t):
        if t < 3.0: return 0.0
        if t < 5.4: return eio((t - 3.0) / 2.4)
        if t < 10.6: return 1.0
        if t < 11.4: return 1 - 0.5 * eio((t - 10.6) / 0.8)
        if t < 12.6: return 0.5
        return 0.5 + 0.5 * eio(cl((t - 12.6) / 0.8))
    def extra(s, fr, t):
        if s.els is None: s.els = s.build()
        a = cl((t - 0.2) / 0.5)
        if a <= 0: return
        dy = (1 - eo(a)) * 40
        w = s.wipe(t); xw = int(PW * w)
        img = s.pa
        if xw > 0:
            img = s.pa.copy(); img.paste(s.pb.crop((0, 0, xw, PH)), (0, 0))
        sh = Image.new('RGBA', (PW + 40, PH + 40), (0, 0, 0, 0))
        paste(fr, img, s.PX, s.PY + dy, a)
        if 0.0 < w < 1.0 and t > 2.6:
            d = ImageDraw.Draw(fr); X = s.PX + xw; Y = s.PY + PH / 2
            d.rectangle((X - 3, s.PY, X + 3, s.PY + PH), fill=WHITE)
            d.line((X, s.PY, X, s.PY + PH), fill=NAVY, width=1)
            d.ellipse((X - 30, Y - 30, X + 30, Y + 30), fill=WHITE, outline=NAVY, width=3)
            d.polygon([(X - 20, Y), (X - 8, Y - 10), (X - 8, Y + 10)], fill=RED)
            d.polygon([(X + 20, Y), (X + 8, Y - 10), (X + 8, Y + 10)], fill=RED)
        elif w == 0 and 2.4 < t < 3.0:
            d = ImageDraw.Draw(fr); X = s.PX + 4; Y = s.PY + PH / 2; k = eo((t - 2.4) / 0.6)
            d.ellipse((X - 30 * k, Y - 30 * k, X + 30 * k, Y + 30 * k), fill=WHITE, outline=NAVY, width=3)

class Gains(Scene):
    def build(s):
        e = [title_el('', "Ce qu'Eurofeu y gagne")]
        cs = [('image-15-1.png', "Une longueur d'avance", 'Des études outillées, là où beaucoup travaillent encore à la main'),
              ('image-15-2.png', 'Des dossiers homogènes', 'Le même niveau de rendu dans toutes les agences, quel que soit le collaborateur'),
              ('image-15-3.png', 'Du temps gagné', "Moins de ressaisie pour les commerciaux, chargés d'affaires, techniciens et chefs d'agence"),
              ('image-15-4.png', 'Des dossiers plus professionnels', 'Plans, DOE et notes de calcul soignés : une meilleure image auprès des clients'),
              ('image-15-5.png', 'Des économies', 'Plus besoin de la licence Fathom (4 000 € par an) pour les notes de calcul RIA'),
              ('image-15-6.png', 'Une conformité mieux maîtrisée', 'Règles APSAD R4, R5 et R7 intégrées, avec contrôles automatiques')]
        for i, (ic, ti, tx) in enumerate(cs):
            im, d = card(570, 260)
            circ_icon(d, im, M + 66, M + 66, 76, RED, ic)
            mtext(d, (M + 122, M + 40 if len(wrap(ti, F(30, True), 420)) > 1 else M + 50), ti, F(30, True), NAVY, 420, 34)
            mtext(d, (M + 32, M + 128), tx, F(24), TX2, 506, 30)
            e.append(El(im, 70 + 605 * (i % 3), 170 + 300 * (i // 3), 0.3 + 0.4 * i, 'pop', 0.5))
        return e

class Valeur(Scene):
    def build(s):
        e = [title_el('', 'Ce que représentent ces modules')]
        im, d = card(620, 600, fill=NAVY, border=None)
        spaced(d, (M + 44, M + 170), 'COÛT GLOBAL ESTIMÉ', F(21, True), A4, 3)
        mtext(d, (M + 44, M + 350), 'C\'est ce que représentent de tels modules métier', F(28), WHITE, 530)
        e.append(El(im, 70, 170, 0.3, 'up', 0.6, 50))
        rows = [('image-16-1.png', 'Trois modules métier complets', 'N4 extincteurs, N5 RIA et N7 détection'),
                ('image-16-2.png', 'Des moteurs de calcul intégrés', 'Dotation R4, hydraulique RIA, règles R7'),
                ('image-16-3.png', 'Tous les livrables', 'Plans, DOE, notes de calcul, dossiers et devis'),
                ('image-16-4.png', 'Le temps passé', 'Conception, développement et mise au point, sur mon temps personnel')]
        for i, (ic, ti, tx) in enumerate(rows):
            im, d = card(1100, 132)
            circ_icon(d, im, M + 62, M + 66, 70, RED, ic)
            d.text((M + 120, M + 30), ti, font=F(30, True), fill=NAVY); d.text((M + 120, M + 72), tx, font=F(24), fill=TX2)
            e.append(El(im, 750, 170 + 156 * i, 0.9 + 0.35 * i, 'right', 0.55, 60))
        return e
    def post(s, fr, t):
        if t < 0.6: return
        v = int(100000 * eo(cl((t - 0.6) / 2.0)) / 1000) * 1000
        ImageDraw.Draw(fr).text((134, 410), f'≈ {v:,} €'.replace(',', ' '), font=F(104, True), fill=WHITE)

class Fin(Scene):
    def base(s, t): return kenburns('FIN-image-1.jpeg', t, s.dur, 1.06, 1.0)
    def build(s):
        return [text_el('OUTILS MÉTIER  ·  N4  ·  N5  ·  N7', F(30, True), A4, 0.8, W / 2, 940, 'up', 0.6, 30, center=True, sp=2)]
    def post(s, fr, t):
        k = cl((t - (s.dur - 0.9)) / 0.9)
        if k > 0:
            ov = Image.new('RGB', (W, H), (18, 20, 48)); fr.paste(Image.blend(fr, ov, k))

BA5 = lambda: BA(14, 'N5 · RIA', 'N5 · RIA', 'Implantation RIA Pro + HydraRIA', 'Référentiel APSAD R5',
    [('Ficelle ou règle sur le plan', "Implantation à l'échelle", 'Couverture calculée sur le plan, murs et obstacles pris en compte, alertes en direct'),
     ('Notes de calcul sous Fathom, 4 000 € par an', 'Note de calcul intégrée', "Pertes de charge, pression au RIA le plus défavorisé, temps d'arrivée d'eau"),
     ('DOE long à constituer', 'DOE généré', "Plans 2D et isométrique, matériel et fiches techniques réunis par l'outil")],
    ['Études multi-niveaux', 'Réseau en vue 3D isométrique', 'Choix du surpresseur', "Temps d'arrivée d'eau en poste sous air"], (n5_avant, n5_apres))
BA7 = lambda: BA(14, 'N7 · Détection', 'N7 · DÉTECTION', 'DetectR7', 'Référentiel APSAD R7',
    [('Étude longue, réalisée à la main sur plan', "Étude sur plan à l'échelle", 'Paramètres R7 par local, implantation des détecteurs et câblage dans le même outil'),
     ('Plan chantier dessiné sur PowerPoint', "Plans édités par l'outil", 'Implantation et câblage par niveau, prêts à être remis au client'),
     ('Plans DOE longs à réaliser', 'DOE généré', "Un dossier imprimable produit directement à partir de l'étude")],
    ['Du R-4 au R+9', 'CMSI adressable ou conventionnel', 'Bilan de puissance', 'Audit de conformité'], (n7_avant, n7_apres))
BA4 = lambda: BA(14, 'N4 · Extincteurs', 'N4 · EXTINCTEURS', 'N4 Conceptor', 'Référentiel APSAD R4',
    [('Dossier long à réaliser', 'Dotation calculée et placée', 'Zones, risques et règle des 15 m : la dotation R4 se place sur le plan'),
     ('Gommettes ou fluo selon le commercial', 'Plan numéroté et lisible', 'Le même rendu professionnel, quel que soit le commercial'),
     ('Technicien qui cherche les appareils', 'Parc existant repéré', 'Appareils en place, à réformer et à ajouter identifiés sur le plan'),
     ('Dossier Excel à remplir', 'Dossier N4 généré', 'Pochette, caractéristiques du site, audit de sécurité et plan en un clic')],
    ['Import du parc existant', 'Études multi-niveaux', 'Contrôle de conformité R4', 'Devis chiffré'], (n4_avant, n4_apres))

SCENES = [Intro(8), Origine(8),
          Divider(4, 'DIV_CONSTAT-image-1.jpeg', '1.', ['LE CONSTAT :', 'LES DIFFICULTÉS', 'DU TERRAIN']),
          Constat5(6), Constat7(6), Constat4(6), Freins(6),
          Divider(4, 'DIV_SOLUTIONS-image-1.jpeg', '2.', ['LES SOLUTIONS :', 'TROIS OUTILS', 'MÉTIER']),
          Logique(8), BA5(), BA7(), BA4(),
          Divider(4, 'DIV_APPORT-image-1.jpeg', '3.', ["L'APPORT POUR", 'EUROFEU']),
          Gains(8), Valeur(5), Fin(5)]
STARTS = []; acc = 0
for sc in SCENES: STARTS.append(acc); acc += sc.dur
TOTAL = acc
XF = 0.35

def frame_at(t):
    i = max(k for k in range(len(SCENES)) if STARTS[k] <= t + 1e-9)
    lt = t - STARTS[i]; fr = SCENES[i].render(lt)
    if i > 0 and lt < XF:
        prev = SCENES[i - 1].render(SCENES[i - 1].dur - 0.001)
        k = eio(lt / XF)
        fr = Image.blend(prev, fr, k)
    return fr

if __name__ == '__main__':
    if sys.argv[2] == 'still':
        for t in sys.argv[4:]:
            frame_at(float(t)).save(f'{sys.argv[3]}/still_{float(t):06.2f}.png')
        sys.exit()
    f0, f1, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-threads', '1', out], stdin=subprocess.PIPE)
    for n in range(f0, f1):
        p.stdin.write(frame_at(n / FPS).convert('RGB').tobytes())
    p.stdin.close(); p.wait()

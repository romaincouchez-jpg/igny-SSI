import sys, os, math, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import video as V
from video import (W, H, FPS, NAVY, RED, BG2, TX2, A4, A5, A3, GREEN, WHITE, F, icon, eo, eio, back, cl, wrap, mtext,
                   spaced, M, card, circ_icon, paste, El, text_el, bandeau, title_el, pill, Scene, Intro, Origine, Divider,
                   Freins, Logique, Gains, Valeur, Fin)
from PIL import Image, ImageDraw, ImageFilter, ImageChops

ASSETS = sys.argv[2]

# ---------------- asset helpers ----------------
_im = {}
def asset(name, box=None, trim=False, maxside=2400):
    k = (name, box, trim)
    if k not in _im:
        im = Image.open(os.path.join(ASSETS, name)).convert('RGB')
        if box:
            w, h = im.size; im = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
        if trim:
            bgc = Image.new('RGB', im.size, (255, 255, 255))
            bb = ImageChops.difference(im, bgc).convert('L').point(lambda v: 255 if v > 18 else 0).getbbox()
            if bb: im = im.crop((max(0, bb[0] - 8), max(0, bb[1] - 8), min(im.width, bb[2] + 8), min(im.height, bb[3] + 8)))
        im.thumbnail((maxside, maxside), Image.LANCZOS)
        _im[k] = im
    return _im[k]

_fitc = {}
def fit(im, w, h, cover=False):
    cacheable = any(v is im for v in _im.values())
    k = (id(im), w, h, cover)
    if cacheable and k in _fitc: return _fitc[k]
    r = _fit(im, w, h, cover)
    if cacheable: _fitc[k] = r
    return r

def _fit(im, w, h, cover=False):
    s = (max if cover else min)(w / im.width, h / im.height)
    r = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    if cover:
        x0 = (r.width - w) // 2; y0 = (r.height - h) // 2; r = r.crop((x0, y0, x0 + w, y0 + h))
    return r

def kb(im, w, h, t, dur, z0=1.0, z1=1.12, ax=0.5, ay=0.5, cover=True):
    """Ken Burns: cover-crop im into w×h with a slow zoom toward (ax, ay)."""
    s = max(w / im.width, h / im.height) if cover else min(w / im.width, h / im.height)
    z = z0 + (z1 - z0) * eio(cl(t / dur))
    cw, ch = w / (s * z), h / (s * z)
    cw, ch = min(cw, im.width), min(ch, im.height)
    x0 = (im.width - cw) * ax; y0 = (im.height - ch) * ay
    return im.resize((w, h), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))

_cc = {}
def contain_on(im, w, h, bgc=WHITE):
    k = (id(im), w, h)
    if k in _cc and any(v is im for v in _im.values()): return _cc[k]
    out = Image.new('RGB', (w, h), bgc); r = fit(im, w, h); out.paste(r, ((w - r.width) // 2, (h - r.height) // 2)); _cc[k] = out; return out

def shadow_frame(fr, x, y, w, h, r=14):
    sh = Image.new('RGBA', (w + 60, h + 60), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((30, 36, 30 + w, 36 + h), r, fill=(39, 43, 96, 55))
    sh = sh.filter(ImageFilter.GaussianBlur(12)); fr.paste(sh, (x - 30, y - 30), sh)

_rm = {}
def rmask(w, h, r=14):
    if (w, h, r) not in _rm:
        m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255); _rm[(w, h, r)] = m
    return _rm[(w, h, r)]

def put_round(fr, img, x, y, a=1.0, r=14):
    m = rmask(img.width, img.height, r)
    if a < 0.99: m = m.point(lambda v: int(v * a))
    fr.paste(img, (int(x), int(y)), m)

def caption(fr, text, x, y, f=None, fill=NAVY, fg=WHITE):
    f = f or F(22, True); w = int(f.getlength(text)) + 28
    d = ImageDraw.Draw(fr); d.rounded_rectangle((x, y, x + w, y + 38), 8, fill=fill); d.text((x + 14, y + 7), text, font=f, fill=fg)

# ---------------- constat unique ----------------
class Constat(Scene):
    COLS = [('N5 · RIA', [('an-2.png', (0.0, 0.0, 1.0, 1.0), 'Étude à la cordelette'), ('an-3.png', (0.0, 0.0, 1.0, 1.0), 'Plan sur PowerPoint')],
             [('image-5-1.png', 'Étude complexe et approximative, à la cordelette'), ('image-6-3.png', 'Plan redessiné sur PowerPoint'),
              ('image-5-3.png', 'Notes de calcul Fathom : 4 000 € / an')]),
            ('N7 · DÉTECTION', [('an-5.png', (0.0, 0.0, 1.0, 1.0), 'Étude sur PowerPoint'), ('an-6.png', (0.0, 0.0, 1.0, 1.0), 'Plan technicien approximatif')],
             [('image-6-1.png', 'Étude longue, faite à la main'), ('image-6-5.png', 'DOE long à réaliser'),
              ('image-7-3.png', 'Plan technicien approximatif')]),
            ('N4 · EXTINCTEURS', [('an-7.png', (0.0, 0.0, 1.0, 1.0), 'Fluo et gommettes'), ('an-7.png', (0.3, 0.25, 0.75, 0.75), 'Plan technicien approximatif')],
             [('image-7-2.png', 'Dossiers non homogènes : fluo, gommettes'), ('image-7-3.png', 'Plan technicien approximatif'),
              ('image-7-4.png', "Dossier Excel rempli à la main")])]
    X = [60, 670, 1280]; CW = 580; IY = 210; IH = 360
    def build(s):
        e = [title_el('', 'Le constat : les difficultés du terrain'), El(pill('AVANT', RED), 1730, 46, 0.3, 'pop', 0.4, off=0)]
        for i, (lab, imgs, bul) in enumerate(s.COLS):
            t0 = 0.6 + 4.2 * i; x = s.X[i]
            im, d = card(s.CW, 54, fill=NAVY, r=8, border=None, shadow=False)
            spaced(d, (M + s.CW / 2, M + 12), lab, F(26, True), WHITE, 3, center=True)
            e.append(El(im, x, 140, t0, 'down', 0.5, 30))
            for j, (ic, tx) in enumerate(bul):
                im, d = card(s.CW, 76, border=None, shadow=False, fill=WHITE)
                circ_icon(d, im, M + 38, M + 38, 54, RED, ic)
                mtext(d, (M + 80, M + 38 - len(wrap(tx, F(25, True), 480)) * 15), tx, F(25, True), NAVY, 480, 30)
                e.append(El(im, x, 600 + 88 * j, t0 + 1.0 + 0.5 * j, 'up', 0.5, 30))
        e.append(bandeau('Résultat : des plans refaits à chaque étape, des dossiers inégaux, du temps perdu', 14.2, 872, h=60))
        return e
    def extra(s, fr, t):
        for i, (lab, imgs, bul) in enumerate(s.COLS):
            t0 = 0.6 + 4.2 * i + 0.3
            a = cl((t - t0) / 0.6)
            if a <= 0: continue
            x = s.X[i]; dy = int((1 - eo(a)) * 40)
            shadow_frame(fr, x, s.IY + dy, s.CW, s.IH)
            per = 4.5; k = int(max(0, t - t0) // per) % 2; lt = (max(0, t - t0)) % per
            nm, box, cap = imgs[k]
            img = kb(asset(nm, box, trim=True, maxside=1800), s.CW, s.IH, lt, per, 1.0, 1.10, 0.5, 0.5)
            if lt < 0.5 and t - t0 > per:
                pn, pb, _ = imgs[1 - k]
                prev = kb(asset(pn, pb, trim=True, maxside=1800), s.CW, s.IH, per, per, 1.0, 1.10)
                img = Image.blend(prev, img, eio(lt / 0.5))
            put_round(fr, img, x, s.IY + dy, a)
            if a >= 1: caption(fr, cap, x + 14, s.IY + s.IH - 52, F(21, True), RED)

# ---------------- solution scenes ----------------
SX, SY, SW, SH = 50, 140, 1210, 770
class Sol(Scene):
    """Left: stage showing the real deliverable for the current beat. Right: tool card + benefit list."""
    def __init__(s, dur, prefix, label, name, beats):
        super().__init__(dur); s.prefix, s.label, s.name, s.beats = prefix, label, name, beats  # beats: (t0, title, sub, fn)
    def build(s):
        e = [title_el(s.prefix, "  –  Avec l'outil"), El(pill('APRÈS', NAVY), 1716, 46, 0.3, 'pop', 0.4, off=0)]
        im, d = card(590, 120, fill=NAVY, border=None)
        p = pill(s.label, RED, F(17, True), h=34); im.paste(p, (M + 28, M + 18), p)
        d.text((M + 28, M + 60), s.name, font=F(36, True), fill=WHITE)
        e.append(El(im, 1290, 140, 0.4, 'up', 0.5, 40))
        return e
    def beat(s, t):
        k = 0
        for i, b in enumerate(s.beats):
            if t >= b[0]: k = i
        return k
    def extra(s, fr, t):
        k = s.beat(t); b = s.beats[k]; lt = t - b[0]
        nxt = s.beats[k + 1][0] if k + 1 < len(s.beats) else s.dur
        a = cl((t - 0.2) / 0.5)
        shadow_frame(fr, SX, SY, SW, SH)
        stage = Image.new('RGB', (SW, SH), WHITE)
        b[3](stage, lt, nxt - b[0])
        if k > 0 and lt < 0.5:
            pb = s.beats[k - 1]; prev = Image.new('RGB', (SW, SH), WHITE); pb[3](prev, b[0] - pb[0], b[0] - pb[0])
            stage = Image.blend(prev, stage, eio(lt / 0.5))
        put_round(fr, stage, SX, SY, a)
        ImageDraw.Draw(fr).rounded_rectangle((SX, SY, SX + SW - 1, SY + SH - 1), 14, outline=A4, width=2)
        # benefit list
        y = 300
        for i, (bt, ti, sub, fn) in enumerate(s.beats):
            ap = cl((t - min(bt, 0.8 + 0.3 * i)) / 0.4)
            if ap <= 0: continue
            h = 170 if i == k else 104
            d = ImageDraw.Draw(fr)
            if i == k:
                d.rounded_rectangle((1290, y, 1880, y + h), 12, fill=NAVY)
                d.ellipse((1312, y + 24, 1364, y + 76), fill=RED)
                fn_ = F(26, True); n = str(i + 1); d.text((1338 - fn_.getlength(n) / 2, y + 34), n, font=fn_, fill=WHITE)
                yy = mtext(d, (1384, y + 22), ti, F(31, True), WHITE, 470, 36)
                mtext(d, (1384, yy + 8), sub, F(23), A4, 470, 28)
            else:
                done = i < k
                d.rounded_rectangle((1290, y, 1880, y + h), 12, fill=WHITE if done else BG2, outline=A4, width=2)
                d.ellipse((1312, y + h / 2 - 22, 1356, y + h / 2 + 22), fill=NAVY if done else A4)
                if done:
                    ck = icon('image-11-2.png', 24); fr.paste(ck, (1322, int(y + h / 2 - 12)), ck)
                else:
                    fn_ = F(22, True); n = str(i + 1); d.text((1334 - fn_.getlength(n) / 2, y + h / 2 - 13), n, font=fn_, fill=WHITE)
                mtext(d, (1376, y + h / 2 - len(wrap(ti, F(26, True), 480)) * 16), ti, F(26, True), NAVY if done else A5, 480, 32)
            y += h + 14

# ---- stage painters (stage is SW×SH RGB) ----
def p_doc(name, box=None, z0=1.0, z1=1.15, ax=0.5, ay=0.5, cap=None, cover=False, margin=24):
    def f(st, lt, dur):
        src = asset(name, box, trim=True, maxside=2600)
        w, h = SW - 2 * margin, SH - 2 * margin
        if cover: img = kb(src, w, h, lt, dur, z0, z1, ax, ay)
        else:
            base = contain_on(src, w, h)
            img = kb(base, w, h, lt, dur, z0, z1, ax, ay)
        st.paste(img, (margin, margin))
        if cap: caption(st, cap, margin + 16, SH - margin - 54, F(22, True), NAVY)
    return f

def p_seq(items, per):
    fns = [p_doc(*it[0], **it[1]) for it in items]
    def f(st, lt, dur):
        k = min(len(fns) - 1, int(lt // per)); l2 = lt - k * per
        fns[k](st, l2, per)
        if k > 0 and l2 < 0.5:
            pv = Image.new('RGB', st.size, WHITE); fns[k - 1](pv, per, per); st.paste(Image.blend(pv, st, eio(l2 / 0.5)))
    return f

def p_doe(pages, label, total, cover):
    """DOE generation: progress bar, page thumbnails filling a grid, then the cover page."""
    def f(st, lt, dur):
        d = ImageDraw.Draw(st)
        tend = dur - 3.5
        prog = cl((lt - 0.6) / (tend - 0.6))
        d.text((40, 30), label, font=F(32, True), fill=NAVY)
        d.rounded_rectangle((40, 84, SW - 40, 104), 10, fill=BG2)
        if prog > 0: d.rounded_rectangle((40, 84, 40 + (SW - 80) * prog, 104), 10, fill=RED)
        n = int(round(total * prog)); txt = f'{n} / {total} pages'
        d.text((SW - 40 - F(26, True).getlength(txt), 34), txt, font=F(26, True), fill=RED if prog < 1 else GREEN)
        cols, rows = 7, 2; tw, th = 150, 212; gx = (SW - cols * tw) / (cols + 1)
        for i, pg in enumerate(pages[:cols * rows]):
            ti = 0.6 + (tend - 0.6) * i / (cols * rows)
            p = cl((lt - ti) / 0.35)
            if p <= 0: continue
            x = int(gx + (i % cols) * (tw + gx)); y = int(150 + (i // cols) * (th + 40))
            th_img = fit(asset(pg, maxside=600), tw, th)
            sc = 0.6 + 0.4 * eo(p)
            if sc < 1: th_img = th_img.resize((max(1, int(th_img.width * sc)), max(1, int(th_img.height * sc))), Image.BILINEAR)
            ox = x + (tw - th_img.width) // 2; oy = y + (th - th_img.height) // 2
            d.rectangle((ox + 4, oy + 6, ox + th_img.width + 4, oy + th_img.height + 6), fill=(220, 222, 234))
            st.paste(th_img, (ox, oy)); d.rectangle((ox, oy, ox + th_img.width, oy + th_img.height), outline=A4)
        pc = cl((lt - tend) / 0.7)
        if pc > 0:
            ov = Image.new('RGB', st.size, WHITE); cimg = fit(asset(cover, maxside=1400), 760, SH - 150)
            ov.paste(cimg, ((SW - cimg.width) // 2 - 150, 120))
            od = ImageDraw.Draw(ov); od.rectangle(((SW - cimg.width) // 2 - 150, 120, (SW + cimg.width) // 2 - 150, 120 + cimg.height), outline=A4, width=2)
            od.text((40, 30), label, font=F(32, True), fill=NAVY)
            bx = (SW + cimg.width) // 2 - 110; by = SH // 2 - 60
            od.rounded_rectangle((bx, by, bx + 400, by + 120), 16, fill=(232, 246, 238), outline=GREEN, width=3)
            od.ellipse((bx + 22, by + 32, bx + 78, by + 88), fill=GREEN); ck = icon('image-11-2.png', 30); ov.paste(ck, (bx + 35, by + 45), ck)
            od.text((bx + 96, by + 26), 'DOE prêt', font=F(36, True), fill=GREEN)
            od.text((bx + 96, by + 70), f'{total} pages générées', font=F(24), fill=TX2)
            st.paste(Image.blend(st, ov, eio(pc)))
    return f

def p_hydra(st, lt, dur):
    """Pertes de charge + vue isométrique (illustration du principe HydraRIA)."""
    d = ImageDraw.Draw(st)
    d.text((40, 30), 'Vue isométrique du réseau', font=F(30, True), fill=NAVY)
    d.text((660, 30), 'Note de calcul – pertes de charge', font=F(30, True), fill=NAVY)
    # isometric network
    def iso(x, y, z): return (330 + (x - y) * 0.866 * 34, 470 + (x + y) * 0.5 * 34 - z * 34)
    segs = [((0, 0, 0), (0, 0, 6)), ((0, 0, 6), (8, 0, 6)), ((8, 0, 6), (8, 6, 6)), ((3, 0, 6), (3, -4, 6)), ((8, 6, 6), (2, 6, 6)),
            ((3, -4, 6), (3, -4, 4)), ((8, 3, 6), (8, 3, 4)), ((2, 6, 6), (2, 6, 4)), ((5, 0, 6), (5, 0, 4))]
    p = cl((lt - 0.3) / 3.0); n = len(segs)
    for i, (a, b) in enumerate(segs):
        q = cl(p * n - i)
        if q <= 0: continue
        A = iso(*a); B = iso(*b); Bq = (A[0] + (B[0] - A[0]) * q, A[1] + (B[1] - A[1]) * q)
        d.line((A, Bq), fill=A3, width=7)
    if p >= 1:
        for k, pt in enumerate([(3, -4, 4), (8, 3, 4), (2, 6, 4), (5, 0, 4)]):
            x, y = iso(*pt); d.rounded_rectangle((x - 17, y - 14, x + 17, y + 14), 4, fill=RED)
            d.text((x + 22, y - 12), f'RIA {k + 1}', font=F(18, True), fill=NAVY)
        x, y = iso(0, 0, 0); d.ellipse((x - 20, y - 20, x + 20, y + 20), fill=NAVY); d.text((x - 12, y - 10), 'CS', font=F(17, True), fill=WHITE)
    # calc table
    rows = [('Tronçon', 'DN', 'Débit', 'ΔP (bar)'), ('CS → T1', '50', '7,2 m³/h', '0,18'), ('T1 → RIA 1', '32', '3,6 m³/h', '0,21'),
            ('T1 → T2', '40', '3,6 m³/h', '0,12'), ('T2 → RIA 3', '32', '3,6 m³/h', '0,26'), ('RIA défavorisé', '', 'P = 2,6 bar', 'OK')]
    x0, y0, cw = 660, 100, [190, 70, 130, 110]
    for r, row in enumerate(rows):
        ta = 1.0 + 0.7 * r
        if lt < ta: break
        y = y0 + r * 62; hdr = r == 0; last = r == len(rows) - 1
        d.rectangle((x0, y, x0 + sum(cw), y + 56), fill=NAVY if hdr else ((232, 246, 238) if last else (BG2 if r % 2 else WHITE)))
        xx = x0
        for c, v in enumerate(row):
            d.text((xx + 12, y + 14), v, font=F(22, True if (hdr or last) else False), fill=WHITE if hdr else (GREEN if last else NAVY)); xx += cw[c]
    d.rectangle((x0, y0, x0 + sum(cw), y0 + 62 * len(rows) - 6), outline=A4, width=2)
    d.text((40, SH - 50), 'Exemple de calcul', font=F(18, False, True), fill=A5)

def p_click(button, cursor_t, then):
    def f(st, lt, dur):
        if lt < cursor_t + 0.6:
            d = ImageDraw.Draw(st)
            src = asset('doe7_2.png', trim=True, maxside=2000); bgimg = contain_on(src, SW - 48, SH - 48)
            st.paste(Image.blend(bgimg, Image.new('RGB', bgimg.size, WHITE), 0.55), (24, 24))
            bw, bh = 460, 96; bx, by = (SW - bw) // 2, (SH - bh) // 2
            press = 1 if cursor_t <= lt < cursor_t + 0.25 else 0
            d.rounded_rectangle((bx + 4, by + 8, bx + bw + 4, by + bh + 8), 18, fill=(200, 202, 220))
            d.rounded_rectangle((bx + 2 * press, by + 4 * press, bx + bw + 2 * press, by + bh + 4 * press), 18, fill=RED)
            fb = F(36, True); d.text((bx + bw / 2 - fb.getlength(button) / 2, by + 26), button, font=fb, fill=WHITE)
            cp = eio(cl(lt / cursor_t)); cx = SW - 120 + (bx + bw * 0.62 - (SW - 120)) * cp; cy = SH - 60 + (by + bh * 0.6 - (SH - 60)) * cp
            pts = [(0, 0), (0, 34), (9, 26), (16, 41), (22, 38), (15, 24), (27, 24)]
            d.polygon([(cx + x, cy + y) for x, y in pts], fill=NAVY, outline=WHITE)
            if lt >= cursor_t:
                r = 20 + 60 * cl((lt - cursor_t) / 0.5); d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=RED, width=3)
        else:
            then(st, lt - cursor_t - 0.6, dur - cursor_t - 0.6)
    return f

EXL_ROWS = [449, 569, 593, 617, 689]
def p_excel(st, lt, dur):
    src = asset('excel.png', (0, 130 / 955, 1300 / 1820, 1.0), maxside=3000).copy()
    blank = src.copy(); bd = ImageDraw.Draw(blank)
    for y in EXL_ROWS: bd.rectangle((540, y - 130 - 10, 600, y - 130 + 11), fill=(255, 242, 204))
    img = blank
    for i, y in enumerate(EXL_ROWS):
        ti = 1.6 + 1.1 * i
        if lt >= ti:
            yy = y - 130; img.paste(src.crop((519, yy - 11, 617, yy + 12)), (519, yy - 11))
            g = cl(1 - (lt - ti) / 1.0)
            if g > 0:
                hd = ImageDraw.Draw(img, 'RGBA'); hd.rectangle((517, yy - 12, 619, yy + 12), outline=(30, 158, 90, int(255 * g)), width=4)
    w, h = SW - 40, SH - 140
    out = fit(img, w, h); st.paste(out, ((SW - out.width) // 2, 110))
    d = ImageDraw.Draw(st)
    d.text((30, 28), 'Chiffrage Eurofeu  ·  detectr7_chiffrage', font=F(30, True), fill=NAVY)
    done = min(len(EXL_ROWS), max(0, int((lt - 1.6) // 1.1) + 1)) if lt >= 1.6 else 0
    msg = f'Quantités reportées automatiquement : {done} / {len(EXL_ROWS)}'
    col = GREEN if done == len(EXL_ROWS) else RED
    d.rounded_rectangle((SW - 40 - F(24, True).getlength(msg) - 40, 22, SW - 30, 72), 25, fill=(232, 246, 238) if done == len(EXL_ROWS) else (253, 232, 232))
    d.text((SW - 40 - F(24, True).getlength(msg) - 20, 33), msg, font=F(24, True), fill=col)

def p_dossier(pages, per):
    def f(st, lt, dur):
        k = min(len(pages) - 1, int(lt // per)); l2 = lt - k * per
        d = ImageDraw.Draw(st)
        # stack of previous pages behind
        for j in range(max(0, k - 3), k):
            off = (k - j) * 14
            pg = fit(asset(pages[j], maxside=1600), SW - 260, SH - 150)
            st.paste(Image.blend(pg, Image.new('RGB', pg.size, WHITE), 0.6), (130 - off, 110 - off))
        pg = fit(asset(pages[k], maxside=1600), SW - 260, SH - 150)
        px, py = 130, 110
        sl = eo(cl(l2 / 0.45)); px2 = int(px + (1 - sl) * 300)
        tmp = pg.copy()
        # auto-fill sweep
        sw = cl((l2 - 0.4) / (per - 1.0))
        if sw > 0:
            ov = Image.new('RGBA', tmp.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
            yy = int(tmp.height * sw)
            od.rectangle((0, 0, tmp.width, yy), fill=(30, 158, 90, 22)); od.rectangle((0, yy - 6, tmp.width, yy), fill=(30, 158, 90, 160))
            tmp = Image.alpha_composite(tmp.convert('RGBA'), ov).convert('RGB')
        d.rectangle((px2 + 6, py + 8, px2 + tmp.width + 6, py + tmp.height + 8), fill=(215, 217, 232))
        st.paste(tmp, (px2, py)); d.rectangle((px2, py, px2 + tmp.width, py + tmp.height), outline=A4, width=2)
        d.text((30, 28), 'Dossier N4 Eurofeu  ·  complété automatiquement', font=F(30, True), fill=NAVY)
        msg = f'Page {k + 1} / {len(pages)}' if not (k == len(pages) - 1 and sw >= 1) else 'Dossier complet'
        d.rounded_rectangle((SW - 300, 22, SW - 30, 72), 25, fill=(232, 246, 238)); d.text((SW - 280, 33), msg, font=F(24, True), fill=GREEN)
    return f

def p_dark(name, cap, z1=1.08):
    """Screenshot on a dark stage (vue isométrique)."""
    def f(st, lt, dur):
        st.paste(Image.new('RGB', st.size, (10, 12, 18)))
        img = kb(contain_on(asset(name, maxside=2000), SW - 40, SH - 140, (10, 12, 18)), SW - 40, SH - 140, lt, dur, 1.0, z1)
        st.paste(img, (20, 90))
        ImageDraw.Draw(st).text((30, 28), cap, font=F(30, True), fill=WHITE)
    return f

def p_fps_collage(st, lt, dur):
    """FPS views as a collage (used for the PowerPoint)."""
    big = fit(asset('iso1.png', maxside=2000), 760, SH - 60, cover=True)
    st.paste(big, (24, 30))
    for j, n in enumerate(('iso2.png', 'iso3.png')):
        sm = fit(asset(n, maxside=2000), SW - 24 - 800 - 24, (SH - 60 - 20) // 2, cover=True)
        st.paste(sm, (24 + 760 + 20, 30 + j * ((SH - 60 - 20) // 2 + 20)))
    caption(st, 'Vue FPS : visite du réseau en 3D', 44, SH - 90, F(22, True), NAVY)

N5 = Sol(40, 'N5 · RIA', 'N5 · RIA', 'Implantation RIA Pro + HydraRIA', [
    (0, 'Un plan propre, une étude professionnelle', "Implantation à l'échelle, couverture calculée", p_doc('doe5_13.png', (0.06, 0.15, 0.94, 0.75), 1.0, 1.25, 0.45, 0.6, cap="Plan d'implantation – DOE RIA")),
    (10, 'Vue isométrique et pertes de charge', 'Réseau en 3D, note de calcul HydraRIA intégrée', p_dark('iso4.png', 'Vue isométrique du réseau RIA')),
    (18, 'Vue FPS : visite du réseau en 3D', 'Se déplacer dans le bâtiment comme sur site', p_seq([
        (('iso1.png', None, 1.0, 1.08, 0.5, 0.5, 'Vue FPS – déplacement libre'), {'cover': True, 'margin': 0}),
        (('iso2.png', None, 1.0, 1.08, 0.5, 0.5, 'Vue FPS – le long du réseau'), {'cover': True, 'margin': 0}),
        (('iso3.png', None, 1.0, 1.08, 0.5, 0.5, 'Vue FPS – source d\'eau et surpresseur'), {'cover': True, 'margin': 0})], 3.4)),
    (28, 'Le DOE se génère tout seul', 'Réception, plans, fiches techniques : tout est réuni',
     p_doe(['doe5_1.png', 'doe5_3.png', 'doe5_4.png', 'doe5_13.png', 'doe5_16.png', 'doe5_17.png', 'doe5_18.png', 'doe5_19.png', 'doe5_21.png',
            'doe5_22.png', 'doe5_23.png', 'doe5_25.png', 'doe5_26.png', 'doe5_28.png'], 'Génération du DOE RIA…', 37, 'doe5_1.png'))])

N7 = Sol(34, 'N7 · Détection', 'N7 · DÉTECTION', 'DetectR7', [
    (0, 'Un plan propre, une étude professionnelle', 'Implantation, câblage et synoptique', p_seq([
        (('doe7_2.png', (0.22, 0.15, 0.78, 0.75), 1.0, 1.2, 0.3, 0.3, "Plan d'implantation et câblage"), {}),
        (('doe7_5.png', (0.0, 0.0, 0.55, 0.42), 1.0, 1.1, 0.2, 0.3, 'Synoptique de détection'), {})], 5.0)),
    (10, 'Le DOE en 1 clic', "Le dossier complet, directement à partir de l'étude",
     p_click('Générer le DOE', 1.2, p_doe(['doe7_%d.png' % i for i in range(1, 14)], 'Génération du DOE détection…', 13, 'doe7_1.png'))),
    (20, 'Le chiffrage Eurofeu se remplit tout seul', 'Le fichier Excel Eurofeu complété automatiquement', p_excel)])

N4 = Sol(32, 'N4 · Extincteurs', 'N4 · EXTINCTEURS', 'N4 Conceptor', [
    (0, 'Le dossier N4 Eurofeu se complète tout seul', 'Pochette, établissement, audit R4, relevé',
     p_dossier(['dn4_1.png', 'dn4_2.png', 'dn4_4.png', 'dn4_8.png', 'dn4_12.png'], 2.4)),
    (12, "Le plan de l'étude", 'Dotation R4 numérotée, posée sur le plan du site', p_doc('n4_2.png', None, 1.0, 1.15, 0.5, 0.45, cap="Plan d'implantation – étude N4")),
    (22, 'Un plan technicien professionnel pour intervenir', 'Appareils à remplacer repérés, liste prête', p_seq([
        (('tech_2.png', None, 1.0, 1.08, 0.5, 0.5, 'Plan technicien – remplacement'), {}),
        (('tech_2.png', (0.0, 0.12, 0.62, 0.98), 1.0, 1.35, 0.6, 0.55, 'Appareils repérés sur le plan'), {})], 5.0))])

SCENES = [Intro(8), Origine(12),
          Divider(4, 'DIV_CONSTAT-image-1.jpeg', '1.', ['LE CONSTAT :', 'LES DIFFICULTÉS', 'DU TERRAIN']),
          Constat(30), Freins(10),
          Divider(4, 'DIV_SOLUTIONS-image-1.jpeg', '2.', ['LES SOLUTIONS :', 'TROIS OUTILS', 'MÉTIER']),
          Logique(12), N5, N7, N4,
          Divider(4, 'DIV_APPORT-image-1.jpeg', '3.', ["L'APPORT POUR", 'EUROFEU']),
          Gains(16), Valeur(10), Fin(6)]
V.SCENES[:] = SCENES
V.STARTS[:] = []
acc = 0
for sc in SCENES: V.STARTS.append(acc); acc += sc.dur
TOTAL = acc

if __name__ == '__main__':
    if sys.argv[3] == 'still':
        for t in sys.argv[5:]:
            V.frame_at(float(t)).save(f'{sys.argv[4]}/s2_{float(t):06.2f}.png')
        sys.exit()
    if sys.argv[3] == 'total': print(TOTAL); sys.exit()
    f0, f1, out = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-threads', '1', out], stdin=subprocess.PIPE)
    for n in range(f0, f1):
        p.stdin.write(V.frame_at(n / FPS).convert('RGB').tobytes())
    p.stdin.close(); p.wait()

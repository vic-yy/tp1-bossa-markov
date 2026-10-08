"""Leitura do MPB Corpus (CC BY 4.0, github.com/ProjetoMPB/mpb-corpus) e decodificacao em notas.

Harmonia: estado = (raiz relativa a tonica, simbolo do acorde, duracao em compassos).
Melodia: letras de contorno (u=repete, P/p=grau conjunto acima/abaixo, A/a=arpejo 3-5 st, S/s=salto >=6 st).
"""
import csv, os, re
from collections import OrderedDict

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "mpb_corpus", "dataset_by_corpus")
SCALES = {"major": [0, 2, 4, 5, 7, 9, 11], "minor": [0, 2, 3, 5, 7, 8, 10]}
TONIC = {"major": 0, "minor": 9}  # saida em Do maior / La menor
DURS = [0.5, 1.0, 2.0, 4.0]       # duracoes de acorde (compassos)


def _rows(composer, table):
    with open(os.path.join(DATA, composer, table + ".csv"), encoding="utf8") as f:
        return list(csv.DictReader(f))


def load_harmony(composers=("JOBIM",), mode="major"):
    """Lista de sequencias de acordes (trechos de modo constante) normalizadas para tonica 0."""
    out = []
    for c in composers:
        comps = OrderedDict()
        for r in _rows(c, "harmony"):
            comps.setdefault(r["composition_id"], []).append(r)
        for rows in comps.values():
            pos = [float(r["position"]) for r in rows]
            run = []
            for i, r in enumerate(rows):
                dur = (pos[i + 1] - pos[i]) if i + 1 < len(rows) else 1.0
                dur = min(DURS, key=lambda d: abs(d - dur)) if dur > 0 else 1.0
                st = ((int(r["root"]) - int(r["key"])) % 12, r["chord_symbol"], dur)
                if r["mode"] == mode:
                    run.append(st)
                elif run:
                    out.append(run)
                    run = []
            if run:
                out.append(run)
    return [s for s in out if len(s) >= 6]


def load_contour(composers=("JOBIM",)):
    """Sequencias de letras de contorno; '|' separa segmentos (frases)."""
    out = []
    for c in composers:
        comps = OrderedDict()
        for r in _rows(c, "contour_rhythm"):
            comps.setdefault(r["composition_id"], []).append(r["c_word"])
        for words in comps.values():
            s = []
            for w in words:
                s += list(w) + ["|"]
            out.append(s)
    return out


_HALF, _DIM = set("Øø"), set("°o")


def chord_tones(sym):
    """Intervalos (semitons a partir da raiz): [0, 3a, 5a, 7a/6a (se houver), extensoes...]."""
    s = sym.lstrip("*")
    third, fifth, seventh, dim = 4, 7, None, False
    if s[:1] == "m":
        third, s = 3, s[1:]
        if s.startswith("M7"):
            seventh, s = 11, s[2:]
    elif s[:1] in _HALF:
        third, fifth, seventh, s = 3, 6, 10, s[1:]
    elif s[:1] in _DIM:
        third, fifth, dim, s = 3, 6, True, s[1:]
    elif s[:1] == "4":
        third, s = 5, s[1:]
    for tok, iv in (("(#5)", 8), ("(b5)", 6)):
        if tok in s:
            fifth, s = iv, s.replace(tok, "")
    if seventh is None:
        if "M7" in s:
            seventh, s = 11, s.replace("M7", "", 1)
        elif "7" in s:
            seventh, s = (9 if dim else 10), s.replace("7", "", 1)
        elif "6" in s:
            seventh, s = 9, s.replace("6", "", 1)
    ext = [{9: 14, 11: 17, 13: 21, 14: 14}[int(n)] + (1 if a == "#" else -1 if a == "b" else 0)
           for a, n in re.findall(r"([#b]?)(9|11|13|14)", s)]
    return [0, third, fifth] + ([seventh] if seventh is not None else []) + ext


def decode_melody(letters, chord_at, mode, total_beats, durs=(1.5, .5, 1, 1, 1.5, .5, 2)):
    """Converte letras de contorno em notas (pitch, inicio, dur) sobre a harmonia.
    chord_at(t) -> classes de altura do acorde em t. Cada segmento comeca em um tom do acorde."""
    scale = {(TONIC[mode] + d) % 12 for d in SCALES[mode]}
    notes, t, p, k, new = [], 0.0, 67, 0, True

    def nearest_chord_tone(p, t):
        pcs = chord_at(t)
        return min((q for q in range(55, 85) if q % 12 in pcs), key=lambda q: abs(q - p))

    def step(p, sign):
        q = p + sign
        while q % 12 not in scale:
            q += sign
        return q

    def leap(p, sign, lo, hi, t):
        cands = [p + sign * i for i in range(lo, hi + 1)]
        good = [q for q in cands if q % 12 in chord_at(t)] or [q for q in cands if q % 12 in scale]
        return good[0] if good else p + sign * lo

    def emit(p):
        nonlocal t, k
        d = durs[k % len(durs)]
        notes.append((p, t, d))
        t += d
        k += 1

    for ch in letters:
        if t >= total_beats:
            break
        if ch == "|":
            if notes:  # alonga a ultima nota e recomeca no proximo compasso
                pp, tt, dd = notes[-1]
                notes[-1] = (pp, tt, dd + 0.5)
                t = ((t + 0.5) // 4 + 1) * 4
            new, k = True, 0
            continue
        if new:
            p = nearest_chord_tone(p, t)
            emit(p)
            new = False
        sign = 1 if ch in "PAS" else -1 if ch in "pas" else 0
        if (sign > 0 and p > 79) or (sign < 0 and p < 62):
            sign = -sign
        if ch == "u":
            pass
        elif ch in "Pp":
            p = step(p, sign)
        elif ch in "Aa":
            p = leap(p, sign, 3, 5, t)
        else:
            p = leap(p, sign, 6, 9, t)
        emit(p)
    return notes

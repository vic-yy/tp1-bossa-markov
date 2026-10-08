"""Uso: python src/main.py  -> gera musicas em music/ e figura/estatisticas em results/."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from markov import MarkovChain, longest_copy
from mpb import load_harmony, load_contour, chord_tones, decode_melody, TONIC
from render import to_midi, to_wav

ROOT = os.path.join(os.path.dirname(__file__), "..")
MUSIC, RES = os.path.join(ROOT, "music"), os.path.join(ROOT, "results")
os.makedirs(MUSIC, exist_ok=True)
os.makedirs(RES, exist_ok=True)
BPM, BARS, COMPOSERS = 132, 32, ("JOBIM",)


def harmony_to_chords(states, mode):
    """states -> lista (inicio, dur em tempos, raiz_pc, intervalos) ate BARS compassos."""
    out, t = [], 0.0
    for rel, sym, dur in states:
        if t >= BARS * 4:
            break
        d = min(dur * 4, BARS * 4 - t)
        out.append((t, d, (rel + TONIC[mode]) % 12, chord_tones(sym)))
        t += d
    return out


def accompaniment(chords):
    ev = []
    clave = [[0, 1.5, 3], [1, 2.5]]  # clave de bossa 3-2 alternando compassos
    for t0, d, root, iv in chords:
        third, seventh = iv[1], (iv[3] if len(iv) > 3 else iv[2])
        top = iv[4] if len(iv) > 4 else iv[2]
        voicing = [55 + (root + x - 55) % 12 for x in (third, seventh, top)]
        for bar in range(int(t0 // 4), int((t0 + d - 1e-6) // 4) + 1):
            for b, (off, dur) in enumerate([(0, 1.5), (1.5, .5), (2, 1.5), (3.5, .5)]):
                s = bar * 4 + off
                if t0 <= s < t0 + d:
                    ev.append(("bass", 36 + (root + (7 if b % 2 else 0)) % 12, s, min(dur, t0 + d - s), 85))
            for off in clave[bar % 2]:
                s = bar * 4 + off
                if t0 <= s < t0 + d:
                    ev += [("comp", p, s, min(0.5, t0 + d - s), 60) for p in voicing]
    return ev


def make_piece(mode, h_order, m_order, seed, harm, cont):
    states = MarkovChain(h_order).fit(harm).generate(80, seed)
    chords = harmony_to_chords(states, mode)

    def chord_pcs(t):
        c = next(c for c in reversed(chords) if c[0] <= t)
        return {(c[2] + x) % 12 for x in c[3]}

    letters = MarkovChain(m_order).fit(cont).generate(400, seed)
    mel = decode_melody(letters, chord_pcs, mode, BARS * 4)
    ev = accompaniment(chords) + [("melody", p, s, d, 90) for p, s, d in mel if s < BARS * 4]
    return ev, states[:len(chords)]


if __name__ == "__main__":
    data = {m: load_harmony(COMPOSERS, m) for m in ("major", "minor")}
    cont = load_contour(COMPOSERS)
    print({m: (len(v), sum(map(len, v))) for m, v in data.items()}, "| contorno:", len(cont), "composicoes")

    # 1) musicas entregues: (modo, ordem harmonia, ordem contorno, semente)
    for mode, ho, mo, seed in [("major", 2, 3, 1), ("major", 2, 3, 2), ("major", 3, 4, 3),
                               ("minor", 2, 3, 4), ("minor", 3, 3, 5)]:
        ev, st = make_piece(mode, ho, mo, seed, data[mode], cont)
        name = f"jobim_{mode}_h{ho}_m{mo}_seed{seed}"
        to_midi(ev, os.path.join(MUSIC, name + ".mid"), BPM)
        to_wav(ev, os.path.join(MUSIC, name + ".wav"), BPM)
        print(name, "|", " ".join(f"{s}" for _, s, _ in st[:6]), "...")

    # 2) experimento: ordem x memorizacao (fracao da sequencia gerada copiada literalmente do corpus)
    orders, N = [1, 2, 3, 4, 5, 6], 15
    res = {"Harmonia (acordes)": [], "Melodia (contorno)": []}
    for o in orders:
        hs = [MarkovChain(o).fit(data["major"]).generate(24, s) for s in range(N)]
        ms = [MarkovChain(o).fit(cont).generate(64, s) for s in range(N)]
        res["Harmonia (acordes)"].append([longest_copy(s, data["major"]) / 24 for s in hs])
        res["Melodia (contorno)"].append([longest_copy(s, cont) / 64 for s in ms])
        print(f"ordem {o}: copia harmonia {np.mean(res['Harmonia (acordes)'][-1]):.2f}, "
              f"contorno {np.mean(res['Melodia (contorno)'][-1]):.2f}")
    fig, ax = plt.subplots(figsize=(3.2, 2.3))
    for lab, v in res.items():
        ax.errorbar(orders, np.mean(v, 1), yerr=np.std(v, 1), marker="o", capsize=2, label=lab)
    ax.set_xlabel("Ordem n")
    ax.set_ylabel("Fração copiada do corpus")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "order_vs_copy.pdf"))
    fig.savefig(os.path.join(RES, "order_vs_copy.png"), dpi=200)

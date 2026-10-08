"""Escreve o MIDI e faz uma síntese simples de WAV a partir dos eventos (trilha, pitch, início, duração, velocity); tempos em semínimas."""
import numpy as np
import pretty_midi
from scipy.io import wavfile

PROGRAMS = {"melody": 73, "comp": 24, "bass": 32}  # flauta, violão nylon, baixo acústico
# harmônicos e decaimento (1/s) de cada trilha
TIMBRE = {"melody": ([(1, 1), (2, .3), (3, .1)], 0.8), "comp": ([(1, 1), (2, .6), (3, .4), (4, .2)], 4.0),
          "bass": ([(1, 1), (2, .4)], 2.0)}


def to_midi(events, path, bpm):
    pm = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    insts = {k: pretty_midi.Instrument(program=v, name=k) for k, v in PROGRAMS.items()}
    spb = 60.0 / bpm
    for tr, p, s, d, v in events:
        insts[tr].notes.append(pretty_midi.Note(v, int(p), s * spb, (s + d * 0.97) * spb))
    pm.instruments.extend(insts.values())
    pm.write(path)


def to_wav(events, path, bpm, sr=22050):
    spb = 60.0 / bpm
    y = np.zeros(int((max(s + d for _, _, s, d, _ in events) * spb + 1.5) * sr))
    for tr, p, s, d, v in events:
        hs, decay = TIMBRE[tr]
        f, dur = 440.0 * 2 ** ((p - 69) / 12), d * spb
        t = np.arange(int((dur + 0.2) * sr)) / sr
        w = sum(a * np.sin(2 * np.pi * f * h * t) for h, a in hs)
        env = np.minimum(1, t / 0.01) * np.exp(-decay * t) * np.where(t > dur, np.exp(-(t - dur) * 30), 1)
        i = int(s * spb * sr)
        seg = (w * env * v / 100)[:len(y) - i]
        y[i:i + len(seg)] += seg
    y = y / np.max(np.abs(y)) * 0.8
    wavfile.write(path, sr, (y * 32767).astype(np.int16))

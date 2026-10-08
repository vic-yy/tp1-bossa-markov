"""Cadeia de Markov de ordem n generica (estados = objetos hashable), com backoff."""
import random
from collections import defaultdict, Counter


class MarkovChain:
    def __init__(self, order=3):
        self.order = order
        self.tables = {}  # k -> {contexto: Counter(proximo)}

    def fit(self, sequences):
        for k in range(1, self.order + 1):  # ordens 1..n para permitir backoff
            t = defaultdict(Counter)
            for s in sequences:
                for i in range(len(s) - k):
                    t[tuple(s[i:i + k])][s[i + k]] += 1
            self.tables[k] = t
        self.starts = [tuple(s[:self.order]) for s in sequences if len(s) > self.order]
        return self

    def generate(self, n, seed=None):
        rng = random.Random(seed)
        seq = list(rng.choice(self.starts))
        while len(seq) < n:
            nxt = None
            for k in range(min(self.order, len(seq)), 0, -1):  # backoff
                c = self.tables[k].get(tuple(seq[-k:]))
                if c:
                    items, w = zip(*c.items())
                    nxt = rng.choices(items, weights=w)[0]
                    break
            seq.append(nxt if nxt is not None else rng.choice(rng.choice(self.starts)))
        return seq[:n]


def longest_copy(seq, corpus):
    """Maior trecho contiguo de seq que aparece literalmente em alguma sequencia do corpus."""
    best = 0
    for m in corpus:
        for i in range(len(seq)):
            for j in range(len(m)):
                l = 0
                while i + l < len(seq) and j + l < len(m) and seq[i + l] == m[j + l]:
                    l += 1
                best = max(best, l)
    return best

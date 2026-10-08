# TP1 – Composição Musical Algorítmica (Cadeias de Markov): bossa nova no estilo de Tom Jobim

Duas cadeias de Markov de ordem *n*, aprendidas das 50 composições de **Tom Jobim** do
[MPB Corpus](https://github.com/ProjetoMPB/mpb-corpus) (CC BY 4.0):
1. **Harmonia**: estado = (raiz relativa à tônica, tipo de acorde, duração em compassos), de `harmony.csv`.
2. **Melodia**: letras de contorno (`c_word` de `contour_rhythm.csv`: repete, grau conjunto, arpejo, salto, acima/abaixo),
   decodificadas em notas sobre o acorde vigente. O corpus não tem alturas absolutas nem durações; o ritmo da melodia
   usa um ciclo sincopado fixo (decisão nossa).
3. **Acompanhamento** (regras): baixo (raiz/quinta) e violão com a clave de bossa 3-2.

## Instalação
```
pip install -r requirements.txt
git clone --depth 1 https://github.com/ProjetoMPB/mpb-corpus.git data/mpb_corpus   # se data/mpb_corpus não existir
```
## Reprodução
```
python src/main.py
```
Gera 5 peças de 32 compassos em `music/jobim_*.{mid,wav}` (modo, ordens e sementes diferentes) e
`results/order_vs_copy.{pdf,png}` (ordem × fração copiada literalmente do corpus). O WAV é síntese aditiva simples,
sem soundfont; o MIDI soa melhor num sintetizador/MuseScore.

## Estrutura
- `src/markov.py` cadeia genérica + métrica de cópia · `src/mpb.py` corpus, acordes e decodificação · `src/render.py` MIDI/WAV
- `paper/ismir.tex` resumo (usar template ISMIR)

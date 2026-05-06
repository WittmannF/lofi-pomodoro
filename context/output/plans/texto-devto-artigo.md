# Artigo — Dev.to / Medium

**Plataforma:** Dev.to (primário), Medium (republicar depois)  
**Tom:** pessoal, técnico, storytelling  
**Tags Dev.to:** `python`, `productivity`, `showdev`, `terminal`  
**Tempo de leitura estimado:** 6–8 minutos

---

## Título

> I built a terminal Pomodoro timer that plays lo-fi music — here's what I learned about the science behind it

---

## Cover image sugerida

Screenshot do terminal com a barra de progresso Rich + nome da música tocando. Fundo escuro, cores do Rich.

---

## Artigo completo

```markdown
# I built a terminal Pomodoro timer that plays lo-fi music — here's what I learned about the science behind it

I have a tab permanently open: "lofi hip hop radio — beats to relax/study to."

At some point I got annoyed at needing a browser tab just to play background music
while I work. So I built a Pomodoro timer that plays lo-fi music directly in the
terminal. Then I went down a rabbit hole researching whether lo-fi music actually
helps you focus — or if it's just placebo.

Here's what I found.

---

## The tool first

pip install pomodoro-lofi

Then just run `pomodoro`. You get a 25/5/15 Pomodoro timer with a Rich progress
bar and 250+ bundled lo-fi tracks playing automatically.

Keyboard controls during the session:
- `s` — skip track
- `p` — pause/unpause timer and music
- `i` — ignore this track forever (saved to `.ignored_songs`)

During breaks it plays ambient sounds (rain, fireplace, wind) instead of music.

You can also point it at your own folder:

    pomodoro --music-folder ~/my-music --volume 0.7

Or generate a custom playlist with ElevenLabs before your session:

    ELEVENLABS_API_KEY=... python scripts/generate_music.py --prompts my_prompts.yaml
    pomodoro --music-folder playlists/elevenlabs

GitHub: [link]

---

## Now, the science

I expected to find that lo-fi music is just a vibe — that the "focus benefits"
are entirely placebo. The reality is more interesting.

### 1. The Mozart Effect is mostly fake

You've probably heard that listening to classical music makes you smarter.
This comes from a 1993 paper by Rauscher, Shaw & Ky in *Nature* — 36 college
students showed a temporary improvement in spatial reasoning after listening to
Mozart K. 448.

The media distorted "temporary spatial reasoning boost in 36 adults" into
"Mozart makes babies smarter." Georgia's governor proposed distributing Mozart
CDs to newborns. Baby Einstein became a franchise.

The problem: the effect is entirely explained by arousal and mood. Thompson et al.
(2001) showed that when you statistically control for how much participants enjoyed
and were energized by the music, the Mozart Effect disappears. Any pleasant,
energizing stimulus — including a Stephen King passage — produces the same effect.

It's not Mozart. It's not classical music. It's mood and arousal.

### 2. Lyrics consistently hurt reading and writing tasks

This one is well-established and important.

When you read or write, your brain uses the phonological loop — the inner voice
that "speaks" words as you process them. Background speech and song lyrics compete
directly with this system, even when you're not consciously listening to them.

Salamé & Baddeley (1989) demonstrated this with serial recall tasks — 769 citations
later, the finding has been consistently replicated. A 2023 paper in *Journal of
Cognition* confirmed: "music with lyrics interferes with cognitive tasks."

The language of the lyrics matters too: if the lyrics are in the same language as
the text you're reading, interference is higher than if the song is in a foreign
language (Sun et al., 2024).

**Practical implication:** for reading, writing, coding with complex logic —
instrumental only. For mechanical or physical tasks, lyrics cause much less harm.

### 3. Lo-fi works because it's predictable

The key mechanism is cognitive load.

Your auditory cortex constantly predicts what comes next in music. When predictions
are confirmed, the brain stops allocating resources to musical analysis — the music
recedes into the background.

Lo-fi achieves this through:
- **Simple, repetitive harmony** — your brain builds the model fast
- **Consistent 70–90 BPM tempo** — no surprises
- **Imperfections (vinyl crackle, tape hiss)** — paradoxically signal that the
  music isn't competing for attention. It sounds "not produced to grab you."
- **No lyrics** — no phonological loop competition
- **Masking** — the consistent audio field masks sudden environmental sounds
  (notifications, conversations) that would otherwise trigger involuntary
  attentional orienting

Winston & Saywood (2019) studied lo-fi hip-hop specifically and found it effective
for "predictable, mechanical tasks" through "sonic self-insulation."

### 4. Volume matters more than you think

Mehta, Zhu & Cheema (2012) tested three noise levels — 50 dB, 70 dB, 85 dB —
and found 70 dB (roughly café volume) was the sweet spot for creative work.
Below that: mild under-arousal. Above 85 dB: performance degraded.

For deep analytical work (reading, writing, learning new material), 45–60 dB is
better — less stimulation, less interference with complex processing.

The Yerkes-Dodson curve applies: moderate arousal enhances performance; too much
or too little hurts. Music is an arousal lever.

### 5. White noise is genuinely useful for ADHD

This was the most surprising finding.

Séderlund et al. (2010) proposed the stochastic resonance model: ADHD brains have
lower baseline dopamine, which means lower internal neural "noise." Your brain
needs a certain noise floor to detect weak signals. When that floor is too low
(as in ADHD), weak signals don't get processed properly.

White noise adds external noise to bring subthreshold signals above the detection
threshold — improving working memory and focus for ADHD individuals.

This explains the paradox: white noise helps ADHD individuals but slightly impairs
neurotypical people. Neurotypical people already have adequate internal noise;
adding more pushes them past the optimal point.

Multiple studies since have confirmed this (Helps et al., 2014; Baijot et al., 2016).

---

## Implementation notes (for the devs)

The architecture is a single-file state machine (`pomodoro/__main__.py`, ~550 LOC).

Three threads:
- **Main thread** — drives the cycle loop, renders the Rich progress bar
- **Music player daemon** — shuffles and plays tracks with pygame.mixer
- **Key listener daemon** — non-blocking keyboard reads (select/termios on POSIX,
  msvcrt on Windows)

Two queues:
- `control_queue` — key listener → music player (skip/pause/ignore)
- `timer_queue` — key listener → main thread (pause/unpause countdown)

The key listener was the trickiest part — getting single-char reads without
blocking or requiring Enter. On POSIX, I save and restore the terminal attributes
with `tty.setraw()`, wrapped in a try/finally to ensure the terminal state is
always restored on exit.

---

## What's next

- ElevenLabs integration via YAML prompt file (generate a full custom playlist
  before your session)
- The full research document on music and cognition is in the repo at
  `docs/music-science-studying.md` if you want to go deeper

GitHub: [link]

Happy to answer questions about the implementation or the research.
```

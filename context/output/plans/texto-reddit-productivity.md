# Post — Reddit r/productivity e r/ADHD

**Subreddits:** r/productivity, r/ADHD, r/studytips  
**Tom:** acessível, baseado em ciência, sem jargão técnico  
**Ângulo:** a ferramenta como solução para um problema real, apoiada por pesquisa

---

## Versão r/productivity

### Título (opções)

**Opção A:**
> I researched the science behind study music and built a free tool around it

**Opção B:**
> The research on lo-fi music for focus is more interesting than I expected — and I built a Pomodoro timer around it

---

### Corpo

```
I went down a rabbit hole researching why lo-fi music seems to help people focus,
expecting to debunk it. The science is actually nuanced and interesting.

**Key findings:**

**1. The Mozart Effect is mostly myth** — the original 1993 Rauscher study showed
a temporary spatial reasoning boost that lasted 15 minutes. Meta-analyses since then
have shown the effect disappears when you control for mood and arousal. It's not
Mozart specifically — any pleasant, energizing stimulus does the same thing.

**2. Lyrics consistently hurt reading and writing** — this one is well-established.
Background speech (including song lyrics) competes with your phonological loop —
the "inner voice" you use when reading. Instrumental music avoids this.
(Salamé & Baddeley, 1989 — 769 citations.)

**3. Lo-fi works because it's predictable** — your auditory cortex quickly builds
a model of the music and stops allocating resources to it. The imperfections
(vinyl crackle, tape hiss) paradoxically signal that the music isn't trying to
grab your attention.

**4. ~70 BPM is the sweet spot for calm focus** — matches resting heart rate,
maintains mild arousal without pushing into anxiety.

**5. Volume matters** — 45–60 dB for deep reading/writing, ~70 dB for creative
work. Mehta et al. (2012) established 70 dB as optimal for creativity.

**6. White noise specifically helps ADHD** — through a dopamine-related mechanism
called stochastic resonance. External noise compensates for lower internal neural
noise baseline. (Séderlund et al., 2010.)

---

Based on this, I built a free CLI Pomodoro timer that plays lo-fi music during
work sessions and ambient sounds (rain, fireplace) during breaks. 250+ tracks
included, works offline.

`pip install pomodoro-lofi` then just run `pomodoro`

GitHub: [link] — the full research doc is also in the repo if you want to read it.
```

---

## Versão r/ADHD

### Título

> Lo-fi music and white noise for ADHD focus actually have scientific backing — here's what the research says (and a free tool)

---

### Corpo

```
I compiled research on music and concentration and the ADHD findings stood out.

**The stochastic resonance model (Séderlund et al., 2010 — 291 citations):**

ADHD brains have lower baseline dopamine, which means lower internal neural "noise."
Your brain needs a certain noise floor to detect and amplify weak signals. When
that floor is too low, weak signals don't get processed properly.

White noise adds exactly the external noise needed to bring those subthreshold
signals above the detection threshold — improving focus and working memory.

This is why white noise seems to help people with ADHD but slightly impairs
neurotypical people: neurotypical people already have adequate internal noise.

**Follow-up studies confirmed it:**
- Helps et al. (2014, PLOS ONE) — white noise enhanced working memory in children
  with ADHD symptoms
- Baijot et al. (2016) — white noise improved cognitive performance in ADHD children
- A 2007 study found white noise improved ADHD students while decreasing performance
  of non-ADHD students — the classic stochastic resonance signature

**For lo-fi specifically:**
- Instrumental (no lyrics competing with your inner voice)
- 70–90 BPM maintains calm arousal
- Predictable structure reduces cognitive overhead
- Vinyl crackle acts as a mild form of consistent background noise

---

I built a free Pomodoro timer that plays lo-fi music during work sessions.
250+ tracks included, works offline, no subscription.

`pip install pomodoro-lofi` → `pomodoro`

Skip tracks with `s`, pause with `p`, never hear a track again with `i`.

GitHub: [link]
```

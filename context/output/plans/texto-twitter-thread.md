# Thread — Twitter/X

**Tom:** informal, técnico mas acessível, GIF obrigatório no primeiro tweet  
**Tamanho:** 6–8 tweets  
**Objetivo:** retweets de devs, link para GitHub no final

---

## Thread A — ângulo técnico

**Tweet 1 (com GIF do terminal)**
```
I was tired of keeping a browser tab open just to play lo-fi music while I work.

So I built a terminal Pomodoro timer with a built-in lo-fi player.

pip install pomodoro-lofi → pomodoro

[GIF]
```

**Tweet 2**
```
250+ lo-fi tracks bundled. Completely offline.

Keyboard controls during the session:
• s → skip track
• p → pause timer + music
• i → ignore this song forever

No mouse. No window switching.
```

**Tweet 3**
```
Architecture nerd stuff:

3 threads: main (timer UI), music player daemon, key listener daemon
2 queues: control_queue (skip/pause/ignore) and timer_queue (pause countdown)

Key listener uses select/termios/tty on POSIX for non-blocking single-char reads.
No Enter required.
```

**Tweet 4**
```
During breaks it plays ambient sounds instead of music.

Rain, fireplace, wind, or "random" — each break picks a different vibe.

Works as a genuine context switch between work and rest.
```

**Tweet 5**
```
Optional: generate a custom lo-fi playlist with ElevenLabs before your session.

Write prompts in a YAML file → generate → play from local files.

No API calls during the actual timer.
```

**Tweet 6**
```
Stack:
• pygame — audio playback (cross-platform, no external binaries)
• rich — terminal progress bar
• Single file, ~550 LOC

GitHub: [link]

The full research doc on why lo-fi actually helps focus is also in the repo.
```

---

## Thread B — ângulo ciência/produtividade

**Tweet 1**
```
I researched the science behind lo-fi music for focus.

Expected to debunk it. The reality is more interesting.

Thread 🧵
```

**Tweet 2**
```
The Mozart Effect is basically fake.

The original 1993 study showed a 15-minute spatial reasoning boost.
Meta-analyses show it disappears when you control for mood and arousal.

It's not Mozart. It's not classical music.
It's just: pleasant + energizing = mild focus boost.
```

**Tweet 3**
```
Lyrics consistently hurt reading and writing.

They compete directly with your phonological loop —
the inner voice you use when reading.

Even when you're not consciously listening to them.

(Salamé & Baddeley, 1989 — 769 citations)

→ instrumental only for language tasks
```

**Tweet 4**
```
Lo-fi works because it's predictable.

Your auditory cortex builds a model of the music fast,
then stops allocating resources to it.

The music becomes background.
Vinyl crackle paradoxically signals "not trying to grab your attention."
```

**Tweet 5**
```
White noise specifically helps ADHD — through dopamine.

ADHD brains have lower neural noise baseline.
White noise adds exactly what's missing to detect weak signals
(stochastic resonance).

This is why white noise helps ADHD but slightly impairs neurotypical people.
```

**Tweet 6**
```
Based on all this: I built a Pomodoro timer that plays lo-fi in the terminal.

250+ bundled tracks, offline, keyboard controls.
Optional ElevenLabs integration for AI-generated playlists.

pip install pomodoro-lofi

Full research doc in the repo: [link]
GitHub: [link]
```

---

## Notas de publicação

- Postar a Thread B primeiro em dias de semana pela manhã (maior alcance)
- Responder os primeiros comentários para o algoritmo boostar o alcance
- Se algum tweet bombar solo, boostar ele com retweet + reply com link
- Usar a Thread A para r/programming e comunidades técnicas

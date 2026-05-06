# Launch — Product Hunt

**Formato:** produto completo com tagline, descrição, screenshots  
**Tom:** direto, focado no benefício, sem jargão técnico  
**Melhor dia para lançar:** terça ou quarta-feira, meia-noite PST (início do dia PH)

---

## Tagline (máx. 60 caracteres)

**Opção A:**
> Pomodoro timer with lo-fi music — no browser, no ads, just focus

**Opção B:**
> Terminal Pomodoro + 250 lo-fi tracks. Works offline. pip install.

**Opção C:**
> The Pomodoro timer for developers who live in the terminal

---

## Descrição curta (para o card)

```
A CLI Pomodoro timer that plays lo-fi music during work sessions and ambient
sounds during breaks — 250+ bundled tracks, completely offline. Keyboard controls
to skip, pause, or permanently ignore tracks. Optional AI music generation via
ElevenLabs.
```

---

## Descrição longa (corpo do lançamento)

```
**Why I built this**

I had a permanent browser tab open for lo-fi music. Every time I alt-tabbed, 
I lost focus. Every few months YouTube changes the stream URL. Ads interrupt 
at random. I wanted something that just worked — inside the terminal, where I 
already spend my day.

**What it does**

pomodoro is a Pomodoro timer that plays lo-fi music as a first-class feature, 
not an afterthought.

- 25/5/15 min cycles with a clean Rich progress bar
- 250+ lo-fi tracks bundled — works completely offline
- Break sounds (rain, fireplace, wind, soft-wind) during short breaks
- Keyboard controls: s=skip, p=pause, i=ignore permanently
- Custom music folder: `--music-folder /path`
- AI-generated playlists via ElevenLabs (YAML prompt file)

**The science**

I compiled 14 research topics on why background music affects focus — the Mozart 
Effect (mostly myth), why lyrics hurt reading tasks (phonological loop competition), 
why lo-fi specifically works (predictability reduces cognitive load), and why white 
noise helps ADHD (stochastic resonance / dopamine model). The full document is in 
the repo.

**Install**

pip install pomodoro-lofi
pomodoro

That's it.

**Open source — GitHub: [link]**
```

---

## Screenshots / assets necessários

1. **GIF principal** — terminal rodando com barra de progresso + música tocando
2. **Screenshot 1** — sessão de trabalho completa (ciclo + nome da música)
3. **Screenshot 2** — modo de pausa (timer parado, música pausada)
4. **Screenshot 3** — break com som de chuva tocando
5. **Opcional:** diagrama da arquitetura de threads

---

## First comment (postar logo após o launch)

```
Hey PH! Builder here.

A few things that didn't fit in the description:

**Why pygame over other audio libs?**
pygame.mixer is the only option I found that's truly cross-platform, has no 
external binary dependencies, and supports MP3 natively. Tried vlc (too heavy), 
playsound (unmaintained), simpleaudio (no MP3).

**The ignore feature**
Pressing `i` during a track adds it permanently to a `.ignored_songs` file. 
It never plays again — across sessions. Useful for tracks you've heard too many 
times or just don't fit your current mood.

**ElevenLabs integration**
Generate a YAML file with music prompts:
  - name: deep-focus
    prompt: "Calm lo-fi at 70 BPM, piano, no drums"

Run the generator script before your session. Tracks are cached — only regenerates 
if the prompt changes.

**Questions? Feedback?** Drop them here, happy to discuss.
```

---

## Comunidades para notificar no dia do launch

- r/Python — "Just launched on Product Hunt: [link]"
- r/productivity — mesmo post
- Twitter/X — tweet com link direto para a página PH
- Discord de Python / dev tools

# Post — Hacker News (Show HN)

**Seção:** Show HN  
**Tom:** minimalista, técnico, sem adjetivos inflados  
**Regra do HN:** o título deve descrever o projeto, não fazer marketing

---

## Título

> Show HN: A terminal Pomodoro timer with a built-in lo-fi music player (Python)

---

## Texto do post

*(HN permite texto curto opcional no post — ir direto ao ponto)*

```
A CLI Pomodoro timer that plays lo-fi music during work sessions and ambient
sounds (rain, fireplace) during breaks.

250+ bundled tracks, works offline. Keyboard controls: s=skip, p=pause, i=ignore.
Optional ElevenLabs integration to generate tracks from a YAML prompt file.

pip install pomodoro-lofi

Single-file implementation (~550 LOC): pygame for audio, Rich for the UI,
two daemon threads (music player + key listener) communicating via queues.

GitHub: [link]
```

---

## Possíveis perguntas do HN e respostas preparadas

**"Why not just use a browser tab with YouTube lofi?"**
> No ads, no network dependency, no browser overhead. Also integrates with the
> terminal workflow — you don't need to switch windows to skip a track.

**"How does the key listener work without pressing Enter?"**
> On POSIX: select/termios/tty for non-blocking single-char reads. On Windows:
> msvcrt.kbhit(). The key listener runs as a daemon thread writing to queues.

**"What's the license on the bundled music?"**
> All tracks are sourced from Free Music Archive and Chosic under CC licenses
> (CC0, CC BY, CC BY-SA). A scraper script is included if you want to add more.

**"ElevenLabs integration seems like an odd addition for a focus tool"**
> The idea is to generate a custom playlist before your session — prompt like
> "calm lo-fi at 70 BPM for deep work" — and play it locally from that point on.
> No API calls during the timer itself.

**"Why pygame?"**
> pygame.mixer is the simplest cross-platform audio playback option in Python
> with no external binary dependencies. Considered vlc (too heavy), playsound
> (unmaintained), simpleaudio (no MP3 support natively).

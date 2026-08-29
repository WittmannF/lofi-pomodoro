# Web UI on GitHub Pages — Implementation Plan

## Goal

Ship a static single-page app at `https://wittmannf.github.io/lofi-pomodoro/` that provides a Pomodoro timer with integrated Spotify playback — no backend, no server, purely client-side. The user logs into Spotify once (PKCE flow), and the page becomes a self-contained focus timer that plays music directly in the browser tab via the Web Playback SDK.

---

## Why This Works Without a Backend

Two Spotify technologies make this possible client-side only:

1. **PKCE Authorization Flow** — designed for apps that can't store secrets (SPAs, mobile). The browser generates a `code_verifier`, hashes it into a `code_challenge`, and exchanges the auth code for tokens directly with Spotify's token endpoint. No server involved.

2. **Web Playback SDK** — creates a virtual Spotify Connect device in the browser. Audio streams directly to the tab. No need for the Spotify desktop app to be open.

Both are free to use. Spotify Premium is required for playback.

---

## Architecture

```
docs/web/ (or a top-level /web folder)
├── index.html          ← single page: timer + player + login
├── style.css           ← minimal dark theme
├── app.js              ← timer logic, auth, SDK integration
└── callback.html       ← receives OAuth redirect, extracts code
```

GitHub Pages serves from the `docs/` folder (or a `gh-pages` branch). Zero build step — vanilla HTML/CSS/JS.

---

## Auth Flow (PKCE, Client-Side)

### Sequence

1. User clicks "Login with Spotify"
2. JS generates `code_verifier` (random 64 chars) → stores in `localStorage`
3. JS computes `code_challenge` = base64url(SHA256(code_verifier))
4. Redirect to:
   ```
   https://accounts.spotify.com/authorize?
     client_id=YOUR_CLIENT_ID&
     response_type=code&
     redirect_uri=https://wittmannf.github.io/lofi-pomodoro/callback.html&
     scope=streaming user-modify-playback-state user-read-playback-state user-read-currently-playing&
     code_challenge_method=S256&
     code_challenge=...
   ```
5. User grants permission → Spotify redirects to `callback.html?code=...`
6. `callback.html` extracts `code`, calls token endpoint:
   ```
   POST https://accounts.spotify.com/api/token
   Body: grant_type=authorization_code&code=...&redirect_uri=...&client_id=...&code_verifier=...
   ```
7. Receives `access_token` + `refresh_token` → stores in `localStorage`
8. Redirects back to `index.html`

### Token Refresh

Access tokens expire in 1 hour. Before each API call (or on 401), refresh:
```
POST https://accounts.spotify.com/api/token
Body: grant_type=refresh_token&refresh_token=...&client_id=...
```

No client secret needed with PKCE.

### Required OAuth Scopes

| Scope | Purpose |
|-------|---------|
| `streaming` | Required by Web Playback SDK |
| `user-modify-playback-state` | Play, pause, skip, shuffle |
| `user-read-playback-state` | Get current track info |
| `user-read-currently-playing` | Display now-playing |

---

## Spotify Developer Dashboard Changes

The existing "Lofi Pomodoro" app needs one update:

**Add a Redirect URI:**
```
https://wittmannf.github.io/lofi-pomodoro/callback.html
```

(Keep the existing `http://127.0.0.1:8888/callback` for the CLI — multiple redirect URIs are supported.)

Also check **"Web Playback SDK"** in the APIs section (in addition to "Web API" which is already checked).

---

## Web Playback SDK Integration

### Loading

```html
<script src="https://sdk.scdn.co/spotify-player.js"></script>
```

### Initialization

```javascript
window.onSpotifyWebPlaybackSDKReady = () => {
  const player = new Spotify.Player({
    name: 'Lofi Pomodoro',
    getOAuthToken: cb => {
      // Return fresh token (refresh if expired)
      const token = getValidToken();
      cb(token);
    },
    volume: 0.5
  });

  player.addListener('ready', ({ device_id }) => {
    console.log('Web player ready, device ID:', device_id);
    // Store device_id for API calls
  });

  player.addListener('player_state_changed', state => {
    // Update now-playing display
  });

  player.connect();
};
```

### Playing a Playlist

Once connected, use the Web API (not the SDK) to start playback on the web player device:

```javascript
fetch(`https://api.spotify.com/v1/me/player/play?device_id=${deviceId}`, {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    context_uri: 'spotify:playlist:37i9dQZF1DX0SM0LYsmbMT',
    offset: { position: Math.floor(Math.random() * 50) }  // random start
  })
});
```

---

## Timer Logic

Same Pomodoro state machine as the CLI:

```
[Work 25min] → beep → [Short Break 5min] → beep → [Work] → ... → [Long Break 15min]
```

### Behavior Per Phase

| Phase | Spotify | UI |
|-------|---------|-----|
| Work | Play playlist (shuffle on) | Progress bar + track info |
| Short Break | Pause Spotify | Progress bar + "Take a break" |
| Long Break | Pause Spotify | Progress bar + "Long break!" |

### Controls

- **Space** — pause/unpause timer + music
- **S** — skip track
- **N** — skip to next phase

---

## UI Design (Minimal)

Dark theme, centered layout:

```
┌─────────────────────────────────────┐
│         🍅 Lofi Pomodoro            │
│                                     │
│     ████████████░░░░░  18:32        │
│          Work (Cycle 2/4)           │
│                                     │
│  🎵 Lotus Beats – Youth            │
│                                     │
│   [⏸ Pause]  [⏭ Skip]  [⏩ Next]  │
│                                     │
│  Playlist: Lo-fi Beats ▾           │
└─────────────────────────────────────┘
```

Responsive — works on mobile too (useful for controlling from phone).

---

## Implementation Steps

1. **Update Spotify Dashboard** — add redirect URI + check Web Playback SDK
2. **Create `docs/web/callback.html`** — extracts code, exchanges for token, redirects to index
3. **Create `docs/web/app.js`** — auth module (PKCE + token refresh), timer module, player module
4. **Create `docs/web/index.html`** — layout with progress bar, controls, login button
5. **Create `docs/web/style.css`** — dark theme, responsive
6. **Configure GitHub Pages** — serve from `docs/web/` or set up a subtree
7. **Test** — login flow, playback, timer transitions, token refresh, mobile

---

## What the CLI App Shares

The same `SPOTIPY_CLIENT_ID` (Spotify app) works for both CLI and web — they just use different redirect URIs. No conflicts.

| | CLI | Web |
|---|---|---|
| Auth flow | PKCE (Spotipy) | PKCE (vanilla JS) |
| Redirect URI | `http://127.0.0.1:8888/callback` | `https://wittmannf.github.io/lofi-pomodoro/callback.html` |
| Playback | Controls Spotify app (Connect API) | Plays in browser tab (Web Playback SDK) |
| Break sounds | Local pygame | Web Audio API or `<audio>` element |
| Config storage | `~/.config/pomodoro/` | `localStorage` |

---

## Limitations & Trade-offs

- **Spotify Premium required** — same as CLI mode
- **Token in localStorage** — acceptable for a personal tool; not ideal for a multi-user production app
- **No offline/fallback** — if not logged in, the page is just a timer without music (still useful)
- **iOS autoplay restriction** — first play requires user tap (browser policy), subsequent plays are fine
- **Client ID visible in source** — this is fine for public PKCE apps (Spotify's own examples do this)

---

## Future Enhancements (Not in V1)

- Preset playlist selector dropdown (same presets as CLI: lofi, deep-focus, chill)
- Break sounds via bundled ambient MP3s (rain, fireplace) played through `<audio>`
- PWA manifest for "Add to Home Screen" on mobile
- Session stats (cycles completed, total focus time)
- Dark/light theme toggle

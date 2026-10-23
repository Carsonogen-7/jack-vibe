# Jack's Palate Quiz

A five-minute quiz that captures how Jack judges food, as a static web app that works well on iPhone and can be added to the home screen. Jack takes the quiz, gets a results code, and sends it back. `tools/decode.py` turns that code into readable data for building the Jack Vibe Score formula.

## Files

| File | What it is |
|---|---|
| `index.html` | The whole quiz: markup, styles and script in one file |
| `log.html` | Vibe Log: Jack logs real meals and sends them in batches |
| `log.webmanifest` | Home-screen settings for the Vibe Log |
| `manifest.webmanifest` | Home-screen name, icon and colors |
| `sw.js` | Service worker for offline use (only runs over HTTPS) |
| `icons/` | Home-screen and favicon icons |
| `tools/decode.py` | Decodes a `JACKVIBE3.` results code |
| `tools/decode_log.py` | Decodes a `JACKLOG1.` review batch, optionally merging into a CSV |

## Run it locally

```bash
python3 -m http.server 8000
```

Open http://localhost:8000. To try it on your phone over Wi-Fi, open `http://<your-computer's-LAN-IP>:8000`. The service worker and the iOS share sheet need HTTPS, so test those on the hosted version.

## Host it (free, HTTPS)

Any static host works. Two easy options:

- **GitHub Pages:** push this folder to a repo, then Settings → Pages → deploy from the `main` branch root. The URL will be `https://<user>.github.io/<repo>/`.
- **Netlify Drop:** drag the folder onto https://app.netlify.com/drop.

## Add to iPhone home screen

Open the hosted URL in Safari → Share → Add to Home Screen. It launches full-screen like an app.

## Getting results back

At the end of the quiz Jack taps **Send to Carson**, which opens the iOS share sheet with his code (or **Copy code** where sharing isn't available). Decode it with:

```bash
python3 tools/decode.py "JACKVIBE3.eyJ2Ijoy..."
python3 tools/decode.py --json "JACKVIBE3...."
```

## Code format

`JACKVIBE3.` + base64(UTF-8 JSON):

```json
{
  "v": 3,
  "w": { "flavor": 0-10, "seasoning": 0-10, "texture": 0-10, "execution": 0-10, "ingredients": 0-10,
         "portion": 0-10, "presentation": 0-10, "crave": 0-10,
         "service": 0-10, "ambiance": 0-10, "speed": 0-10, "value": 0-10 },  // 0.0-10.0, one decimal
  "share": 0-40,                         // % of the final score given to the restaurant
  "p": { "q1": "a"|"b", ... "q6": ... }, // tradeoff picks
  "m": { "d1": 0.0-10.0, ... "d7": ... }, // overall ratings of the 7 sample dishes; missing = unrated
  "deal": ["cold", "seasoning", ...],    // dealbreakers
  "price": "relative"|"absolute"|"some",
  "sig": "signature category text",
  "best": "...", "worst": "..."
}
```

The dish profiles behind `d1`–`d7` (1–5 per food category plus one restaurant score) are the `MEALS` array in `index.html`. Those plus Jack's ratings are the data for fitting revealed weights.

## Review log

`log.html` is for ongoing data. For each real meal Jack scores the 8 food categories and 4 restaurant factors (0.0–10.0, any can be skipped), ticks any dealbreakers that happened, and gives his own overall score. Reviews stay on his phone until he taps **Send**, which shares one code with every unsent review.

```bash
python3 tools/decode_log.py "JACKLOG1...."
python3 tools/decode_log.py --csv reviews.csv "JACKLOG1...."   # keeps a running dataset
```

Code format: `JACKLOG1.` + base64(UTF-8 JSON) of `{"v":1,"r":[review,...]}`, where each review is
`{"id","date","rest","dish","price"?,"f":{food key: 0-10},"r":{restaurant key: 0-10},"deal":[...],"o":0-10,"note"}`. Skipped categories are left out.

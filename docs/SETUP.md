# Setup, step by step (from zero)

You need four free accounts and two tools. Nothing here needs a payment card. Total time ≈ 30–45 minutes.
Every key goes in one file, `.env`, in the repo root. `.env` is listed in `.gitignore`, so it is never committed.

```
copy .env.example .env        (Windows)      cp .env.example .env     (macOS/Linux)
```
Open `.env` in VS Code and fill the values in as you go.

> **What is an API key?** A long secret string that identifies you to a service, like a password for programs.
> Anyone who has it can spend your free quota, so never paste it in chat, screenshots, commits or Slack.
> If one leaks, delete it on the provider's site and create a new one.

---

## 1. Gemini API key (writes the storyboard draft and speaks the narration)

1. Open **https://aistudio.google.com** and sign in with a Google account.
2. Accept the terms if asked.
3. In the left menu click **Get API key** (or the key icon).
4. Click **Create API key**. If it asks for a project, choose **Create API key in new project**.
5. Copy the key (it starts with `AIza…`).
6. In `.env`: `GEMINI_API_KEY=AIza...your key...`
7. Check the free limits: in AI Studio open **Usage / Rate limits** and note the requests-per-minute and per-day
   for the Flash and the TTS models. Write them in `COSTS.md`.

**Test:** `uv run python -m pipeline smoke` → step [1/4] lists the models your key sees, [2/4] prints `'ready'`,
[3/4] writes an Arabic test WAV. If the TTS model name differs from the default, copy the one it lists into
`GEMINI_TTS_MODEL=` in `.env`.

## 2. Cloudflare Workers AI (draws the keyframe images)

1. Open **https://dash.cloudflare.com/sign-up**, sign up with email + password, and verify your email.
2. **Account ID:** after logging in, go to **Workers & Pages** (or **Compute (Workers)**) in the left menu.
   The **Account ID** is on the right side of the overview page. Click to copy it.
   (Also visible in the browser address bar: `dash.cloudflare.com/<ACCOUNT_ID>/...`)
3. **API token:** click the profile icon (top right) → **My Profile** → **API Tokens** → **Create Token**.
4. Find the template **"Workers AI"** → **Use template** → leave the defaults → **Continue to summary** → **Create Token**.
   (No template? Choose **Create Custom Token**, add permission **Account → Workers AI → Edit**, include your account.)
5. Copy the token now. Cloudflare shows it only once.
6. In `.env`:
   ```
   CLOUDFLARE_ACCOUNT_ID=your account id
   CLOUDFLARE_API_TOKEN=your token
   ```
7. Free allowance: about 10,000 "neurons" a day, roughly 50–170 images depending on the model. Check it under
   **AI → Workers AI → Usage**, and write what you find in `COSTS.md`.

**Test:** the smoke test step [4/4] writes `outputs/smoke/flux-check.jpg`.

## 3. Kaggle (free GPU for the video clips and the music)

1. Open **https://www.kaggle.com** → **Register** (Google sign-in is fine).
2. **Phone verification (required for GPUs):** profile picture → **Settings** → **Phone verification** → enter your phone
   number and the SMS code. Without this, the GPU and Internet switches stay greyed out.
3. (Optional, for the command line) **Settings → API → Create New Token** downloads `kaggle.json` with your username and key.
   Put them in `.env` as `KAGGLE_USERNAME` and `KAGGLE_KEY`. **Never commit `kaggle.json`.**
4. To run our notebooks: **Create → New Notebook → File → Import Notebook** → upload `kaggle/acestep_score.ipynb`
   (or `kaggle/wan_i2v.ipynb`).
5. In the notebook's right panel → **Session options**: **Accelerator = GPU T4 x2**, **Internet = On**.
6. Quota: about 30 GPU hours a week. The meter is at the top of the notebook page. Note it in `COSTS.md`.

## 4. GitHub (public repository)

1. In a terminal: `gh auth status`. If not logged in: `gh auth login` → GitHub.com → HTTPS → login with browser.
2. We create the public repo later with `gh repo create heritage-short --public --source . --push`.

## 5. Tools on your machine

| Tool | Why | Install |
|---|---|---|
| **uv** | runs Python 3.12 with exactly the right packages | https://docs.astral.sh/uv/ (Windows: `winget install astral-sh.uv`) |
| **FFmpeg** | assembles the film (cuts, subtitles, ducking, loudness) | Windows: `winget install Gyan.FFmpeg` · macOS: `brew install ffmpeg` · Linux: `apt install ffmpeg` |

Then, in the repo:
```
uv sync                                  # install the Python packages into .venv
uv run python -m pipeline smoke          # one call per provider, logged to runs.jsonl
```

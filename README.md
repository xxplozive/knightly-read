# Knightly Read

A news aggregator website with a weekly current events quiz.

## Features

- Aggregates headlines from 20+ RSS feeds across multiple regions (US, Global, Tri-State, Sports, Odd News)
- Local news based on user geolocation (via Cloudflare Worker proxy)
- Weekly quiz generated from headlines using AI
- Leaderboard for quiz scores
- Dark mode support
- Mobile-friendly with swipe navigation
- Automatic hourly updates via GitHub Actions

## External Services

| Service | Purpose | Required | Cost |
|---------|---------|----------|------|
| **GitHub Pages** | Static site hosting | Yes | Free |
| **Anthropic API** | Quiz question generation (Claude) | For quiz | ~$0.02/week |
| **Firebase** | Leaderboard score storage | For leaderboard | Free tier |
| **Cloudflare Workers** | Local news RSS proxy (avoids CORS) | For local news | Free tier (100k req/day) |
| **Cloudflare** | Domain & DNS (knightlyread.com) | Optional | ~$10/year for domain |
| **GoatCounter** | Privacy-friendly analytics | Optional | Free |
| **Formspree** | Feedback form submission | Optional | Free tier |

## Setup

### 1. Clone and Install

```bash
git clone https://github.com/xxplozive/knightly-read.git
cd knightly-read
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Locally

```bash
python run.py
# Open output/index.html in browser
# For quiz.json to load, use a local server:
cd output && python -m http.server 8000
```

### 3. Configure GitHub Secrets

Go to repo Settings → Secrets → Actions and add:

| Secret | Value |
|--------|-------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key from console.anthropic.com |

### 4. Set Up Firebase (for leaderboard)

1. Create project at [console.firebase.google.com](https://console.firebase.google.com)
2. Enable Realtime Database (start in test mode)
3. Get your config from Project Settings → Your apps → Web
4. Update `firebaseConfig` in `templates/index.html`

### 5. Set Up Cloudflare Worker (for local news)

1. Create a free account at [dash.cloudflare.com](https://dash.cloudflare.com)
2. Go to **Workers & Pages** → **Create** → **Create Worker**
3. Name it `local-news-proxy` and click **Deploy**
4. Click **Edit Code**, paste the contents of `cloudflare-worker/worker.js`, and **Deploy**
5. Update the worker URL in `templates/index.html` (search for `workers.dev`)

### 6. Custom Domain (optional)

1. Register domain (e.g., Cloudflare)
2. Add DNS records pointing to GitHub Pages:
   - `CNAME @ → xxplozive.github.io`
   - `CNAME www → xxplozive.github.io`
3. In repo Settings → Pages → Custom domain, enter your domain

## Python Dependencies

```
feedparser      # RSS feed parsing
requests        # HTTP requests for fetching feeds
pyyaml          # Configuration file parsing
jinja2          # HTML template rendering
python-dateutil # Date parsing from feeds
rapidfuzz       # Fuzzy matching for article deduplication
anthropic       # Claude API for quiz generation
```

## Project Structure

```
├── config/
│   └── feeds.yaml        # RSS feeds and settings
├── src/
│   ├── aggregator.py     # Main orchestrator
│   ├── fetcher.py        # RSS feed fetching with retries
│   ├── parser.py         # Feed parsing and normalization
│   ├── deduplicator.py   # Fuzzy title matching
│   ├── generator.py      # HTML/JSON output
│   ├── quiz_generator.py # AI quiz question generation
│   ├── paywall.py        # Paywall detection
│   └── country_detector.py # Country flag emojis
├── templates/
│   └── index.html        # Jinja2 template with CSS/JS
├── cloudflare-worker/
│   └── worker.js         # Cloudflare Worker for local news RSS proxy
├── output/               # Generated site (deployed to GitHub Pages)
├── run.py                # Entry point
└── .github/workflows/
    └── deploy.yml        # Hourly builds + deployment
```

## GitHub Actions

The site rebuilds automatically:
- **Every hour** - Refreshes news headlines
- **On push to main** - Deploys code changes
- **Manual trigger** - Via Actions tab

Quiz regenerates when `ANTHROPIC_API_KEY` is set.

## License

MIT

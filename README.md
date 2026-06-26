# yvision-parser

Export a [yvision.kz](https://yvision.kz) blog account's posts to Markdown files —
with images downloaded locally and YAML frontmatter, organized by year.

## Features

- Export by **username**, **profile URL**, or **numeric user id**
- Converts post HTML to clean Markdown (`markdownify` + `BeautifulSoup`)
- Downloads inline images and rewrites links to local copies
- YAML frontmatter (title, date, original URL, tags, view/comment/like counts)
- Output organized as `posts/<username>/<year>/<date>-<slug>.md`

## Install

Requires **Python 3.12+**.

```bash
git clone https://github.com/<you>/yvision-parser.git
cd yvision-parser
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# by username
python main.py drugoi

# by profile URL
python main.py https://drugoi.yvision.kz

# by numeric user id
python main.py 8249

# custom output directory
python main.py drugoi --output ./export
```

Posts are written to `posts/<username>/`. Re-running skips images that are already
downloaded.

## Output example

```
posts/drugoi/
  2013/
    2013-01-01-pochemu-kazahstan.md
  images/
    2013/
      tumblr_xxxx.jpg
```

```markdown
---
title: "Post title"
date: 2013-01-01
original_url: https://yvision.kz/p/311830
tags: ["tag1", "tag2"]
views: 1328
comments: 0
likes: 5
---

Post body in Markdown…
```

## Web app

A simple Russian web UI to export a yvision blog to a downloadable zip, designed
to run at [myvision.drugoi.xyz](https://myvision.drugoi.xyz). It shares the same
export engine as the CLI and runs exports as background jobs.

```bash
# run locally
EXPORT_DIR=/tmp/yv-exports uvicorn webapp.app:app --reload
# then open http://127.0.0.1:8000

# run with Docker (listens on 127.0.0.1:8771)
docker compose up -d --build
```

To deploy to a server behind nginx, see [`deploy/README.md`](deploy/README.md).

Like the CLI, the web app exports **public** posts only and respects yvision.kz's
Terms of Service.

## Development

```bash
pip install pytest
pytest
```

Tests are fully mocked and never hit the network.

## Notes

- Exports **public** posts only, via yvision's public API. No login required.
- Please use this to back up **your own** content and respect yvision.kz's Terms of
  Service. This project is not affiliated with yvision.kz.

## License

[MIT](LICENSE) © 2026 Nikita Bayev

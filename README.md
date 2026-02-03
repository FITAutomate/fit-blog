# 🤖 FIT Blog — Automation + AI Playbooks for SMBs
Secure, practical automation insights for small businesses, published as a MkDocs Material blog.

## Why FIT?
We believe automation should **augment human judgment**, not replace it. Every workflow should include checkpoints, approvals, and visibility — so you get the upside without the risk.

## 🌐 Live Site
Production: https://johnbewley.github.io/fit-automate-blog/

## 🚀 Quick Start
### Prerequisites
- Python 3.10+
- PowerShell (Windows) or a POSIX shell (macOS/Linux)

### Local Development
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
mkdocs serve
```
Then visit: http://localhost:8000

### Build
```powershell
mkdocs build
```
The output is generated in `site/` and should **not** be committed.

## 📁 Project Structure
```
mkdocs.yml               # MkDocs configuration
requirements.txt         # Python dependencies
docs/
  index.md               # Home page
  blog/
    index.md             # Blog index
    posts/               # Blog posts (Markdown)
  assets/                # Images
  stylesheets/           # Custom CSS
```

## 🧭 Content Workflow
- New posts go in `docs/blog/posts/`
- Images go in `docs/assets/`
- Update theme/custom CSS in `docs/stylesheets/extra.css`

## 🔒 Repo Hygiene
- `site/` is build output (generated on each build)
- `venv/` is local-only (do not commit)

## 🤝 Contributing
- Keep changes small and focused
- Validate locally with `mkdocs build`
- Prefer Markdown lint/consistency (headings, links, image paths)

## 🧾 License
MIT (or update this section if different)

---
Built by Forward IT Thinking — secure, practical automation for SMBs.

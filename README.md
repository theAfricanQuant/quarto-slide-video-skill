# Quarto Slide Video Skill

Convert Quarto presentations with speaker notes into AI-narrated MP4 videos with professional enhancements.

## What It Does

This skill automates the full pipeline from a Quarto `.qmd` presentation to a polished video:

1. **Extract speaker notes** from Quarto source
2. **Generate AI narration** using Kokoro TTS (multiple voices available)
3. **Capture slide screenshots** via Chrome headless
4. **Build synchronized video** with:
   - Slide images synced to narration timing
   - Fade transitions between slides
   - Background music (ambient, low-volume)
   - Burned-in captions (ASS format with bottom positioning)

## Output

- **1920×1080 MP4** (H.264 + AAC)
- **Duration**: Matches total narration time (~4-5 min for 14 slides)
- **File size**: ~7 MB for a 4-minute presentation

## Prerequisites

### 1. HyperFrames (Optional but Recommended)

This skill was developed as part of the [HyperFrames](https://github.com/heygen-com/hyperframes) ecosystem — a framework for creating HTML-based video compositions. While this skill uses a standalone ffmpeg pipeline, HyperFrames provides additional tools for advanced video production.

```bash
# Install HyperFrames CLI
npx hyperframes@latest init my-project
```

### 2. ffmpeg

**Windows (winget):**
```powershell
winget install Gyan.FFmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS (Homebrew):**
```bash
brew install ffmpeg
```

**Verify installation:**
```bash
ffmpeg -version | head -1
```

### 3. Quarto CLI

**Windows (winget):**
```powershell
winget install Posit.Quarto
```

**Ubuntu/Debian:**
```bash
sudo apt install quarto
```

**macOS (Homebrew):**
```bash
brew install quarto
```

**Or download directly:** https://quarto.org/docs/get-started/

### 4. Chrome/Chromium

Required for headless slide screenshots.

**Windows:** Download from https://www.google.com/chrome/

**Ubuntu/Debian:**
```bash
sudo apt install chromium-browser
```

**macOS:**
```bash
brew install --cask google-chrome
```

### 5. Python Dependencies (via uv)

This project uses [uv](https://github.com/astral-sh/uv) — an extremely fast Python package manager and resolver written in Rust.

**Install uv:**

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Linux/macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Or with Homebrew:**
```bash
brew install uv
```

**Install Python dependencies:**
```bash
uv pip install kokoro-onnx soundfile
```

The Kokoro TTS model will auto-download on first run (~300 MB).

**Run scripts with uv:**
```bash
uv run scripts/build_working.py
```

## Quick Start

```bash
# 1. Clone this skill
git clone https://github.com/theAfricanQuant/quarto-slide-video-skill.git
cd quarto-slide-video-skill

# 2. Render your Quarto presentation
quarto render slides.qmd --to revealjs

# 3. Extract notes & generate TTS
uv run scripts/extract_notes.py

# 4. Capture screenshots
uv run scripts/screenshot_slides.py

# 5. Build final video
uv run scripts/build_working.py
```

## Repository Structure

```
quarto-slide-video/
├── SKILL.md                          # Full skill documentation
├── README.md                         # This file
├── scripts/
│   ├── build_working.py              # Main production build script (WORKING)
│   ├── generate_sentence_captions.py # ASS caption generator (sentence-level)
│   └── generate_ass_captions.py      # ASS caption generator (phrase-level)
└── examples/
    ├── timeline_v2.json              # Sample timing data
    ├── captions.ass                  # Sample ASS subtitles
    └── notes.json                    # Sample extracted notes
```

## Critical Bug Warning

**Do NOT use `-movflags +faststart`** with ffmpeg 6.x on videos longer than ~60 seconds. It corrupts the H.264 NAL stream ("Invalid NAL unit size" errors). The working build script uses a clean two-pass approach without this flag.

## Requirements Summary

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.10+ | Script runtime |
| ffmpeg | 6.x | Video encoding (libx264, libass) |
| Chrome/Chromium | Latest | Headless screenshots |
| Quarto | 1.4+ | Presentation rendering |
| Kokoro TTS | Latest | AI narration |

## License

MIT

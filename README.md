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

## Quick Start

```bash
# 1. Install dependencies
pip install kokoro-onnx soundfile

# 2. Render your Quarto presentation
quarto render slides.qmd --to revealjs

# 3. Extract notes & generate TTS
python3 scripts/extract_notes.py

# 4. Capture screenshots
python3 scripts/screenshot_slides.py

# 5. Build final video
python3 scripts/build_working.py
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

## Requirements

- Python 3.10+
- ffmpeg 6.x (with libx264, libass)
- Chrome/Chromium (for screenshots)
- Quarto CLI
- Kokoro TTS model (auto-downloaded on first run)

## License

MIT

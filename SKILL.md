# Quarto Slide Video Skill

## Overview

This OpenCode skill converts Quarto presentations with speaker notes into polished, AI-narrated MP4 videos. It extracts speaker notes, generates AI voice narration, captures slide screenshots, composes a synchronized video with smooth transitions, background music, and optional burned-in captions.

---

## Features

- **AI Voice Narration** — Uses Kokoro TTS (e.g., `af_heart`, `af_bella`) via `npx hyperframes tts`
- **Slide Synchronization** — Each slide displayed for exactly the duration of its narration + 1 second buffer
- **Smooth Transitions** — 0.5s fade in/out per slide using ffmpeg `fade` filter
- **Background Music** — Subtle ambient track mixed at ~10% volume with fade in/out
- **Burned Captions** — Complete sentence subtitles with bottom positioning, proportional timing, and smooth transitions
- **Production Ready** — Two-pass encoding with concat demuxer (reliable) + muxed mixed audio

---

## Workflow

```
Quarto .qmd ──┬──► Render ──► HTML ──► Screenshot ──► slides/*.png
              │                              │
              └──► Speaker Notes ──► TTS ────┼─► assets/slide_*.wav
                                             │
                                             ▼
                                       + Background Music
                                       + Captions
                                       ▼
                                  FFmpeg concat demuxer
                                       ▼
                                   Final MP4
```

---

## Required Files

1. **Quarto presentation** (`.qmd`) with speaker notes in reveal.js format
2. **Speaker notes** embedded in `.qmd` files: `::: notes\nYour note text here.\n:::`
3. **Dependencies**: ffmpeg, google-chrome (headless), npx hyperframes (with TTS support)

---

## Scripts

### Script 1: extract_notes.py

Extract speaker notes and generate TTS audio.

```python
#!/usr/bin/env python3
"""Extract notes and generate TTS narration per slide."""
import json, subprocess, time
from pathlib import Path
from bs4 import BeautifulSoup

def main(voice='af_bella'):
    html_file = 'presentation.html'
    Path('assets').mkdir(exist_ok=True)
    
    with open(html_file, 'r') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    slides = []
    for idx, section in enumerate(soup.find_all('section')):
        section_copy = BeautifulSoup(str(section), 'html.parser').find('section')
        notes_elem = section_copy.find('aside', class_='notes')
        
        if notes_elem:
            notes = notes_elem.get_text(strip=True)
            output = f'assets/slide_{idx:03d}.wav'
            
            subprocess.run([
                'npx', 'hyperframes', 'tts', notes,
                '--voice', voice, '--output', output
            ], check=True, timeout=120)
            
            slides.append({'index': idx, 'notes': notes})
            print(f"✅ Slide {idx}: {output}")
            time.sleep(2)  # Rate limit protection
    
    with open('timeline.json', 'w') as f:
        json.dump({'slides': slides}, f, indent=2)

if __name__ == '__main__':
    main()
```

**Key points:**
- Use `af_heart` for warm American female voice
- Use `af_bella` for slightly different female voice
- Add `time.sleep(2)` between API calls to avoid rate limits
- File naming: `slide_001.wav`, `slide_002.wav`, etc. (3-digit zero-padded)

---

### Script 2: screenshot_slides.py

Capture slide images.

```python
#!/usr/bin/env python3
import json, subprocess
from pathlib import Path

def main():
    with open('timeline.json') as f:
        timeline = json.load(f)
    Path('slides').mkdir(exist_ok=True)
    
    for slide in timeline['slides']:
        idx = slide['index']
        url = f'file://{Path.cwd()}/presentation.html'
        output = f'slides/slide_{idx:03d}.png'
        
        subprocess.run([
            'google-chrome', '--headless', '--disable-gpu',
            '--no-sandbox', f'--screenshot={output}',
            '--window-size=1920,1080', '--hide-scrollbars',
            url
        ], capture_output=True, timeout=30)
        
        if Path(output).exists():
            print(f"✅ Screenshot {idx}")

if __name__ == '__main__':
    main()
```

---

### Script 3: build_enhanced.py (PRODUCTION BUILD)

Full-featured production video builder with all enhancements.

```python
#!/usr/bin/env python3
"""
Production video builder with:
- af_bella voice narration
- 0.5s fade in/out transitions per slide
- Background music mixed at 10% volume with fade in/out
- Burned-in captions from SRT file
- Reliable concat demuxer workflow
"""
import json, subprocess, sys
from pathlib import Path

WORKDIR = Path(".")
ASSETS = WORKDIR / "assets"
CLIPS = WORKDIR / "clips_enhanced"
FADE_DURATION = 0.5

def run(cmd, **kwargs):
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)

def get_duration(path):
    r = run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'json', str(path)])
    return float(json.loads(r.stdout)['format']['duration'])

def build():
    CLIPS.mkdir(exist_ok=True)
    
    # 1. Read and recalibrate timeline with actual audio durations
    with open(WORKDIR / 'timeline.json') as f:
        timeline = json.load(f)
    
    new_timeline = {'slides': []}
    cumulative = 0
    for slide in timeline['slides']:
        idx = slide['index']
        wav = ASSETS / f"slide_{idx:03d}.wav"
        dur = get_duration(wav)
        slide_duration = dur + 1  # +1s display buffer
        new_timeline['slides'].append({
            'index': idx, 'notes': slide['notes'],
            'audio_file': str(wav), 'audio_duration': dur,
            'slide_duration': slide_duration, 'start_time': cumulative
        })
        cumulative += slide_duration
    new_timeline['total_duration'] = cumulative
    
    with open(WORKDIR / 'timeline_v2.json', 'w') as f:
        json.dump(new_timeline, f, indent=2)
    
    # 2. Create clips with fade transitions
    print(f"🎬 Creating clips with {FADE_DURATION}s fades...")
    for slide in new_timeline['slides']:
        idx = slide['index']
        dur = slide['audio_duration']
        img = WORKDIR / 'slides' / f"slide_{idx:03d}.png"
        wav = ASSETS / f"slide_{idx:03d}.wav"
        clip = CLIPS / f"clip_{idx:03d}.mp4"
        
        vf = (
            f"scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2,"
            f"fade=t=in:st=0:d={FADE_DURATION}:alpha=1,"
            f"fade=t=out:st={dur-FADE_DURATION}:d={FADE_DURATION}:alpha=1"
        )
        
        cmd = [
            'ffmpeg', '-y', '-loop', '1', '-framerate', '25', '-i', str(img),
            '-i', str(wav), '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
            '-t', str(dur + FADE_DURATION), '-vf', vf,
            '-c:a', 'aac', '-b:a', '192k', '-pix_fmt', 'yuv420p', '-shortest', str(clip)
        ]
        result = run(cmd)
        if result.returncode != 0:
            print(f"ERROR clip {idx}: {result.stderr[:500]}")
            sys.exit(1)
        print(f"  Clip {idx}: OK")
    
    # 3. Concatenate video clips
    print("🎞️ Concatenating clips...")
    filelist = WORKDIR / "concat_enhanced.txt"
    with open(filelist, 'w') as f:
        for s in new_timeline['slides']:
            f.write(f"file 'clips_enhanced/clip_{s['index']:03d}.mp4'\n")
    
    run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(filelist),
         '-c', 'copy', str(WORKDIR / 'concat_video_temp.mp4')])
    
    # 4. Combine narration audio
    print("🎵 Combining narration...")
    audio_files = [str(ASSETS / f"slide_{s['index']:03d}.wav") for s in new_timeline['slides']]
    af = ''.join(f"[{i}:a]" for i in range(len(audio_files)))
    af += f"concat=n={len(audio_files)}:v=0:a=1[aout]"
    
    cmd = ['ffmpeg', '-y'] + [item for f in audio_files for item in ('-i', f)]
    cmd += ['-filter_complex', af, '-map', '[aout]', str(WORKDIR / 'combined_narration.wav')]
    run(cmd)
    
    # 5. Mix with background music
    print("🎼 Mixing background music...")
    narr_dur = get_duration(WORKDIR / 'combined_narration.wav')
    
    run(['ffmpeg', '-y', '-i', str(WORKDIR / 'combined_narration.wav'),
         '-i', str(ASSETS / 'background_music.wav'),
         '-filter_complex',
         f'[1:a]volume=0.08,afade=t=in:st=0:d=2,afade=t=out:st={narr_dur-3}:d=3[bg];'
         f'[0:a][bg]amix=inputs=2:duration=first:dropout_transition=3[aout]',
         '-map', '[aout]', '-c:a', 'aac', '-b:a', '192k',
         str(WORKDIR / 'final_mixed_audio.m4a')])
    
    # 6. Burn captions (ASS format recommended)
    print("📝 Burning ASS captions...")
    ass_file = str(WORKDIR / 'captions.ass').replace(':', '\\:')
    
    result = run(['ffmpeg', '-y', '-i', str(WORKDIR / 'concat_video_temp.mp4'),
                  '-vf', f"subtitles={ass_file}",
                  '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
                  '-an', '-pix_fmt', 'yuv420p',
                  str(WORKDIR / 'video_with_captions.mp4')])
    
    video_input = (WORKDIR / 'video_with_captions.mp4' 
                   if result.returncode == 0 
                   else WORKDIR / 'concat_video_temp.mp4')
    
    # 7. Final mux
    print("🔧 Final assembly...")
    run(['ffmpeg', '-y', '-i', str(video_input),
         '-i', str(WORKDIR / 'final_mixed_audio.m4a'),
         '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
         '-shortest',
         str(WORKDIR / 'agentic-ai-enhanced.mp4')])
    
    dur = get_duration(WORKDIR / 'agentic-ai-enhanced.mp4')
    print(f"\n✅ SUCCESS: agentic-ai-enhanced.mp4 ({dur:.1f}s)")

if __name__ == '__main__':
    build()
```

---

## Creating Captions (ASS Format — Recommended)

For professional, non-distracting captions, use **ASS (Advanced SubStation Alpha)** instead of SRT. This provides:

- **Bottom positioning** — Fixed at bottom-center of screen (not floating)
- **Phrase-by-phrase timing** — Each caption is 4-6 words max, synchronized to speech
- **Smooth fade transitions** — 300ms fade in/out between phrases
- **Karaoke-style highlighting** — Words light up as they're spoken (`\k` tag)
- **Pixel-perfect positioning** — Exact coordinates via `\pos(x,y)`

### Script: generate_ass_captions.py

```python
#!/usr/bin/env python3
"""Generate ASS subtitles with bottom positioning and sync timing."""
import json, re
from pathlib import Path
from datetime import timedelta

def sec_to_ass(seconds):
    """Convert seconds to ASS time format: H:MM:SS.cc"""
    td = timedelta(seconds=seconds)
    total = int(td.total_seconds() * 100)
    hours = total // 360000
    minutes = (total % 360000) // 6000
    secs = (total % 6000) // 100
    cents = total % 100
    return f"{hours}:{minutes:02d}:{secs:02d}.{cents:02d}"

def split_into_phrases(text, max_words=5):
    """Split narration into natural 4-6 word phrases."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    
    phrases = []
    for sentence in sentences:
        words = sentence.split()
        if len(words) <= max_words:
            phrases.append(sentence)
            continue
        
        # Split by commas, semicolons, dashes first
        parts = re.split(r'[,;:\-–—]\s*', sentence)
        parts = [p.strip() for p in parts if p.strip()]
        
        for part in parts:
            words = part.split()
            if len(words) <= max_words:
                if len(part) > 3:
                    phrases.append(part)
                continue
            
            # Split into 4-5 word chunks
            for i in range(0, len(words), max_words):
                chunk = words[i:i+max_words]
                phrase = ' '.join(chunk).strip(',.;:-–—').strip()
                if len(phrase) > 3:
                    phrases.append(phrase)
    
    return [p for p in phrases if len(p) > 3]

def generate_ass(timeline_file='timeline_v2.json', output='captions.ass'):
    with open(timeline_file) as f:
        timeline = json.load(f)
    
    header = """[Script Info]
Title: Presentation Captions
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
Timer: 100.0000

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,36,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,2,40,40,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    lines = [header]
    
    for slide in timeline['slides']:
        idx = slide['index']
        notes = slide['notes']
        duration = slide['audio_duration']
        start_time = slide['start_time']
        
        phrases = split_into_phrases(notes)
        if not phrases:
            continue
        
        phrase_duration = duration / len(phrases)
        
        for i, phrase in enumerate(phrases):
            phrase_start = start_time + (i * phrase_duration)
            phrase_end = phrase_start + phrase_duration
            
            # Karaoke word timing
            words = phrase.split()
            word_cs = int((phrase_duration * 100) / max(1, len(words)))  # centiseconds
            karaoke_text = ' '.join(f"{{\\k{word_cs}}}{w}" for w in words)
            
            # Bottom-center with fade
            text = f"{{\\an2\\pos(960,980)\\fad(300,300)}}{karaoke_text}"
            event = f"Dialogue: 0,{sec_to_ass(phrase_start)},{sec_to_ass(phrase_end)},Default,,0,0,0,,{text}"
            lines.append(event)
    
    with open(output, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ ASS captions: {output} ({len(lines)-11} events)")

if __name__ == '__main__':
    generate_ass()
```

**Key ASS features used:**
- `\an2` — Bottom-center alignment
- `\pos(960,980)` — Center X=960, bottom Y=980 (1080p)
- `\fad(300,300)` — 300ms fade in, 300ms fade out
- `\k<cs>` — Karaoke timing per word in centiseconds
- `PlayResX/Y` — Resolution anchors for positioning

**Burning ASS into video:**
```bash
ffmpeg -i concat_video_temp.mp4 -vf "subtitles=captions.ass" \
       -c:v libx264 -preset medium -crf 23 \
       -an -pix_fmt yuv420p video_with_captions.mp4
```

**Why ASS over SRT?**
| Feature | SRT | ASS |
|---------|-----|-----|
| Positioning | Limited | Pixel-perfect `\pos(x,y)` |
| Fade effects | None | Native `\fad()` |
| Word timing | None | Karaoke `\k` tags |
| Animation | None | Full scripting support |
| Transparency | None | Alpha channel support |

---

## Creating Background Music

Generate a subtle ambient track with ffmpeg:

```bash
ffmpeg -y -f lavfi -i "sine=frequency=196:duration=260" \
       -f lavfi -i "sine=frequency=246:duration=260" \
       -f lavfi -i "sine=frequency=293:duration=260" \
       -filter_complex "[0:a][1:a][2:a]amix=inputs=3:duration=longest,"
                       "volume=0.08,lowpass=f=600,aecho=0.6:0.5:1200:0.2" \
       -ar 24000 -ac 1 assets/background_music.wav
```

**Mix settings:**
- `volume=0.08` — Music at 8% volume
- `lowpass=f=600` — Filter out high frequencies
- `aecho` — Gentle reverb for ambience
- `afade` — Fade in/out at start/end

---

## Key Technical Details

**Why concat demuxer instead of filter_complex concat?**

The old `filter_complex concat` approach corrupts the H.264 NAL stream when combining many raw image inputs. The correct approach:
1. Create individual MP4 clips first (properly encoded)
2. Use `ffmpeg -f concat -safe 0 -i filelist.txt` to join them
3. Mux with separately-combined audio

> **⚠️ CRITICAL ffmpeg BUG:** Do NOT use `-movflags +faststart` on videos longer than ~60s with ffmpeg 6.x. It corrupts the H.264 NAL stream ("Invalid NAL unit size" errors). If you need streaming-friendly MP4, apply faststart as a **separate post-process step** after verifying the video is valid.
>
> **Working approach:**
> ```python
> # PASS 1: Build video WITHOUT -movflags
> subprocess.run(['ffmpeg', '-y',
>     '-i', 'video.mp4', '-i', 'audio.m4a',
>     '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
>     '-shortest', 'output.mp4'])  # NO -movflags
> 
> # PASS 2 (optional): Burn subtitles onto valid video
> subprocess.run(['ffmpeg', '-y',
>     '-i', 'output.mp4', '-vf', 'subtitles=captions.ass',
>     '-c:v', 'libx264', '-c:a', 'copy',
>     'final.mp4'])
> ```

**Audio mixing strategy:**
1. Concat all narration WAV files into one track
2. Process background music (volume down, fade in/out)
3. Use `amix` filter with `duration=first` to align lengths
4. Mux final mixed audio with concatenated video

**Fade transitions:**
- Use `fade=t=in:st=0:d=0.5:alpha=1` for video fade-in
- Use `fade=t=out:st=<DUR-0.5>:d=0.5:alpha=1` for fade-out
- Add `FADE_DURATION = 0.5` overlap in clip timing

---

## Quick Start

```bash
# 1. Render Quarto to reveal.js HTML
quarto render slides.qmd --to revealjs

# 2. Extract notes & generate TTS
python3 extract_notes.py  # creates assets/*.wav

# 3. Capture screenshots
python3 screenshot_slides.py  # creates slides/*.png

    # 4. Optional: Generate background music and captions.ass

# 5. Build final video (with all enhancements)
python3 build_enhanced.py  # creates agentic-ai-enhanced.mp4
```

---

## File Structure

```
skill-test/
├── slides.qmd              # Source presentation
├── presentation.html       # Rendered reveal.js output
├── slides/
│   └── slide_*.png         # Screenshots
├── assets/
│   ├── slide_*.wav         # TTS narration per slide
│   └── background_music.wav
├── clips_enhanced/         # Individual MP4 clips
├── captions.ass            # ASS subtitles (recommended)
├── captions.srt            # SRT subtitles (fallback)
├── timeline.json           # Original timing data
├── timeline_v2.json        # Recalibrated with actual durations
├── generate_ass_captions.py # ASS caption generator
├── build_enhanced.py       # Main production build script
└── agentic-ai-enhanced.mp4 # FINAL OUTPUT
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Black video / codec corruption (Invalid NAL unit size) | **Do NOT use `-movflags +faststart`** on long videos — it corrupts H.264 in ffmpeg 6.x. Use clean two-pass: pass 1 = concat+audio, pass 2 = burn subtitles. Also avoid concat demuxer on raw images; use filter_complex concat with re-encode. |
| TTS API rate limits | Add `time.sleep(2)` between requests |
| Audio/video out of sync | Ensure `-shortest` flag and accurate durations |
| Captions not visible | Check SRT timestamps match timeline; fallback to no captions |
| Chrome screenshots blank | Check `--window-size=1920,1080` and URL format |
| Background music too loud | Reduce `volume=0.08` to `0.05` or lower |

---

## Author

Created as reusable OpenCode skill for automated presentation video production.

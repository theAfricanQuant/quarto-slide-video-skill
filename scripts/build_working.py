#!/usr/bin/env python3
"""
WORKING BUILD - Two clean passes, NO -movflags +faststart.
Pass 1: Video + Audio + Fade + BGM via filter_complex concat
Pass 2: Burn subtitles onto the valid video
"""
import json, subprocess, sys
from pathlib import Path

WORKDIR = Path("/home/siseng/Documents/hyperframes/skill-test-nigeria-ai")

with open(WORKDIR / 'timeline_v2.json') as f:
    timeline = json.load(f)

slides = timeline['slides']
n = len(slides)

# === PASS 1: Build video+audio ===
inputs = []
vf_parts = []
af_parts = []

for i, slide in enumerate(slides):
    idx = slide['index']
    dur = slide['audio_duration']
    img = WORKDIR / 'slides' / f"slide_{idx:03d}.png"
    wav = WORKDIR / 'assets' / f"slide_{idx:03d}.wav"
    
    inputs.extend(['-loop', '1', '-t', str(dur + 0.5), '-i', str(img)])
    inputs.extend(['-i', str(wav)])
    
    vf_parts.append(
        f"[{i*2}:v]scale=1920:1080:force_original_aspect_ratio=decrease,"
        f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2,"
        f"fade=t=in:st=0:d=0.5:alpha=1,"
        f"fade=t=out:st={dur}:d=0.5:alpha=1[v{i}]"
    )
    af_parts.append(f"[{i*2+1}:a]aformat=sample_fmts=fltp:sample_rates=24000:channel_layouts=mono[a{i}]")

vconcat = ''.join(f"[v{i}]" for i in range(n))
vf_parts.append(f"{vconcat}concat=n={n}:v=1:a=0[vid]")

aconcat = ''.join(f"[a{i}]" for i in range(n))
af_parts.append(f"{aconcat}concat=n={n}:v=0:a=1[aud]")

bgm = WORKDIR / 'assets' / 'background_music.wav'
inputs.extend(['-i', str(bgm)])
bgm_idx = n * 2
af_parts.append(
    f"[{bgm_idx}:a]volume=0.08,afade=t=in:st=0:d=2,"
    f"afade=t=out:st=243:d=3[bgm]"
)
af_parts.append("[aud][bgm]amix=inputs=2:duration=first:dropout_transition=3[finala]")

pass1_cmd = [
    'ffmpeg', '-y',
    *inputs,
    '-filter_complex', ';'.join(vf_parts + af_parts),
    '-map', '[vid]',
    '-map', '[finala]',
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
    '-c:a', 'aac', '-b:a', '192k',
    '-pix_fmt', 'yuv420p',
    '-shortest',
    str(WORKDIR / 'agentic-ai-pass1.mp4')
]

print(f"PASS 1: Building {n} segments...")
result = subprocess.run(pass1_cmd, capture_output=True, text=True)
if result.returncode != 0:
    print("PASS 1 FAILED")
    print(result.stderr[-500:])
    sys.exit(1)

# Verify pass 1
print("Verifying pass 1...")
result = subprocess.run(
    ['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
     '-show_entries', 'stream=nb_read_frames,duration', '-of', 'csv',
     str(WORKDIR / 'agentic-ai-pass1.mp4')],
    capture_output=True, text=True
)
print(result.stdout.strip())

# === PASS 2: Burn subtitles ===
print("\nPASS 2: Burning subtitles...")
pass2_cmd = [
    'ffmpeg', '-y',
    '-i', str(WORKDIR / 'agentic-ai-pass1.mp4'),
    '-vf', 'subtitles=captions.ass',
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
    '-c:a', 'copy',
    '-pix_fmt', 'yuv420p',
    str(WORKDIR / 'agentic-ai-FINAL.mp4')
]

result = subprocess.run(pass2_cmd, capture_output=True, text=True)
if result.returncode != 0:
    print("PASS 2 FAILED")
    print(result.stderr[-500:])
    sys.exit(1)

# Verify pass 2
print("Verifying final output...")
result = subprocess.run(
    ['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
     '-show_entries', 'stream=nb_read_frames,duration', '-of', 'csv',
     str(WORKDIR / 'agentic-ai-FINAL.mp4')],
    capture_output=True, text=True
)
print(result.stdout.strip())
print("\n✅ DONE: agentic-ai-FINAL.mp4")

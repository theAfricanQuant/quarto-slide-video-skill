#!/usr/bin/env python3
"""
Generate ASS subtitles with:
- Bottom-screen positioning
- One line per caption (max 5-6 words)
- Phrase-by-phrase splitting based on punctuation and clauses
- Fade in/out transitions synced to voice
- Exact timing matching slide audio durations
"""
import json, re
from pathlib import Path
from datetime import timedelta

WORKDIR = Path("/home/siseng/Documents/hyperframes/skill-test-nigeria-ai")

def sec_to_ass(seconds):
    """Convert seconds to ASS time format: H:MM:SS.cc"""
    td = timedelta(seconds=seconds)
    total = int(td.total_seconds() * 100)
    hours = total // 360000
    minutes = (total % 360000) // 6000
    secs = (total % 6000) // 100
    cents = total % 100
    return f"{hours}:{minutes:02d}:{secs:02d}.{cents:02d}"

def split_into_phrases(text, target_chunks=None):
    """Split text into natural phrases for captions.
    
    Strategy:
    1. First split by sentence-ending punctuation (.!?)
    2. Then split long sentences by commas, semicolons, dashes
    3. Ensure each chunk is 2-6 words
    4. If still too long, split by conjunctions/prepositions
    """
    # Clean up text
    text = text.strip()
    
    # Split by sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    phrases = []
    for sentence in sentences:
        # If sentence is short enough, keep as one phrase
        words = sentence.split()
        if len(words) <= 6:
            phrases.append(sentence)
            continue
        
        # Split by commas, semicolons, dashes, colons
        parts = re.split(r'[,;:\-–—]\s*', sentence)
        parts = [p.strip() for p in parts if p.strip()]
        
        for part in parts:
            words = part.split()
            if len(words) <= 6:
                if part not in ['and', 'or', 'but', 'for', 'with', 'from', 'to', 'of', 'in', 'on', 'at', 'by']:
                    phrases.append(part)
                continue
            
            # Split by conjunctions for very long parts
            # Split into chunks of 4-5 words
            for i in range(0, len(words), 5):
                chunk = words[i:i+5]
                phrase = ' '.join(chunk)
                # Clean up: remove trailing punctuation, capitalize first letter
                phrase = phrase.strip(',.;:-–—').strip()
                if phrase and len(phrase) > 3:
                    phrases.append(phrase)
    
    # Final filter: remove very short fragments that are standalone conjunctions
    filtered = []
    for p in phrases:
        p = p.strip()
        if len(p) > 3 and p.lower() not in ['and', 'or', 'but', 'for', 'with', 'from', 'to', 'of']:
            filtered.append(p)
    
    # If we have target_chunks and too few phrases, split largest ones
    if target_chunks and len(filtered) < target_chunks:
        while len(filtered) < target_chunks:
            # Find longest phrase and split it
            longest_idx = max(range(len(filtered)), key=lambda i: len(filtered[i].split()))
            words = filtered[longest_idx].split()
            if len(words) <= 3:
                break
            mid = len(words) // 2
            left = ' '.join(words[:mid])
            right = ' '.join(words[mid:])
            filtered[longest_idx:longest_idx+1] = [left, right]
    
    return filtered

def generate_ass():
    # Read timeline
    with open(WORKDIR / 'timeline_v2.json') as f:
        timeline = json.load(f)
    
    ass_lines = []
    
    # ASS Header with style for bottom-center captions
    header = """[Script Info]
Title: Agentic AI Presentation Captions
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
    
    ass_lines.append(header)
    
    # Generate caption events for each slide
    for slide in timeline['slides']:
        idx = slide['index']
        notes = slide['notes']
        duration = slide['audio_duration']
        start_time = slide['start_time']
        
        # Split into natural phrases
        phrases = split_into_phrases(notes)
        
        if not phrases:
            continue
        
        # Calculate timing for each phrase
        # Each phrase gets equal time, with small padding at start/end
        phrase_duration = duration / len(phrases)
        
        for i, phrase in enumerate(phrases):
            # Fade in/out: 300ms each
            fade_in = 300
            fade_out = 300
            
            phrase_start = start_time + (i * phrase_duration)
            phrase_end = phrase_start + phrase_duration
            
            # Word-by-word karaoke effect using \k tags
            # Split phrase into words, each gets proportional time
            words = phrase.split()
            if len(words) > 1:
                word_duration = int((phrase_duration * 100) / len(words))  # in centiseconds
                karaoke_text = ''
                for word in words:
                    karaoke_text += f"{{\\k{word_duration}}}{word} "
                caption_text = karaoke_text.strip()
            else:
                caption_text = phrase
            
            # Position at bottom center with fade
            # \pos(960, 980) = center horizontally, near bottom
            # \fad(300,300) = fade in 300ms, fade out 300ms
            # \an2 = bottom-center alignment
            text = f"{{\\an2\\pos(960,980)\\fad({fade_in},{fade_out})}}{caption_text}"
            
            event = f"Dialogue: 0,{sec_to_ass(phrase_start)},{sec_to_ass(phrase_end)},Default,,0,0,0,,{text}"
            ass_lines.append(event)
        
        print(f"Slide {idx}: {len(phrases)} phrases over {duration:.1f}s")
    
    # Write ASS file
    ass_path = WORKDIR / 'captions.ass'
    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(ass_lines))
    
    print(f"\n✅ Generated ASS: {ass_path}")
    print(f"   Total events: {len(ass_lines) - 11}")  # minus header lines

if __name__ == '__main__':
    generate_ass()

#!/usr/bin/env python3
"""
Generate ASS captions showing COMPLETE SENTENCES only.
Each sentence is displayed as one caption, timed proportionally by word count.
Sync points are at sentence boundaries (periods, questions, exclamations).
"""
import json, re
from pathlib import Path

def sec_to_ass(seconds):
    """Convert seconds to ASS time format: H:MM:SS.cc"""
    total_cs = int(seconds * 100)  # centiseconds
    hours = total_cs // 360000
    minutes = (total_cs % 360000) // 6000
    secs = (total_cs % 6000) // 100
    cents = total_cs % 100
    return f"{hours}:{minutes:02d}:{secs:02d}.{cents:02d}"

def split_into_sentences(text):
    """Split text into complete sentences."""
    # Match periods, question marks, and exclamation marks followed by space or end
    # But not abbreviations like "Mr." or "i.e."
    text = text.strip()
    
    # Add a space at end to capture last sentence
    text = text + " "
    
    # Split by sentence-ending punctuation
    # Pattern: punctuation + optional space + capital letter or end
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])\s*$', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences

def generate_ass():
    with open('/home/siseng/Documents/hyperframes/skill-test-nigeria-ai/timeline_v2.json') as f:
        timeline = json.load(f)
    
    header = """[Script Info]
Title: Presentation Sentence Captions
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
Timer: 100.0000

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,40,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,1,2,40,40,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    lines = [header]
    total_events = 0
    
    for slide in timeline['slides']:
        idx = slide['index']
        notes = slide['notes']
        audio_duration = slide['audio_duration']  # Exact audio length
        slide_start = slide['start_time']
        
        # Split into sentences
        sentences = split_into_sentences(notes)
        if not sentences:
            continue
        
        # Calculate timing proportionally by word count
        word_counts = [len(s.split()) for s in sentences]
        total_words = sum(word_counts)
        
        current_time = 0
        for i, sentence in enumerate(sentences):
            # Proportional duration based on word count
            ratio = word_counts[i] / total_words if total_words > 0 else 1 / len(sentences)
            sentence_duration = audio_duration * ratio
            
            start = slide_start + current_time
            end = start + sentence_duration
            
            # Fade: 200ms in, 200ms out at the END of the sentence
            # This makes the transition smooth but keeps text fully visible during reading
            fade_out_duration = 200  # ms
            fade_in_duration = 200   # ms
            
            # Position: bottom center, slightly higher so it doesn't overlap slide numbers
            # \an2 = bottom-center alignment
            # \pos(960, 1000) = horizontal center, slightly up from very bottom
            text = f"{{\\an2\\pos(960,1000)\\fad({fade_in_duration},{fade_out_duration})}}{sentence}"
            
            event = f"Dialogue: 0,{sec_to_ass(start)},{sec_to_ass(end)},Default,,0,0,0,,{text}"
            lines.append(event)
            total_events += 1
            
            current_time += sentence_duration
            
            print(f"Slide {idx}: Sentence {i+1}/{len(sentences)} "
                  f"({word_counts[i]} words, {sentence_duration:.1f}s) "
                  f"| {sentence[:50]}...")
    
    ass_path = '/home/siseng/Documents/hyperframes/skill-test-nigeria-ai/captions.ass'
    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"\n✅ Generated {ass_path}")
    print(f"   Total sentence events: {total_events}")
    print(f"   Captions show COMPLETE SENTENCES with proportional timing")

if __name__ == '__main__':
    generate_ass()

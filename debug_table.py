#!/usr/bin/env python3
import re
from pathlib import Path

# Simplified version to check raw output
def simple_rtf_to_text(rtf_content):
    """Convert RTF to plain text by removing all RTF codes and table markers."""
    
    text = rtf_content
    
    # Remove RTF header and all metadata sections first
    text = re.sub(r'\{\\fonttbl[^}]*(?:\{[^}]*\})*[^}]*\}', '', text, flags=re.DOTALL)
    text = re.sub(r'\{\\colortbl[^}]*\}', '', text, flags=re.DOTALL)
    text = re.sub(r'\{\\stylesheet[^}]*(?:\{[^}]*\})*[^}]*\}', '', text, flags=re.DOTALL)
    text = re.sub(r'\{\\listdef[^}]*(?:\{[^}]*\})*[^}]*\}', '', text, flags=re.DOTALL)
    text = re.sub(r'\{\\info[^}]*(?:\{[^}]*\})*[^}]*\}', '', text, flags=re.DOTALL)
    
    # Remove RTF special character sequences - convert to ASCII equivalents
    text = text.replace('\\endash', '-')
    text = text.replace('\\emdash', '--')
    text = text.replace('\\ldblquote', '"')
    text = text.replace('\\rdblquote', '"')
    text = text.replace('\\lquote', "'")
    text = text.replace('\\rquote', "'")
    text = text.replace('\\tab', '\t')
    text = text.replace('\\par', '\n')
    text = text.replace('\\\'' + '92', '"')
    
    # Remove all RTF control codes systematically
    text = re.sub(r'\{\\\*[^}]*\}', '', text)
    text = re.sub(r'\\[a-z]+\d*\s?', ' ', text)
    text = re.sub(r"\\\'[0-9a-f]{2}", '', text, flags=re.IGNORECASE)
    text = re.sub(r'\\u-?\d+\?', '', text)
    
    # Remove table control codes but preserve Table: label lines
    text = re.sub(r'\\trowd[^\\]*', '', text)
    text = re.sub(r'\\trgaph\d+', '', text)
    text = re.sub(r'\\trleft-?\d+', '', text)
    text = re.sub(r'\\cellx\d+', '', text)
    text = re.sub(r'\\row\s*', '\n', text)
    text = re.sub(r'\\cell\s*', ' ', text)
    
    # Remove braces carefully
    while '{}' in text or '{ }' in text:
        text = text.replace('{}', '')
        text = text.replace('{ }', '')
    text = re.sub(r'[{}]', '', text)
    
    # Remove common RTF artifacts
    text = re.sub(r'\bWidth\d+\b', '', text)
    text = re.sub(r'\s*-108\s*', ' ', text)
    text = re.sub(r'\bbin\b', '', text)
    text = re.sub(r'\bclfts\b', '', text)
    text = re.sub(r'\bclw\b', '', text)
    text = re.sub(r'\bcf\d+\b', '', text)
    text = re.sub(r'\bfs\d+\b', '', text)
    text = re.sub(r'\bltrch\b', '', text)
    text = re.sub(r'\brtlch\b', '', text)
    
    # Remove standalone 'd' characters
    text = re.sub(r'^\s*d\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s+d\s+', ' ', text)
    
    # Normalize whitespace
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n\n+', '\n\n', text)
    text = re.sub(r' +\n', '\n', text)
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # Remove blank lines but preserve paragraph breaks
    text = re.sub(r'\n\n\n+', '\n\n', text)
    
    # Fix line breaks in the middle of words
    text = re.sub(r'(\w)\s*\n\s*(\w)', r'\1 \2', text)
    
    return text.strip()

# Read and convert just CombatI
with open('d:/git/srd/original/CombatI.rtf', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

result = simple_rtf_to_text(content)

# Find the table section
idx = result.find('Table: Size Modifiers')
if idx >= 0:
    section = result[idx:idx+300]
    print("After RTF cleaning, before heading processing:")
    print(repr(section))
    print()
    
    # Show line-by-line
    print("Line by line:")
    for i, line in enumerate(section.split('\n')[:15]):
        print(f"  {i}: {repr(line)}")

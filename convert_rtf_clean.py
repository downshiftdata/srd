#!/usr/bin/env python3
import re
import os
from pathlib import Path

def rtf_to_text(rtf_content):
    text = rtf_content
    
    # Remove metadata sections
    result = []
    i = 0
    skip_until_close = -1
    skip_keywords = ('fonttbl', 'colortbl', 'stylesheet', 'listtable', 'listoverridetable', 'info', 'revtbl')
    brace_depth = 0
    
    while i < len(text):
        char = text[i]
        
        if char == '{' and skip_until_close == -1:
            remaining = text[i:i+50]
            should_skip = False
            
            for keyword in skip_keywords:
                if '\\' + keyword in remaining[:20]:
                    should_skip = True
                    break
            
            if '\\*' in remaining[:10]:
                should_skip = True
            
            if should_skip:
                skip_until_close = 0
                brace_depth = 1
                i += 1
                continue
        
        if skip_until_close != -1:
            if char == '{':
                brace_depth += 1
            elif char == '}':
                brace_depth -= 1
                if brace_depth == 0:
                    skip_until_close = -1
            i += 1
            continue
        
        result.append(char)
        i += 1
    
    text = ''.join(result)
    
    # Remove table cell and row markers
    text = re.sub(r'\\trowd\b', '', text)
    text = re.sub(r'\\cell\b', '\t', text)
    text = re.sub(r'\\row\b', '\n', text)
    text = re.sub(r'\\tr\w+\b', '', text)
    
    # Remove RTF control sequences
    text = re.sub(r'\\[a-z]+[0-9]*\s?', '', text)
    text = re.sub(r"\\'[0-9a-f]{2}", '', text)
    text = re.sub(r'[{}]', '', text)
    text = re.sub(r'\\', '', text)
    
    # Replace escape sequences
    text = text.replace('endash', '–')
    text = text.replace('emdash', '—')
    text = text.replace('rquote', "'")
    text = text.replace('lquote', "'")
    text = text.replace('ldblquote', '"')
    text = text.replace('rdblquote', '"')
    text = text.replace('par', '\n')
    text = text.replace('tab', '\t')
    
    # Remove table artifacts
    text = re.sub(r'\bWidth\d+\b\s*', '', text)
    text = re.sub(r'\b108\b\s*', '', text)
    
    # Clean spacing
    text = re.sub(r'\t +', '\t', text)
    text = re.sub(r' +\t', '\t', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    
    lines = text.split('\n')
    lines = [line.rstrip() for line in lines]
    text = '\n'.join(lines)
    text = text.strip()
    
    return text

def convert_rtf_files(source_dir, target_dir):
    source_path = Path(source_dir)
    target_path = Path(target_dir)
    
    target_path.mkdir(parents=True, exist_ok=True)
    
    rtf_files = sorted(source_path.glob('*.rtf'))
    
    if not rtf_files:
        print(f"No RTF files found in {source_dir}")
        return
    
    print(f"Found {len(rtf_files)} RTF files to convert\n")
    
    for idx, rtf_file in enumerate(rtf_files, 1):
        md_filename = rtf_file.stem + '.md'
        md_path = target_path / md_filename
        
        print(f"[{idx}/{len(rtf_files)}] Converting {rtf_file.name} -> {md_filename}", end='')
        
        try:
            with open(rtf_file, 'r', encoding='utf-8', errors='ignore') as f:
                rtf_content = f.read()
            
            text = rtf_to_text(rtf_content)
            
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(" OK")
        except Exception as e:
            print(f" ERROR: {e}")
    
    print(f"\nConversion complete. Files saved to: {target_dir}")

if __name__ == '__main__':
    source_dir = r'd:\git\srd\original'
    target_dir = r'd:\git\srd\markdown'
    convert_rtf_files(source_dir, target_dir)

#!/usr/bin/env python3
import re
from pathlib import Path

def extract_rtf_text_and_tables(rtf_content):
    """Extract text and table structure from RTF, preserving tables."""
    
    # Remove RTF header and metadata
    text = rtf_content
    
    # Remove metadata sections (fonttbl, colortbl, stylesheet, etc.)
    text = re.sub(r'\{\\fonttbl[^}]*(?:\{[^}]*\})*[^}]*\}', '', text)
    text = re.sub(r'\{\\colortbl[^}]*\}', '', text)
    text = re.sub(r'\{\\stylesheet[^}]*(?:\{[^}]*\})*[^}]*\}', '', text)
    text = re.sub(r'\{\\listdef[^}]*(?:\{[^}]*\})*[^}]*\}', '', text)
    text = re.sub(r'\{\\info[^}]*(?:\{[^}]*\})*[^}]*\}', '', text)
    
    # First pass: identify table rows and mark them
    # Tables are structured with \trowd ... \row markers
    table_pattern = r'\\trowd(.*?)\\row'
    tables = []
    text_parts = []
    last_end = 0
    
    for match in re.finditer(table_pattern, text, re.DOTALL):
        # Add text before this table
        text_parts.append(('text', text[last_end:match.start()]))
        
        # Extract table row
        row_content = match.group(1)
        tables.append(('table', row_content))
        text_parts.append(('table', len(tables) - 1))
        
        last_end = match.end()
    
    # Add remaining text
    text_parts.append(('text', text[last_end:]))
    
    # Process text parts to clean up RTF codes
    processed_text = []
    for part_type, content in text_parts:
        if part_type == 'text':
            processed_text.append(('text', clean_rtf_text(content)))
        else:
            # Keep table reference for later processing
            processed_text.append(('table', content))
    
    # Now extract cells from tables
    final_output = []
    for part_type, content in processed_text:
        if part_type == 'text':
            if content.strip():
                final_output.append(content)
        else:
            # Process table
            table_md = extract_table_from_row(tables[content][1])
            if table_md:
                final_output.append(table_md)
    
    return '\n'.join(final_output)

def extract_table_from_row(row_content):
    """Extract cells from a single table row (or multiple rows between \\row markers)."""
    
    # Split by \row to get individual rows
    row_pattern = r'\\trowd(.*?)(?=\\trowd|$)'
    rows = []
    
    # Find all cells in this row block
    cell_pattern = r'([^\\]*?)\\cell'
    
    for match in re.finditer(cell_pattern, row_content):
        cell_content = match.group(1)
        # Clean the cell
        cell_text = clean_rtf_text(cell_content).strip()
        if cell_text or len(rows[-1]) > 0 if rows else True:
            if not rows:
                rows.append([])
            rows[-1].append(cell_text)
    
    if not rows or not rows[0]:
        return None
    
    # Check if first row looks like a header (often contains table title)
    first_row = rows[0]
    
    # Build markdown table
    lines = []
    
    # Add header row
    lines.append('| ' + ' | '.join(first_row) + ' |')
    
    # Add separator
    lines.append('| ' + ' | '.join(['---' for _ in first_row]) + ' |')
    
    # Add data rows
    for row in rows[1:]:
        # Pad row to match header length
        while len(row) < len(first_row):
            row.append('')
        lines.append('| ' + ' | '.join(row[:len(first_row)]) + ' |')
    
    return '\n'.join(lines)

def clean_rtf_text(text):
    """Remove RTF control codes and clean up text."""
    
    # Remove braced content that's just formatting (but keep content in braces with text)
    # This is tricky - we want to remove {\b ...} but keep the text inside
    text = re.sub(r'\{([^{}]*?)\}', r'\1', text)
    
    # Remove RTF control codes
    # Pattern: backslash followed by letters, optional digits
    text = re.sub(r'\\[a-z]+\d*\s?', ' ', text)
    text = re.sub(r'\\[a-z]+\d*\s?', ' ', text)  # Run twice for nested
    
    # Remove special RTF sequences
    text = re.sub(r"\\\'[0-9a-f]{2}", '', text)  # Hex characters
    text = re.sub(r'\\u-?\d+\?', '', text)  # Unicode escapes
    text = re.sub(r'[{}]', '', text)  # Remove remaining braces
    
    # Clean up common RTF artifacts
    text = re.sub(r'-108', '', text)
    text = re.sub(r'Width\d+', '', text)
    
    # Replace RTF special characters
    text = text.replace('\\endash', '–')
    text = text.replace('\\emdash', '—')
    text = text.replace('\\lquote', ''')
    text = text.replace('\\rquote', ''')
    text = text.replace('\\ldblquote', '"')
    text = text.replace('\\rdblquote', '"')
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def convert_rtf_files():
    """Convert all RTF files to Markdown."""
    
    source_dir = Path('d:/git/srd/original')
    target_dir = Path('d:/git/srd/markdown')
    target_dir.mkdir(exist_ok=True)
    
    rtf_files = list(source_dir.glob('*.rtf'))
    print(f"Found {len(rtf_files)} RTF files to convert")
    
    for i, rtf_file in enumerate(rtf_files, 1):
        try:
            # Read RTF file
            with open(rtf_file, 'r', encoding='utf-8', errors='ignore') as f:
                rtf_content = f.read()
            
            # Convert to text
            markdown_content = extract_rtf_text_and_tables(rtf_content)
            
            # Write markdown file
            md_file = target_dir / rtf_file.with_suffix('.md').name
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"[{i}/{len(rtf_files)}] {rtf_file.name} -> {md_file.name} [OK]")
            
        except Exception as e:
            print(f"[{i}/{len(rtf_files)}] {rtf_file.name} [ERROR: {e}]")
    
    print(f"\nConversion complete. Files saved to: {target_dir}")

if __name__ == '__main__':
    convert_rtf_files()

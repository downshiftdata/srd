#!/usr/bin/env python3
import re
from pathlib import Path

def rtf_to_markdown(rtf_content):
    """Convert RTF to Markdown with proper table handling."""
    
    # Remove metadata sections completely
    text = rtf_content
    text = re.sub(r'\{\\fonttbl[^}]*(?:\{[^}]*\})*[^}]*\}', '', text)
    text = re.sub(r'\{\\colortbl[^}]*\}', '', text)
    text = re.sub(r'\{\\stylesheet[^}]*(?:\{[^}]*\})*[^}]*\}', '', text)
    text = re.sub(r'\{\\listdef[^}]*(?:\{[^}]*\})*[^}]*\}', '', text)
    text = re.sub(r'\{\\info[^}]*(?:\{[^}]*\})*[^}]*\}', '', text)
    
    # Process content section
    # Extract everything between document start and end
    match = re.search(r'\\colortbl.*?\}(.*?)(?:\\par\s*\}|\})$', text, re.DOTALL)
    if match:
        text = match.group(1)
    
    # Replace RTF special characters
    replacements = {
        '\\endash': '–',
        '\\emdash': '—',
        '\\ldblquote': '"',
        '\\rdblquote': '"',
        '\\lquote': ''',
        '\\rquote': ''',
        '\\\'' + '92': '"',
        '\\tab': '\t',
        '\\par': '\n',
    }
    
    for rtf_seq, replacement in replacements.items():
        text = text.replace(rtf_seq, replacement)
    
    # Extract table rows with their cells
    # Tables have \\trowd ... \\row structure with cells marked by \\cell
    table_rows = []
    current_pos = 0
    
    # Find all table row definitions
    for trowd_match in re.finditer(r'\\trowd\b', text):
        trowd_start = trowd_match.start()
        
        # Find corresponding \row marker
        row_end = text.find(r'\row', trowd_start)
        if row_end == -1:
            row_end = len(text)
        
        row_content = text[trowd_start:row_end]
        
        # Extract cells from this row
        cells = []
        cell_pattern = r'(?:^|\\cell)(.*?)(?=\\cell|$)'
        
        for cell_match in re.finditer(cell_pattern, row_content, re.DOTALL):
            cell_text = cell_match.group(1)
            
            # Clean up the cell
            # Remove RTF formatting codes but preserve text
            cell_text = re.sub(r'\{[^{}]*\}', lambda m: extract_text_from_braces(m.group(0)), cell_text)
            cell_text = re.sub(r'\\[a-z]+\d*\s?', ' ', cell_text)
            cell_text = re.sub(r"\\\'[0-9a-f]{2}", '', cell_text)
            cell_text = re.sub(r'[{}]', '', cell_text)
            cell_text = re.sub(r'\s+', ' ', cell_text)
            cell_text = cell_text.strip()
            
            if cell_text or len(cells) < 5:  # Allow empty cells to maintain table structure
                cells.append(cell_text)
        
        if cells:
            table_rows.append(cells)
    
    # Convert table rows to markdown
    markdown_tables = []
    if table_rows:
        # Determine column count from longest row
        max_cols = max(len(row) for row in table_rows) if table_rows else 0
        
        # Pad all rows to match column count
        for i, row in enumerate(table_rows):
            while len(row) < max_cols:
                row.append('')
        
        # Check if first row looks like header
        first_row = table_rows[0]
        first_row_text = ' '.join(first_row).lower()
        
        # Generate markdown table
        table_lines = []
        
        # Add header row
        table_lines.append('| ' + ' | '.join(first_row[:max_cols]) + ' |')
        
        # Add separator
        table_lines.append('| ' + ' | '.join(['---' for _ in range(max_cols)]) + ' |')
        
        # Add data rows
        for row in table_rows[1:]:
            table_lines.append('| ' + ' | '.join(row[:max_cols]) + ' |')
        
        markdown_tables = '\n'.join(table_lines)
    
    # Remove all RTF codes from main text
    text = re.sub(r'\\[a-z]+\d*\s?', ' ', text)
    text = re.sub(r"\\\'[0-9a-f]{2}", '', text)
    text = re.sub(r'\\bin\b', '', text)
    text = re.sub(r'\{[^{}]*\}', lambda m: extract_text_from_braces(m.group(0)), text)
    text = re.sub(r'[{}]', '', text)
    
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Combine text and tables
    if markdown_tables:
        # Try to find good place to insert tables
        result = text + '\n\n' + markdown_tables
    else:
        result = text
    
    return result

def extract_text_from_braces(braced_text):
    """Extract visible text from RTF braced content."""
    # Remove the outer braces
    inner = braced_text[1:-1] if braced_text.startswith('{') and braced_text.endswith('}') else braced_text
    
    # Remove formatting codes
    inner = re.sub(r'\\[a-z]+\d*\s?', '', inner)
    inner = re.sub(r"\\\'[0-9a-f]{2}", '', inner)
    
    return inner

def convert_rtf_files():
    """Convert all RTF files in directory to Markdown."""
    
    source_dir = Path('d:/git/srd/original')
    target_dir = Path('d:/git/srd/markdown')
    target_dir.mkdir(exist_ok=True)
    
    rtf_files = sorted(source_dir.glob('*.rtf'))
    print(f"Found {len(rtf_files)} RTF files to convert")
    
    for i, rtf_file in enumerate(rtf_files, 1):
        try:
            with open(rtf_file, 'r', encoding='utf-8', errors='ignore') as f:
                rtf_content = f.read()
            
            markdown_content = rtf_to_markdown(rtf_content)
            
            md_file = target_dir / rtf_file.with_suffix('.md').name
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"[{i}/{len(rtf_files)}] {rtf_file.name} -> {md_file.name} [OK]")
            
        except Exception as e:
            print(f"[{i}/{len(rtf_files)}] {rtf_file.name} [ERROR: {str(e)[:50]}]")
    
    print(f"\nConversion complete. Files saved to: {target_dir}")

if __name__ == '__main__':
    convert_rtf_files()

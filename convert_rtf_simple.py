#!/usr/bin/env python3
"""
RTF to Markdown converter with heading detection, table conversion, and proper RTF cleanup.
"""
import re
from pathlib import Path

def extract_rtf_tables(rtf_content):
    """Extract and convert RTF tables to markdown format before text conversion."""
    
    # Pattern to find RTF tables: look for \trowd...\row sequences
    # Tables start with \trowd and end with \row
    table_pattern = r'\\trowd[^\\]*(?:\\row)'
    
    tables = []
    
    for match in re.finditer(table_pattern, rtf_content, re.DOTALL):
        table_rtf = match.group(0)
        tables.append({
            'rtf': table_rtf,
            'start': match.start(),
            'end': match.end()
        })
    
    return tables

def parse_rtf_table_rows(table_rtf):
    """Parse rows and cells from RTF table, extracting only text content."""
    
    # Split by \row to get individual rows
    rows = table_rtf.split('\\row')
    
    table_data = []
    
    for row_idx, row_rtf in enumerate(rows[:-1]):  # Last split will be empty
        # Extract all text segments between braces, avoiding RTF codes
        cells = []
        
        # Find all {} sections that might contain cell content
        # Pattern: { ... text ... }
        brace_pattern = r'\{[^{}]*?\}'
        
        for match in re.finditer(brace_pattern, row_rtf):
            content = match.group(0)[1:-1]  # Remove braces
            
            # Remove RTF codes
            content = re.sub(r'\\[a-z]+\d*', '', content)
            content = re.sub(r'[{}\\]', '', content)
            
            # Clean the text
            content = content.strip()
            
            # Skip if it's just RTF markers or empty
            if content and not any(c in content for c in ['trgaph', 'trpaddl', 'cellx']):
                cells.append(content)
        
        if cells:
            table_data.append(cells)
    
    return table_data

def convert_rtf_table_to_markdown_simple(table_rtf, table_label=''):
    """Convert an RTF table to markdown table format - simplified approach."""
    
    rows = parse_rtf_table_rows(table_rtf)
    
    if len(rows) < 2:
        return None
    
    # Build markdown table
    md_lines = []
    
    if table_label:
        md_lines.append(f'#### {table_label}')
        md_lines.append('')
    
    # Use first row as header
    header_row = rows[0]
    md_lines.append('| ' + ' | '.join(header_row) + ' |')
    md_lines.append('|' + ''.join(['---|' for _ in header_row]))
    
    # Add data rows
    for row in rows[1:]:
        md_lines.append('| ' + ' | '.join(row) + ' |')
    
    return '\n'.join(md_lines) if md_lines else None

def cleanup_tables_in_markdown(markdown_content):
    """Post-process markdown to identify and format table data properly BEFORE heading processing."""
    
    lines = markdown_content.split('\n')
    result = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Look for "table:" labels (case-insensitive) - they appear on lines with all the table data crammed in
        if 'table:' in line.lower():
            # Extract table name using position-based method (case-insensitive)
            table_start = line.lower().find('table:')
            d_pos = line.find(' d ', table_start + 6)  # Find first " d " after "Table:"
            
            if d_pos > 0:
                table_name = line[table_start+6:d_pos].strip()
            else:
                table_name = 'Table'
            
            # Get everything after the first " d "
            if d_pos > 0:
                remainder = line[d_pos+3:]
            else:
                remainder = line

            # Collect table data - read until we hit actual prose or a heading
            # Table data consists of lines with 'd' separators and capitalized words with numbers
            table_data_lines = [remainder] if remainder.strip() else []
            j = i + 1

            while j < len(lines):
                next_line = lines[j].strip()

                # Stop at headings
                if next_line.startswith('##'):
                    break

                # Check if this line looks like table data or prose
                if next_line:
                    # If it contains ' d ' and capitalized words, it's likely table data
                    # If it's longer prose, stop
                    if ' d ' in next_line or re.search(r'[A-Z]\w+\s+[+-]?\d+', next_line):
                        table_data_lines.append(next_line)
                    elif len(next_line) > 100:
                        # Long lines are likely prose, not table data
                        break
                    elif re.match(r'^[A-Z][a-z]+ [A-Z]', next_line):
                        # This looks like a sentence (Capital word followed by lowercase, then space and capital)
                        if 'attack' in next_line.lower() or 'weapon' in next_line.lower() or 'damage' in next_line.lower():
                            break
                        # Otherwise might be more table data
                        table_data_lines.append(next_line)
                    else:
                        table_data_lines.append(next_line)

                j += 1

            # Only auto-format as a 4-column Size/Size Modifier table
            # if the table name or the collected data suggests it's a size table.
            # Otherwise, attempt a conservative generic parse for two-column tables.
            joined_sample = ' '.join(table_data_lines).lower()
            is_size_table = 'size' in table_name.lower() or 'size' in joined_sample

            # If this looks like the Size Modifiers table, use the 4-column extractor.
            if is_size_table:
                # Parse all collected data - join and split by ' d ' marker
                all_data = ' '.join(table_data_lines)
                rows_raw = re.split(r'\s+d\s+', all_data)

                # Extract pairs
                all_pairs = []
                for row_idx, row_text in enumerate(rows_raw):
                    # Skip header row
                    if 'Size Modifier' in row_text or (row_text.startswith('Size') and len(row_text) < 30):
                        continue

                    # Stop if we hit prose
                    if any(prose in row_text for prose in ['When ', 'Your ', 'attack succeeds', 'deal damage']):
                        break

                    # Find all pairs like "Colossal - 8" or "Small +1"
                    pairs = re.findall(r'([A-Z]\w+)\s*[-–]?\s*([0-9+]+)', row_text)
                    all_pairs.extend(pairs)

                # Format as table rows (4-column layout)
                for idx in range(0, len(all_pairs), 2):
                    if idx + 1 < len(all_pairs):
                        size1, mod1 = all_pairs[idx]
                        size2, mod2 = all_pairs[idx+1]
                        result.append(f'| {size1} | {mod1} | {size2} | {mod2} |')
                    else:
                        size1, mod1 = all_pairs[idx]
                        result.append(f'| {size1} | {mod1} | | |')

                result.append('')
                i = j
                continue

            # Conservative generic parse for two-column 'd'-separated tables
            joined = ' '.join(table_data_lines).strip()
            segs = re.split(r'\s+d\s+', joined)

            parsed_rows = []
            header_text = segs[0].strip() if segs else table_name

            # If we have an explicit table name (not the placeholder 'Table'),
            # treat all segments as rows; otherwise the first segment is a header and skip it.
            iterate_segs = segs if (table_name and table_name.lower() != 'table') else segs[1:]

            for seg in iterate_segs:
                s = seg.strip()
                if not s:
                    continue
                # Avoid parsing large prose blocks: if we've already captured rows, stop; otherwise abort
                if len(s) > 200:
                    if parsed_rows:
                        break
                    parsed_rows = []
                    break

                # Try to capture a left/right pair where the right is a short word (e.g., Faint, Moderate)
                m = re.match(r'(.+?)\s+([A-Za-z]+)$', s)
                if m:
                    left = m.group(1).strip()
                    right = m.group(2).strip()
                    parsed_rows.append((left, right))
                    continue

                # Fallback: try number-range on the left and a word on the right
                m2 = re.match(r'([0-9\-\sor]+)\s+([A-Za-z]+)', s, re.IGNORECASE)
                if m2:
                    left = m2.group(1).strip()
                    right = m2.group(2).strip()
                    parsed_rows.append((left, right))
                    continue

                # If we couldn't parse this segment, stop parsing further segments if we already have rows,
                # otherwise abort generic parsing entirely.
                if parsed_rows:
                    break
                parsed_rows = []
                break

            if len(parsed_rows) >= 2:
                # Build a conservative two-column markdown table
                # Prefer a clean header derived from the table name when available
                header_for_columns = table_name if table_name and table_name.lower() != 'table' else header_text
                parts = header_for_columns.split()
                if len(parts) >= 2:
                    hleft = parts[0].strip()
                    hright = ' '.join(parts[1:]).strip()
                else:
                    hleft = header_for_columns.strip()
                    hright = 'Value'

                result.append(f'#### {table_name if table_name and table_name.lower() != "table" else header_text}')
                result.append('')
                result.append(f'| {hleft} | {hright} |')
                result.append('|---|---|')
                for left, right in parsed_rows:
                    result.append(f'| {left} | {right} |')
                result.append('')
                i = j
                continue
            else:
                # Could not parse as a table; keep the original reference
                result.append(line)
                i += 1
                continue
        
        result.append(line)
        i += 1
    
    return '\n'.join(result)

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
    
    # EXTRACT TABLE DATA BEFORE REMOVING CODES
    # Find tables marked by "Table: " labels
    table_lines = []
    table_pattern = r'Table:\s*([^\n]+)'
    for match in re.finditer(table_pattern, text):
        table_lines.append(match.group(1).strip())
    
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
    
    # Remove braces carefully - track depth to preserve content
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
    
    # Remove standalone 'd' characters that appear from RTF markers
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

def add_markdown_headings(text):
    """Convert all-caps sequences embedded in text to markdown headings with line breaks."""
    
    # First, remove RTF header lines at the beginning
    lines = text.split('\n')
    in_rtf_header = True
    filtered_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # Skip initial RTF header lines (font names, style info, etc.)
        if in_rtf_header:
            if stripped and not any(marker in stripped for marker in [
                'Times New Roman', 'Courier New', 'Arial', 'heading',
                'Body Text', 'Normal', 'Preformatted', ';', ')', '@'
            ]):
                in_rtf_header = False
            else:
                continue
        
        filtered_lines.append(line)
    
    text = '\n'.join(filtered_lines)
    
    # Now process for embedded headings - work with full text to handle line continuations
    abbreviations = {'AC', 'DC', 'XP', 'HP', 'SP', 'GP', 'CP', 'PP', 'NPC', 'PC', 'CR', 'HD', 'BAB', 'SD', 'TP', 'PS', 'AD', 'FT', 'AT', 'SA'}
    
    # Find all-caps sequences that are 2+ letter groups and followed by any word character
    # Pattern: \b([A-Z]{2,}(?:\s+[A-Z]{2,})*)\s+(\w)
    # - \b: word boundary
    # - ([A-Z]{2,}(?:\s+[A-Z]{2,})*): capture group 1 - all-caps words (2+ letters each)
    # - \s+: one or more spaces
    # - (\w): capture group 2 - any word character (start of next word)
    
    def replace_heading(match):
        heading_text = match.group(1).strip()
        following_char = match.group(2)
        words = heading_text.split()
        
        # Only convert to heading if:
        # - Length > 4 characters
        # - Not all words are in abbreviation list
        # - Has at least 2 words or 1 word longer than 3 chars
        if (len(heading_text) > 4 and 
            not all(w in abbreviations for w in words) and
            (len(words) >= 2 or len(words[0]) > 3)):
            
            # Return with newline separation
            return f'\n## {heading_text}\n{following_char}'
        else:
            # Not a heading, return original
            return match.group(0)
    
    # Apply the replacement
    result = re.sub(
        r'\b([A-Z]{2,}(?:\s+[A-Z]{2,})*)\s+(\w)',
        replace_heading,
        text
    )
    
    # Clean up the newlines created by the replacement
    # Remove extra blank lines but preserve paragraph breaks
    result = re.sub(r'\n\n\n+', '\n\n', result)
    
    # Clean up any leading/trailing newlines
    result = result.strip()
    
    return result

def convert_rtf_files():
    """Convert all RTF files in original/ to markdown in markdown/."""
    
    source_dir = Path('d:/git/srd/original')
    target_dir = Path('d:/git/srd/markdown')
    target_dir.mkdir(exist_ok=True)
    
    rtf_files = sorted(source_dir.glob('*.rtf'))
    print(f"Found {len(rtf_files)} RTF files to convert")
    
    for i, rtf_file in enumerate(rtf_files, 1):
        try:
            # Read RTF file
            with open(rtf_file, 'r', encoding='utf-8', errors='ignore') as f:
                rtf_content = f.read()
            
            # Convert to plain text
            markdown_content = simple_rtf_to_text(rtf_content)
            
            # CLEAN UP TABLES FIRST, before heading processing
            # This prevents headings from destroying table data
            markdown_content = cleanup_tables_in_markdown(markdown_content)
            
            # Add markdown headings and remove RTF header
            markdown_content = add_markdown_headings(markdown_content)
            
            # Write markdown file
            md_file = target_dir / rtf_file.with_suffix('.md').name
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # Show progress
            file_size = len(markdown_content)
            print(f"[{i:2d}/{len(rtf_files)}] {rtf_file.name:40s} [OK] ({file_size} bytes)")
            
        except Exception as e:
            error_msg = str(e)[:40]
            print(f"[{i:2d}/{len(rtf_files)}] {rtf_file.name:40s} [ERROR: {error_msg}]")
    
    print(f"\nConversion complete!")
    print(f"Files saved to: {target_dir}")

if __name__ == '__main__':
    convert_rtf_files()

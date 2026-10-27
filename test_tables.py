#!/usr/bin/env python3
import re

# Read the RTF file
with open('d:/git/srd/original/CombatI.rtf', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Find 'Table: Size Modifiers' and get the table data
idx = content.find('Table: Size Modifiers')
print(f"Found 'Table: Size Modifiers' at position {idx}")

# Find the next \trowd after this
next_trowd = content.find('\\trowd', idx)
print(f"Next \\trowd at position {next_trowd}")

# Find ALL \row markers after this trowd within reasonable distance
rows = []
search_pos = next_trowd
row_starts = []
while True:
    row_pos = content.find('\\row', search_pos)
    if row_pos < 0 or row_pos > next_trowd + 3000:  # Limit search
        break
    row_starts.append(row_pos)
    search_pos = row_pos + 4

print(f'Found table with {len(row_starts)} rows\n')

# Extract each row's content
for row_idx, row_pos in enumerate(row_starts[:7]):  # First 7 rows
    if row_idx == 0:
        start = next_trowd
    else:
        start = row_starts[row_idx-1]
    
    row_section = content[start:row_pos+100]
    
    # Find all \cell markers which separate columns
    cells = []
    cell_pattern = r'([^}]*?)\\cell'
    for match in re.finditer(cell_pattern, row_section):
        cell = match.group(1)
        # Clean it up
        cell = re.sub(r'\\[a-z]+[\d\s]*', ' ', cell)
        cell = re.sub(r'[{}]', '', cell)
        cell = ' '.join(cell.split()).strip()
        if cell and len(cell) > 1:
            cells.append(cell)
    
    print(f'Row {row_idx}: {cells}')

#!/usr/bin/env python3
import re

# Simulate what cleanup receives
test_lines = [
    'Table: Size Modifiers d Size Size Modifier Size Size Modifier d Colossal - 8 Small',
    '',
    '+1 d Gargantuan',
    '',
    '- 4 Tiny +2 d Huge - 2 Diminutive +4 d Large - 1 Fine +8 d Medium +0 d DAMAGE When your attack succeeds, you deal damage.'
]

# Simulate the cleanup process
line = test_lines[0]
print("Processing table line:")
print(f"  {repr(line)}")

# Extract table name
table_start = line.find('Table:')
d_pos = line.find(' d ', table_start + 6)

if d_pos > 0:
    table_name = line[table_start+6:d_pos].strip()
    remainder = line[d_pos+3:]
else:
    table_name = 'Table'
    remainder = line

print(f"Table name: {repr(table_name)}")
print(f"Remainder from line 0: {repr(remainder[:80])}")

# Collect data from following lines
table_data_lines = [remainder] if remainder.strip() else []
j = 1
while j < len(test_lines):
    next_line = test_lines[j].strip()
    print(f"  Line {j}: {repr(next_line[:60])}")
    
    if next_line.startswith('##'):
        print(f"    -> Stopping (heading)")
        break
    
    if any(pattern in next_line.lower() for pattern in ['when ', 'your ', 'attack ', 'each ', 'that ', 'this ', 'which ']):
        print(f"    -> Stopping (prose pattern)")
        break
    
    if next_line:
        print(f"    -> Adding to table data")
        table_data_lines.append(next_line)
    else:
        print(f"    -> Skipping (empty)")
    
    j += 1

print(f"\nCollected lines: {table_data_lines}")

# Join and split
all_data = ' '.join(table_data_lines)
print(f"\nJoined data: {repr(all_data[:150])}")

rows_raw = re.split(r'\s+d\s+', all_data)
print(f"\nAfter split by 'd': {rows_raw}")

# Extract pairs
all_pairs = []
for row_idx, row_text in enumerate(rows_raw):
    print(f"\n  Row {row_idx}: {repr(row_text[:80])}")
    if 'Size Modifier' in row_text or row_text.startswith('Size'):
        print(f"    -> Skipping (header)")
        continue
    
    pairs = re.findall(r'([A-Z]\w+)\s*[-–]?\s*([0-9+]+)', row_text)
    print(f"    -> Pairs: {pairs}")
    all_pairs.extend(pairs)

print(f"\nAll pairs: {all_pairs}")
print(f"\nFormatted table:")
for idx in range(0, len(all_pairs), 2):
    if idx + 1 < len(all_pairs):
        size1, mod1 = all_pairs[idx]
        size2, mod2 = all_pairs[idx+1]
        print(f"| {size1} | {mod1} | {size2} | {mod2} |")
    else:
        size1, mod1 = all_pairs[idx]
        print(f"| {size1} | {mod1} | | |")

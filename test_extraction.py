#!/usr/bin/env python3
import re

# The raw line from RTF conversion
line = 'Table: Size Modifiers d Size Size Modifier Size Size Modifier d Colossal - 8 Small'

# BETTER extraction - look for "Table: " followed by non-d text, then " d "
table_start = line.find('Table:')
d_after_table = line.find(' d ', table_start + 6)  # Find first " d " after "Table:"

if d_after_table > 0:
    table_name = line[table_start+6:d_after_table].strip()
    print(f"Table name: '{table_name}'")
    
    remainder = line[d_after_table+3:]  # Start after " d "
    print(f"Remainder: '{remainder}'")
    
    # Split by ' d '
    rows_raw = re.split(r'\s+d\s+', remainder)
    print(f"Rows after split: {rows_raw}")
    
    # Extract pairs - look for pattern "Word - Number" or "Word Number"
    all_pairs = []
    for row_text in rows_raw:
        print(f"  Processing: '{row_text}'")
        # Look for Word (- or +)? Number
        pairs = re.findall(r'(\w+)\s*[-–]?\s*([0-9]+)', row_text)
        print(f"    Found pairs: {pairs}")
        all_pairs.extend(pairs)
    
    print(f"\nAll pairs: {all_pairs}")

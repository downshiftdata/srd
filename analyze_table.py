#!/usr/bin/env python3
import re

# Read the RTF file
with open('d:/git/srd/original/CombatI.rtf', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Find the "Table: Size Modifiers" section and extract ALL text after it until we hit another "Table:" or major section
idx = content.find('Table: Size Modifiers')
section_start = idx
# Find the next major heading or Table:
next_major = content.find('Table:', idx + 5)
if next_major < 0:
    next_major = content.find('\\par }\\trowd', idx)  # End of table
if next_major < 0:
    next_major = idx + 2000  # Default limit

table_section = content[section_start:next_major]

print("Raw table section:")
print(repr(table_section[:1000]))
print("\n" + "="*80 + "\n")

# Extract just the text, removing all RTF codes
# First, let's identify all actual text strings
text_strings = []
brace_pattern = r'\{([^{}]*?)\}'

pos = 0
while pos < len(table_section):
    # Find next brace pair
    start = table_section.find('{', pos)
    if start < 0:
        break
    end = table_section.find('}', start)
    if end < 0:
        break
    
    content_in_braces = table_section[start+1:end]
    
    # Remove all RTF codes but keep actual text
    text = re.sub(r'\\[a-z]+\d*\s*', '', content_in_braces)
    text = text.strip()
    
    if text and not text.startswith('\\') and len(text) > 1:
        text_strings.append(text)
        print(f"Found: {repr(text)}")
    
    pos = end + 1

print("\n" + "="*80)
print(f"\nTotal text fragments: {len(text_strings)}")
print("\nFiltered (removing short/RTF codes):")
for t in text_strings:
    if len(t) > 2 and 'cellx' not in t and 'trgaph' not in t:
        print(f"  {repr(t)}")

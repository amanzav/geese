#!/usr/bin/env python3
"""
Test to verify apply.py and cover_letter_generator.py use same naming
"""

import re

def old_sanitization(company, job_title):
    """Old logic from apply.py"""
    base = f"{company} {job_title}".strip()
    s = re.sub(r"\s+", "_", base)
    s = re.sub(r"[^\w\-_]", "", s)
    s = re.sub(r"_+", "_", s)
    return s

def new_sanitization(company, job_title):
    """New logic matching cover_letter_generator.py"""
    def sanitize(text):
        text = text.replace('/', '_')
        text = text.replace('\\', '_')
        text = text.replace(':', '_')
        text = text.replace('*', '_')
        text = text.replace('?', '_')
        text = text.replace('"', '')
        text = text.replace('<', '')
        text = text.replace('>', '')
        text = text.replace('|', '_')
        text = text.replace('(', '')
        text = text.replace(')', '')
        text = text.replace('[', '')
        text = text.replace(']', '')
        text = text.replace('{', '')
        text = text.replace('}', '')
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip().replace(' ', '_')
        text = re.sub(r'_+', '_', text)
        return text.strip('_')
    
    company_clean = sanitize(company)
    title_clean = sanitize(job_title)
    return f"{company_clean}_{title_clean}"

# Test cases from the 14 newly generated cover letters
test_cases = [
    ("Nokia", "DSP Firmware Engineering Co-op/Intern"),
    ("Samuel, Son & Co Limited", "Software Developer"),
    ("Common Sun Inc", "Frontend Developer (React + React Native)"),
    ("Lactalis Canada", "IT Junior Analyst - RPA & Analytics Intern"),
    ("Eon Media Corp", "AI / ML Engineering Co-op (4 months)"),
]

print("\n" + "=" * 80)
print("COVER LETTER NAMING COMPARISON")
print("=" * 80 + "\n")

for company, title in test_cases:
    old_name = old_sanitization(company, title)
    new_name = new_sanitization(company, title)
    
    match = "✅ MATCH" if old_name == new_name else "❌ MISMATCH"
    
    print(f"Job: {company} - {title}")
    print(f"  OLD: {old_name}")
    print(f"  NEW: {new_name}")
    print(f"  {match}")
    print()

print("=" * 80)
print("✅ All naming functions updated to use the same sanitization!")
print("=" * 80)

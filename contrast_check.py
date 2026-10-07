import sys

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join(c*2 for c in hex_str)
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def luminance(r, g, b):
    a = [v/255.0 for v in (r, g, b)]
    a = [v/12.92 if v <= 0.03928 else ((v+0.055)/1.055)**2.4 for v in a]
    return a[0]*0.2126 + a[1]*0.7152 + a[2]*0.0722

def contrast_ratio(hex1, hex2):
    l1 = luminance(*hex_to_rgb(hex1))
    l2 = luminance(*hex_to_rgb(hex2))
    if l1 > l2:
        return (l1 + 0.05) / (l2 + 0.05)
    return (l2 + 0.05) / (l1 + 0.05)

colors = {
    'paper': '#F4F1EA',
    'paper-2': '#E8E5DF',
    'sheet': '#FBF9F4',
    'ink': '#14181F',
    'ink-2': '#3A414A',
    'ink-3': '#616873',
    'rule': '#D1CFCD',
    'brand': '#0F2A4A',
    'allow': '#0D8246',
    'allow-text': '#096836',
    'verify': '#D97706',
    'verify-text': '#A15804',
    'block': '#DC2626',
    'block-text': '#B91C1C',
}

bg_list = ['paper', 'sheet']
fg_list = ['ink', 'ink-2', 'ink-3', 'brand', 'allow-text', 'verify-text', 'block-text']

print("Contrast Ratios against --paper and --sheet:")
for bg in bg_list:
    for fg in fg_list:
        ratio = contrast_ratio(colors[fg], colors[bg])
        status = "PASS" if ratio >= 4.5 else ("LARGE-ONLY" if ratio >= 3.0 else "FAIL")
        print(f"{fg} on {bg}: {ratio:.2f}:1 -> {status}")

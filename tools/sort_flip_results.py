from pathlib import Path
import re

def main():
    # Process both the classic and no_majority results files if present
    SOURCES = [
        Path('results/flip_results_1900-2024.txt'),
        Path('no_majority/no_majority_results_1900-2024.txt'),
    ]

    for SRC in SOURCES:
        if not SRC.exists():
            print(f'skipping missing source: {SRC}')
            continue

        text = SRC.read_text(encoding='utf-8')
        # strip possible surrounding code fences
        text = re.sub(r'^\s*```(?:\w+)?\s*\n', '', text)
        text = re.sub(r'\n?\s*```\s*$', '', text)

        # split into sections starting with 'Year: ####'
        sections = re.split(r'(?=^Year:\s*\d{4})', text, flags=re.MULTILINE)
        # drop any leading chunk before first Year:
        if sections and not sections[0].strip().startswith('Year:'):
            sections = sections[1:]

        raw_entries = []   # (raw_count:int, section:str)
        ratio_entries = [] # (ratio:float, section:str) -- ratio is percent value (e.g. 0.53931 means percent)

        for sec in sections:
            m_raw = re.search(r'Total number of flipped votes:\s*([\d,]+)', sec)
            if m_raw:
                raw = int(m_raw.group(1).replace(',', ''))
            else:
                raw = -1

            # look for the 'Ratio to Total Votes in Year: X.XXXXX%'
            m_ratio = re.search(r'Ratio to Total Votes in Year:\s*([\d.]+)%', sec)
            if m_ratio:
                # store the percent numeric (not divided by 100) so it's comparable to the printed value
                ratio = float(m_ratio.group(1))
            else:
                ratio = -1.0

            raw_entries.append((raw, sec))
            ratio_entries.append((ratio, sec))

        # sort descending (largest first) — raw by count, ratio by percent value
        raw_entries.sort(key=lambda x: x[0], reverse=False)
        ratio_entries.sort(key=lambda x: x[0], reverse=False)

        base_name = SRC.name
        dst_raw = SRC.parent / f'sorted_raw_{base_name}'
        dst_ratio = SRC.parent / f'sorted_ratio_{base_name}'

        out_raw = '\n\n'.join([sec.rstrip() for num, sec in raw_entries]) + '\n'
        out_ratio = '\n\n'.join([sec.rstrip() for num, sec in ratio_entries]) + '\n'

        dst_raw.write_text(out_raw, encoding='utf-8')
        dst_ratio.write_text(out_ratio, encoding='utf-8')
        print(f'Wrote {dst_raw} and {dst_ratio} with {len(sections)} sections')

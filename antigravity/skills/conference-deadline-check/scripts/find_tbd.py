#!/usr/bin/env python3
import argparse
import os
import sys
import yaml
from datetime import datetime, date, time

def parse_date(date_val):
    if not date_val:
        return None
    if isinstance(date_val, datetime):
        return date_val
    if isinstance(date_val, date):
        return datetime.combine(date_val, time.min)
    s = str(date_val).strip()
    if s.upper() == 'TBD':
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None

def main():
    parser = argparse.ArgumentParser(
        description="Find conferences with TBD deadlines or dates that happen strictly in the future."
    )
    parser.add_argument("path", help="Path to the workspace root or conferences data directory.")
    parser.add_argument(
        "--reference-date",
        type=str,
        default=None,
        help="Reference date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS), default: current time."
    )
    parser.add_argument(
        "--include-venue",
        action="store_true",
        help="Include conferences where only the venue is TBD (default: False)."
    )
    args = parser.parse_args()

    target_path = os.path.abspath(args.path)

    if not os.path.exists(target_path):
        print(f"Error: Specified path '{target_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    # Determine conferences directory
    if target_path.endswith('conferences') and os.path.basename(target_path) == 'conferences':
        conf_dir = target_path
    else:
        conf_dir = os.path.join(target_path, 'src/data/conferences')

    if not os.path.exists(conf_dir):
        print(f"Error: Conferences directory not found at '{conf_dir}'.", file=sys.stderr)
        sys.exit(1)

    if args.reference_date:
        try:
            s = args.reference_date.strip()
            if len(s) == 10:
                ref_dt = datetime.strptime(s, "%Y-%m-%d")
            else:
                ref_dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            print(f"Error parsing reference date: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        ref_dt = datetime.now()

    tbd_files = []

    for filename in sorted(os.listdir(conf_dir)):
        if not filename.endswith('.yml'):
            continue
        filepath = os.path.join(conf_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            if not data or not isinstance(data, list):
                continue

            for conf in data:
                conf_year = int(conf.get('year', 0))

                # 1. Conference must happen strictly in the future:
                # Conference date is NOT passed nor currently appearing/ongoing.
                start_dt = parse_date(conf.get('start'))
                end_dt = parse_date(conf.get('end'))

                if start_dt:
                    # If start_dt <= ref_dt, the conference is either currently appearing
                    # (start_dt <= ref_dt <= end_dt) or already passed (end_dt < ref_dt or start_dt < ref_dt).
                    if start_dt.date() <= ref_dt.date():
                        continue
                else:
                    # Conference start date is TBD or unstated.
                    # Exclude past years; conference must be in a future or current year.
                    if conf_year < ref_dt.year:
                        continue
                    if end_dt and end_dt.date() < ref_dt.date():
                        continue

                # 2. Check for TBD in ALL deadlines inside `deadlines` (submission, abstract,
                # notification/final_decision, rebuttal, review_release, etc.) or TBD conference dates
                missing = []
                if str(conf.get('date', '')).strip().upper() == 'TBD' or \
                   str(conf.get('start', '')).strip().upper() == 'TBD' or \
                   str(conf.get('end', '')).strip().upper() == 'TBD':
                    missing.append('date')

                deadlines = conf.get('deadlines', [])
                tbd_types = []
                if deadlines:
                    for d in deadlines:
                        dtype = str(d.get('type', '')).strip().lower() or 'deadline'
                        d_date = str(d.get('date', '')).strip().upper()
                        if d_date == 'TBD':
                            if dtype not in tbd_types:
                                tbd_types.append(dtype)
                elif str(conf.get('deadline', '')).strip().upper() == 'TBD':
                    tbd_types.append('submission')

                if tbd_types:
                    missing.extend(tbd_types)

                # Handle venue: only trigger if --include-venue, or annotate if already missing date/deadlines
                is_venue_tbd = str(conf.get('venue', '')).strip().upper() == 'TBD'
                if args.include_venue and is_venue_tbd:
                    if 'venue' not in missing:
                        missing.append('venue')
                elif missing and is_venue_tbd:
                    missing.append('venue')

                if missing:
                    tbd_files.append(f"{filename} | {conf_year} | {','.join(missing)} | {conf.get('link')}")
                    break
        except Exception:
            pass

    for f in sorted(list(set(tbd_files))):
        print(f)

if __name__ == '__main__':
    main()

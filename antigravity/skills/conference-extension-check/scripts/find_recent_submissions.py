#!/usr/bin/env python3
import argparse
import os
import sys
import yaml
from datetime import datetime, date, time, timedelta

def parse_deadline_date(date_val):
    if not date_val:
        return None
    s = str(date_val).strip()
    if s.upper() == 'TBD':
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None

def parse_event_date(date_val):
    if not date_val:
        return None
    if isinstance(date_val, datetime):
        return date_val
    if isinstance(date_val, date):
        return datetime.combine(date_val, time.max)
    s = str(date_val).strip()
    if s.upper() == 'TBD':
        return None
    if len(s) == 10:
        try:
            return datetime.strptime(s + " 23:59:59", "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

def is_ignored_label(label):
    l = label.lower()
    ignored_keywords = [
        'camera-ready', 'camera ready', 'cameraready',
        'registration', 'early bird',
        'workshop', 'tutorial', 'symposium', 'doctoral',
        'poster', 'demo', 'challenge', 'competition',
        'rebuttal', 'notification', 'decision', 'review',
        'revision'
    ]
    return any(k in l for k in ignored_keywords)

def main():
    parser = argparse.ArgumentParser(
        description="Find conferences with recently passed or upcoming near-date paper/abstract submission deadlines to check for extensions."
    )
    parser.add_argument("path", help="Path to workspace root or conferences data directory.")
    parser.add_argument("--days-past", type=int, default=14, help="Days to look back into the past (default: 14).")
    parser.add_argument("--days-future", type=int, default=14, help="Days to look forward into the future (default: 14).")
    parser.add_argument("--reference-date", type=str, default=None, help="Reference date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS), default: current time.")
    args = parser.parse_args()

    target_path = os.path.abspath(args.path)
    if not os.path.exists(target_path):
        print(f"Error: Specified path '{target_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if target_path.endswith('conferences') and os.path.basename(target_path) == 'conferences':
        conf_dir = target_path
    else:
        conf_dir = os.path.join(target_path, 'src/data/conferences')

    if not os.path.exists(conf_dir):
        print(f"Error: Conferences directory not found at '{conf_dir}'.", file=sys.stderr)
        sys.exit(1)

    if args.reference_date:
        try:
            if len(args.reference_date.strip()) == 10:
                ref_dt = datetime.strptime(args.reference_date.strip() + " 23:59:59", "%Y-%m-%d %H:%M:%S")
            else:
                ref_dt = datetime.strptime(args.reference_date.strip(), "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            print(f"Error parsing reference date: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        ref_dt = datetime.now()

    past_limit = ref_dt - timedelta(days=args.days_past)
    future_limit = ref_dt + timedelta(days=args.days_future)

    matches = []

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
                # Only check conferences for the current or upcoming years
                if conf_year < ref_dt.year:
                    continue

                # Ensure conference event has not fully concluded
                conf_end_dt = parse_event_date(conf.get('end')) or parse_event_date(conf.get('start'))
                if conf_end_dt and conf_end_dt < ref_dt:
                    continue

                deadlines = conf.get('deadlines', [])
                if not deadlines:
                    continue

                for d in deadlines:
                    dtype = str(d.get('type', '')).strip().lower()
                    dlabel = str(d.get('label', '')).strip()

                    # Strictly only submission or abstract
                    if dtype not in ('submission', 'abstract'):
                        continue

                    # Filter out non-main-paper deadlines
                    if is_ignored_label(dlabel):
                        continue

                    d_dt = parse_deadline_date(d.get('date'))
                    if not d_dt:
                        continue

                    if past_limit <= d_dt <= future_limit:
                        diff = d_dt - ref_dt
                        diff_days = diff.total_seconds() / 86400.0
                        if diff_days < 0:
                            status = "recently_passed"
                            diff_str = f"{diff_days:.1f}d"
                        else:
                            status = "near_date"
                            diff_str = f"+{diff_days:.1f}d"

                        link = conf.get('link', '')
                        matches.append({
                            'filename': filename,
                            'year': conf_year,
                            'type': dtype,
                            'status': status,
                            'deadline_date': str(d.get('date')),
                            'diff_str': diff_str,
                            'label': dlabel,
                            'link': link
                        })
        except Exception:
            pass

    # Print matching candidates
    # Format: filename | year | type | status | deadline_date | diff_str | label | link
    # Group by filename + year
    seen = set()
    for m in sorted(matches, key=lambda x: (x['filename'], x['deadline_date'])):
        key = (m['filename'], m['year'], m['type'], m['deadline_date'], m['label'])
        if key in seen:
            continue
        seen.add(key)
        print(f"{m['filename']} | {m['year']} | {m['type']} | {m['status']} | {m['deadline_date']} | {m['diff_str']} | {m['label']} | {m['link']}")

if __name__ == '__main__':
    main()

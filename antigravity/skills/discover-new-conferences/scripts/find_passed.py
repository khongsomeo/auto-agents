#!/usr/bin/env python3
import argparse
import os
import sys
import yaml
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="Find conferences where all deadlines have passed.")
    parser.add_argument("path", help="Path to the workspace root or conferences data directory.")
    args = parser.parse_args()

    target_path = os.path.abspath(args.path)

    if not os.path.exists(target_path):
        print(f"Error: Specified path '{target_path}' does not exist.")
        sys.exit(1)

    # Determine conferences directory
    if target_path.endswith('conferences') and os.path.basename(target_path) == 'conferences':
        conf_dir = target_path
    else:
        conf_dir = os.path.join(target_path, 'src/data/conferences')

    if not os.path.exists(conf_dir):
        print(f"Error: Conferences directory not found at '{conf_dir}'.")
        sys.exit(1)

    passed_files = []
    now = datetime.utcnow()

    for filename in sorted(os.listdir(conf_dir)):
        if filename.endswith('.yml'):
            path = os.path.join(conf_dir, filename)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if not data or not isinstance(data, list):
                        continue
                    
                    # Find the edition with the highest year
                    latest_conf = max(data, key=lambda c: int(c.get('year', 0)))
                    
                    has_future_or_tbd = False
                    has_valid_deadline = False
                    
                    deadlines = latest_conf.get('deadlines', [])
                    for d in deadlines:
                        date_str = str(d.get('date')).strip()
                        if date_str.upper() == 'TBD':
                            has_future_or_tbd = True
                            break
                        
                        try:
                            # Date format: YYYY-MM-DD HH:MM:SS
                            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                            if dt > now:
                                has_future_or_tbd = True
                                break
                            has_valid_deadline = True
                        except ValueError:
                            # If date parsing fails, ignore or treat as not passed
                            has_future_or_tbd = True
                            break
                    
                    # If all deadlines are valid dates in the past, and we found at least one deadline
                    if not has_future_or_tbd and has_valid_deadline:
                        passed_files.append(filename)
            except Exception:
                pass

    for f in sorted(list(set(passed_files))):
        print(f)

if __name__ == '__main__':
    main()

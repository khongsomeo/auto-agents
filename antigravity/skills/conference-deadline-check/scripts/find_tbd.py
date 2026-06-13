#!/usr/bin/env python3
import argparse
import os
import sys
import yaml

def main():
    parser = argparse.ArgumentParser(description="Find conferences with TBD deadlines or dates.")
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

    tbd_files = []

    for filename in sorted(os.listdir(conf_dir)):
        if filename.endswith('.yml'):
            path = os.path.join(conf_dir, filename)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if not data or not isinstance(data, list):
                        continue
                    for conf in data:
                        has_tbd = False
                        if str(conf.get('date')).strip().upper() == 'TBD' or \
                           str(conf.get('start')).strip().upper() == 'TBD' or \
                           str(conf.get('end')).strip().upper() == 'TBD':
                            has_tbd = True
                        else:
                            deadlines = conf.get('deadlines', [])
                            for d in deadlines:
                                if d.get('type') == 'submission' and str(d.get('date')).strip().upper() == 'TBD':
                                    has_tbd = True
                                    break
                        if has_tbd:
                            tbd_files.append(filename)
                            break
            except Exception:
                pass

    for f in sorted(list(set(tbd_files))):
        print(f)

if __name__ == '__main__':
    main()

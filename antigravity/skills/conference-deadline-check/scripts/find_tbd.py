#!/usr/bin/env python3
import os
import yaml

def main():
    # Resolve path relative to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # .agent/skills/conference-deadline-check/scripts -> 4 levels up to workspace root
    workspace_root = os.path.abspath(os.path.join(script_dir, '../../../../'))
    conf_dir = os.path.join(workspace_root, 'src/data/conferences')
    tbd_files = []

    if not os.path.exists(conf_dir):
        # Fallback to current working directory
        workspace_root = os.getcwd()
        conf_dir = os.path.join(workspace_root, 'src/data/conferences')

    if not os.path.exists(conf_dir):
        print(f"Error: conferences directory not found at {conf_dir}")
        return

    for filename in sorted(os.listdir(conf_dir)):
        if filename.endswith('.yml'):
            path = os.path.join(conf_dir, filename)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if not data or not isinstance(data, list):
                        continue
                    for conf in data:
                        deadlines = conf.get('deadlines', [])
                        for d in deadlines:
                            if d.get('type') == 'submission' and str(d.get('date')).strip().upper() == 'TBD':
                                tbd_files.append(filename)
                                break
            except Exception:
                pass

    for f in sorted(list(set(tbd_files))):
        print(f)

if __name__ == '__main__':
    main()

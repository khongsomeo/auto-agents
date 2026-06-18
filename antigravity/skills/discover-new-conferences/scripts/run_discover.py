import yaml
import json
import os
import requests
import re
import time

def main():
    with os.popen('python3 .agent/skills/discover-new-conferences/scripts/find_passed.py /home/tlxuong/Documents/ai-deadlines/src/data/conferences') as f:
        files = f.read().splitlines()

    explore_path = '.agent/skills/find-conference-dates/resources/explore.json'
    try:
        with open(explore_path, 'r') as f:
            explore_data = json.load(f)
    except Exception:
        explore_data = {}

    count = 0

    for filename in files:
        yml_path = os.path.join('/home/tlxuong/Documents/ai-deadlines/src/data/conferences', filename)
        try:
            with open(yml_path, 'r') as f:
                data = yaml.safe_load(f)
                latest = max(data, key=lambda c: int(c.get('year', 0)))
                link = latest.get('link', '')
            short_name = latest.get('title', '')
            year = latest.get('year', '')
            rankings = latest.get('rankings', {})
            rank_url = rankings.get('rank_source_url', '')

            if not link or not year:
                continue

            # Predict next year
            next_year = str(int(year) + 1)
            predicted_link = link.replace(str(year), next_year)
            
            # Also try replacing 2-digit year
            short_year = str(year)[-2:]
            short_next = next_year[-2:]
            if predicted_link == link and short_year in link:
                predicted_link = link.replace(short_year, short_next)

            if predicted_link == link:
                continue # No year in URL to replace

            print(f"Checking {predicted_link} for {short_name}...")
            try:
                res = requests.get(predicted_link, timeout=5)
                if res.status_code == 200:
                    # Found it!
                    if short_name not in explore_data:
                        explore_data[short_name] = {
                            "conference_url": predicted_link,
                            "conference_rank_url": rank_url
                        }
                        count += 1
                        print(f"  -> Added {short_name}")
            except Exception:
                pass
                
        except Exception as e:
            print(f"Error on {filename}: {e}")
            
    with open(explore_path, 'w') as f:
        json.dump(explore_data, f, indent=2)
        
    print(f"Finished. Added {count} new conferences to explore.json.")

if __name__ == '__main__':
    main()

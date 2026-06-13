---
name: conference-deadline-check
description: Checks for updates on conferences that currently have TBD paper submission deadlines or TBD conference dates. It reads the existing yml files to extract the link, and sequentially scrapes each conference website to find updated dates.
---

# Skill: Conference Deadline Check (TBD Updates)

## Overview

This skill checks for updates to conferences in the database that currently have a `TBD` paper submission deadline or `TBD` conference dates. It automates identifying which conferences need updates, extracting their website links from their current YAML configurations, scraping their official websites for newly announced deadlines/dates, and updating the database.

---

## 🚨 Absolute Rules — No Exceptions, Ever

These are hard constraints. They match the guidelines from the `find-conference-dates` skill:

1. **RULE 1 — BROWSER BUDGET: EXACTLY 1 PER CONFERENCE.**
   For each conference checked, you are allowed exactly **one** browser session. That session must visit the homepage and relevant subpages (Important Dates, CFP, etc.) to collect dates and close. Do not open multiple browser sessions.
2. **RULE 2 — ZERO EXTERNAL URLS.**
   Only navigate to the official conference link found inside its YAML configuration. Do NOT visit Google, search engines, or third-party conference calendars/aggregators.
3. **RULE 3 — NO VERIFICATION BROWSING.**
   Once the browser session for a conference has ended, do not open another browser session for that conference to double-check.
4. **RULE 4 — ONLY MAIN PAPERS; NO WORKSHOPS, CAMERA-READY OR REGISTRATION.**
   Only track main track paper deadlines (abstract, paper submission, rebuttal, notification). Skip camera-ready, final version, and registration deadlines entirely.
5. **RULE 5 — DO NOT TRY TO REBUILD THE SITE.**
   Do **NEVER** run commands like `npm run build` or `npm run dev` to test or check your changes. Strictly limit actions to updating YAML files.
6. **RULE 6 — DO NOT CREATE NEW TAGS.**
   Do not add custom tags; only use tags defined in `available_tags.json`.
7. **RULE 7 — STRICT SEQUENTIAL EXECUTION.**
   If multiple conferences are identified as TBD, process them **one at a time, in order, with no parallelism**. You must fully check and process **all** of the returned conferences in a single continuous run, without interrupting the flow to ask the user for confirmation or check-ins. Only present the summary report once all items are fully processed.

---

## Step-by-Step Workflow

### Step 1: Identify Conferences with TBD Deadlines
Run the helper script inside the skill's scripts directory using Python, passing the path to the workspace root or the `conferences` data directory as a required argument:
```bash
python3 .agent/skills/conference-deadline-check/scripts/find_tbd.py <path_to_workspace_or_conf_dir>
```

### Step 2: Read Existing Configurations
For each file returned by the script:
1. Open and inspect the YAML file in `src/data/conferences/<short_name>.yml`.
2. Extract the canonical `link` (official conference homepage) and current metadata.

### Step 3: Browse and Scrape for Updates (1 Browser Session)
1. Start a single browser session to navigate to the official conference URL.
2. Look for updated dates (Abstract deadline, Submission deadline, Rebuttal phase, Notification date).
3. If new dates are found, record them. If they are still TBD or unannounced, record them as `TBD`.

### Step 4: Update the YAML File
If new deadlines are found:
1. Edit the deadlines block in `src/data/conferences/<short_name>.yml` to replace the `TBD` values with the exact dates in `YYYY-MM-DD HH:MM:SS` format.
2. Ensure you specify the timezone (e.g. `UTC-12` or `AoE`) for both the top-level and each individual deadline entry.
3. Keep the existing structure, rankings, and tags unchanged unless there is a clear change documented on the new homepage.

### Step 5: Report Results
After checking all conferences, output a brief structured summary report to the user listing:
1. **Updated Conferences:** A list of conferences where deadlines were successfully updated from TBD to specific dates, showing the new submission and notification deadlines.
2. **Unchanged/Still TBD Conferences:** A list of conferences that were checked but whose deadlines remain unannounced or TBD.

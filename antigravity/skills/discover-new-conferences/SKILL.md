---
name: discover-new-conferences
description: Discovers websites for next year's conferences by predicting URLs based on past conferences. If found, it updates explore.json so that another agent can retrieve the deadlines later.
---

# Skill: Discover New Conferences

## Overview

This skill proactively finds upcoming conferences for the next year that are not yet tracked. It scans `src/data/conferences` for conferences that have already passed their deadlines, predicts the URL for the next year's conference, and verifies if the site is live.

If the new website is live, this skill **only** updates `.agent/skills/find-conference-dates/resources/explore.json` with the new URL and the CORE ranking URL. 
**CRITICAL:** This skill creates data for another agent to process. **Do NOT dip your nose in to retrieve deadline information or parse the new website's dates.** Doing so will waste tokens and result in immediate termination.

---

## 🚨 Absolute Rules — No Exceptions, Ever

These rules are strict constraints to ensure token efficiency.

1. **RULE 1 — NO DATA EXTRACTION, NO YAML UPDATES, NO GIT COMMITS.**
   Your ONLY job is to find if the website is live and add the URL to `explore.json`. **DO NOT** extract deadlines, dates, or tags, and **DO NOT** update or write to any conference `.yml` files in `src/data/conferences/`. **DO NOT** run any `git` commands (commit, push, add, etc.) and **DO NOT** use the GitHub MCP tool for any purpose whatsoever — committing, pushing, creating PRs, or anything else. Unless the user explicitly asks you to do something Git-related, you must not perform, suggest, recommend, or mention any Git or GitHub action. Updating YAML files and committing to GitHub is the job of a completely different agent and is **STRICTLY FORBIDDEN** here.
2. **RULE 2 — EXPLORE.JSON IS FOR WRITING ONLY.**
   You must only **write/append** new discovered conferences to `.agent/skills/find-conference-dates/resources/explore.json`. You must **NOT** read from it to look for input conferences to process.
3. **RULE 3 — RESEARCH AGENT BUDGET: STRICTLY LIMITED.**
   When checking if a predicted website is live, limit your research to simply loading the homepage to confirm it's the correct conference for the new year. Do not spawn extensive research subagents to read multiple pages.
4. **RULE 4 — ZERO EXTERNAL SEARCH ENGINES.**
   You may only guess/predict the next year's URL (e.g., changing `2026` to `2027` in the URL) or find announcements on the current year's website. **DO NOT** use Google, Bing, DBLP, or any search engines to find the new website.
5. **RULE 5 — NO PARALLELISM.**
   Process conferences one at a time, in order. Do not batch or pipeline steps across multiple conferences simultaneously.
6. **RULE 6 — STRICTLY PASSED DEADLINES ONLY.**
   Do not process conferences that still have ongoing deadlines. Only focus on conferences where all deadlines have passed.

---

## Step-by-Step Workflow

### Step 1: Scan for Passed Conferences
Run the helper script inside the skill's scripts directory using Python, passing the path to the workspace root or the `conferences` data directory as a required argument:
```bash
python3 .agent/skills/discover-new-conferences/scripts/find_passed.py <path_to_workspace_or_conf_dir>
```
The script will output a list of conference YAML files where all submission and notification deadlines have already passed. Process these returned files in the next step.

### Step 2: Predict and Verify the Next Year's Website
For each passed conference:
1. Look at the `link` provided in the YAML for the most recent edition.
2. Predict the next year's URL. For example, if the current URL is `https://2026.aclweb.org`, try `https://2027.aclweb.org`. If the URL is `https://iwcmc.net/2026/`, try `https://iwcmc.net/2027/`.
3. You may also check the current year's homepage for a link or announcement about the next edition.
4. Briefly check if the predicted URL is live and actually represents the next year's conference (not a 404 page or parked domain).

#### ⚠️ Redirect Detection — Mandatory Check
Many conference websites silently redirect unknown or future-year URLs back to the default landing page (e.g., `https://iwcmc.net/2027/` → `https://iwcmc.net/`). This must **NOT** be mistaken for a live next-year conference site.

After loading the predicted URL, perform all of the following checks. If **any** check fails, treat the predicted site as **not found** and move on:

- **Final URL check**: Compare the URL that was actually loaded (after all redirects) with the predicted URL. If the browser/tool was redirected to a different URL (especially the root domain or the current-year page), the new site is **NOT live**. Do **not** add it to `explore.json`.
- **Year mention check**: Confirm that the page content explicitly mentions the target year (e.g., "2027") in a way consistent with it being the next edition's official page (e.g., in the title, header, or call-for-papers text). A page that only mentions the current or past year is a redirect artifact, not the new site.
- **Content sanity check**: Confirm the page is actually a conference page (has a title, dates, or call-for-papers content). A generic domain landing page or parking page does not count.

### Step 3: Update `explore.json`
If the new website is live and confirmed (all redirect checks passed):
1. Get the `conference_rank_url` from the past conference's YAML file (typically the `rank_source_url` under `rankings`).
2. Add a new entry to `.agent/skills/find-conference-dates/resources/explore.json` using the conference's short name as the key.
3. Example format to append:
   ```json
   "SHORT_NAME": {
       "conference_url": "<new_verified_url>",
       "conference_rank_url": "<core_ranking_url_from_yaml>"
   }
   ```
4. Do **not** process the dates. Immediately move on to the next conference.

### Step 4: Report Results
Once all relevant files in `src/data/conferences` have been checked, stop execution and report a brief summary of how many new conferences were added to `explore.json` to the user.

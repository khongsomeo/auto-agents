---
name: find-conference-dates
description: Automatically discovers a conference's deadline information from its website and creates a properly-formatted YAML track file inside `src/data/conferences`. Use this skill when the user provides a conference website URL, its short name, and a CORE edu ranking link.
---

# Skill: Find Conference Dates & Create Deadline Track

## Overview

This skill automates adding a new conference to the `ai-deadlines` tracker. Given a conference website, short name, and CORE ranking link, you will:

1. Scrape the conference website for all important dates and metadata.
2. Look up the conference's latest CORE ranking.
3. Map the conference topics to the project's standardized tag taxonomy.
4. Write a properly-formatted YAML file into `src/data/conferences/`.

---

## Inputs

The user can either provide the details directly, or the skill can read them from [explore.json](file:///.agent/skills/find-conference-dates/resources/explore.json) located in the skill's `resources` directory.

### Direct Input
The user must provide all three of the following:

| Input | Description | Example |
|---|---|---|
| `conference_url` | Official conference website | `https://2027.emnlp.org` |
| `short_name` | Abbreviated name (used as file/id base) | `EMNLP` |
| `core_ranking_url` | Direct CORE portal link for this conference | `https://portal.core.edu.au/conf-ranks/1232/` |

### JSON Input (explore.json)
Alternatively, check `.agent/skills/find-conference-dates/resources/explore.json`. The file lists one or more conferences as key-value pairs:
```json
{
    "SHORT_NAME": {
        "conference_url": "...",
        "conference_rank_url": "..."
    }
}
```
If this file is present and has conferences to import, the skill will read it and sequentially process each entry.

---

## 🚨 Absolute Rules — No Exceptions, Ever

These are hard constraints. They apply to **every single conference**, whether you are processing one or twenty. There is no situation, edge case, or "just this once" that overrides them.

**RULE 1 — RESEARCH AGENT BUDGET: EXACTLY 1 PER CONFERENCE.**
For each conference, you are allowed exactly **one** `research` subagent call (or text-only retrieval tool execution). That single session MUST visit both the `conference_url` and the `core_ranking_url` before returning. After it returns, the research session is closed and you write the YAML. You do NOT perform another lookup to double-check, verify, fill gaps, or look for anything else. If data is missing, write `TBD` and move on.

**RULE 2 — ZERO EXTERNAL URLS.**
You may ONLY navigate to the exact URLs provided by the user. You MUST NOT visit Google, Bing, Wikipedia, DBLP, Semantic Scholar, any search engine, any conference aggregator, or any URL not explicitly given. If you find yourself tempted to "just quickly check" somewhere else — do not. Write `TBD` and report it.

**RULE 3 — NO VERIFICATION RESEARCH AFTER THE FACT.**
Once the research session for a conference has ended, you MUST NOT perform any additional lookups or open any web resources for that conference for any reason. Not to confirm a date. Not to check a venue. Not to validate a ranking. The data you got is the data you use.

**RULE 4 — FORMAT IS `in-person` OR `hybrid` ONLY.**
The value `virtual` does not exist in this project. Do not use it even if the website says the event is fully online.

**RULE 5 — ONLY MAIN PAPERS; NO WORKSHOPS, CAMERA-READY OR REGISTRATION.**
ONLY include deadlines for full papers or short papers (research, applied, or industry). Do NOT include workshops, challenges, tutorials, symposiums, or doctoral consortiums unless explicitly asked to. Skip camera-ready, final-version, author registration, and early/late registration dates entirely. They must not appear in the YAML.

**RULE 6 — DO NOT CREATE NEW TAGS.**
You MUST NOT create any new tags under any circumstances. You must ONLY assign tags from the exact list provided in `available_tags.json` (listed in Step 4). If a topic does not match any existing tag, simply omit it.

**RULE 7 — DO NOT TRY TO REBUILD THE SITE.**
Your task is strictly limited to updating YAML data files. You must **NEVER** run commands to build, build-check, or compile the site (e.g. `npm run build`, `npm run dev`, or checks/linters) to test your changes. This is a strict project rule to conserve execution tokens.

**RULE 8 — AUTOMATIC TERMINATION ON EMPTY INPUT.**
If using `explore.json` as the input source and it is empty, contains no conferences, or does not exist, you must immediately terminate the skill execution without performing any URL requests, research subagent calls, file checks, or updates. Only proceed with execution if there is valid content to process.

---

## Processing Multiple Conferences (Batch Input)

When the user provides a **list** of conferences, you MUST process them **one at a time, in order, with no parallelism**.

**Strictly sequential means:**
- Do NOT run research sessions for multiple conferences at the same time.
- Do NOT collect data for conference N+1 before conference N is fully written and reported.
- Do NOT batch or pipeline any steps across conferences.

**The only allowed execution order:**

```
conference_list = [A, B, C, ...]

STEP 1: Process conference A
  → Open research session (A's conference_url + A's core_ranking_url) → collect data → session CLOSED.
  → Write A's YAML file.
  → Report A's results.
  *** FULLY STOP. A is done. ***

STEP 2: Process conference B  ← only starts after STEP 1 is 100% complete
  → Open research session (B's conference_url + B's core_ranking_url) → collect data → session CLOSED.
  → Write B's YAML file.
  → Report B's results.
  *** FULLY STOP. B is done. ***

... repeat for each remaining conference, one at a time.
```

**The research budget is per-conference and non-transferable.** Each conference gets exactly 1 research session/agent call, consumed the moment it returns. You cannot run research for a later conference while a previous one is still being processed, and you cannot perform another lookup for a conference that has already been processed.

---

## Step-by-Step Instructions

### Step 1 — Single Research Session: Conference Site + CORE Ranking

Launch **one** research subagent with a task that covers both URLs. This is your **entire research budget for this conference** — once it returns, no more URL or retrieval requests.

1. Retrieve `conference_url` content. Look for pages named "Important Dates", "Call for Papers", "Submission", or similar. Collect all data listed below.
2. **In the same research session**, retrieve `core_ranking_url` content and collect the ranking data.
3. Return **all** collected data in a single structured report. Do not stop early.
4. **Do not navigate to or read any other URL.** If a link on the conference site looks useful but was not explicitly given by the user, ignore it.

**Conference site — required fields to extract:**

- **`full_name`**: The complete official name of the conference (e.g., `"The 2027 Conference on Empirical Methods in Natural Language Processing"`).
- **`year`**: The year the conference *takes place* (integer, not the submission year).
- **`link`**: The canonical URL of the conference homepage.
- **`deadlines`**: A list of all important milestone dates (see deadline schema below).
- **`timezone`**: The timezone that applies to submission deadlines (e.g., `UTC-12`, `AoE`, `UTC`). If the site says "AoE" or "Anywhere on Earth", use `UTC-12`. **If the site does not state a timezone at all, default to `UTC-12` (AoE).**
- **`city`** and **`country`**: The conference venue location. **Important:** Conferences held in the USA must format the city as `<city name>, <state short code>` (e.g., `Tempe, AZ`) and the country MUST be `United States`.
- **`venue`**: The venue name/address (if available; use `TBD` if not announced).
- **`format`**: `in-person` or `hybrid` — **no other values are permitted**.
- **`date`**: Human-readable conference date range (e.g., `"November 5-9, 2027"`).
- **`start`** / **`end`**: ISO dates for the first and last conference day (e.g., `2027-11-05` / `2027-11-09`).
- **`note`** *(optional)*: Any special submission notes (e.g., `"OpenReview submission"`).

> **Important**: Be thorough. Navigate to sub-pages (CFP, Important Dates, etc.) if the homepage does not list all dates. **Do not guess or fabricate dates** — only record what is explicitly stated on the website.

---

### Step 2 — Build the Deadlines List

Each deadline entry follows this schema:

```yaml
- type: <deadline_type>
  label: <human-readable label from the website>
  date: "<YYYY-MM-DD HH:MM:SS>"
  timezone: <timezone>
```

**Deadline `type` mapping** — map the website's language to the closest type:

| Website language | `type` to use |
|---|---|
| Abstract deadline / Abstract submission | `abstract` |
| Paper submission / Full paper deadline | `submission` |
| Supplementary / Code / Appendix submission | `submission` |
| Notification / Decision / Accept/reject | `final_decision` |
| Rejection notification / Phase 1 rejection | `final_decision` |
| Rebuttal starts / Author response opens | `rebuttal_start` |
| Rebuttal ends / Author response closes | `rebuttal_end` |
| Major revision deadline | `submission` |

**Deadlines to include — ONLY include these:**
- Full papers (research, applied, industry)
- Short papers (research, applied, industry)

**Deadlines to skip entirely — do not include these:**

| Website language | Action |
|---|---|
| Workshops, challenges, tutorials, symposiums | **Skip — do not add to YAML** |
| Camera-ready / Final version / Camera ready deadline | **Skip — do not add to YAML** |
| Author registration / Early registration / Late registration | **Skip — do not add to YAML** |

**Time formatting rules:**
- Deadlines (submission, abstract): use `23:59:00` unless stated otherwise.
- Notification / decision dates: use `07:59:00` unless stated otherwise.
- Rebuttal start: use `07:59:00`.
- Rebuttal end: use `23:59:00`.
- If the website gives an explicit time, use that time exactly.
- If the conference has multiple rounds, label them clearly (e.g., `"(1st round) Paper Submission"`).

### Step 3 — Extract CORE Ranking (from the same browser session)

The CORE ranking page must be visited inside the **same** research session as Step 1. Extract:

- **`rank_name`**: The ranking letter (e.g., `A*`, `A`, `B`, `C`). If the conference is not ranked, use `Non-ranked`.
- **`rank_source`** and **`rank_source_url`**:
  - If the conference has a CORE rank: Use the edition label (e.g., `ICORE2026`) for `rank_source`, and the exact URL the user provided for `rank_source_url`.
  - If the conference is **Non-ranked**:
    - The provided `conference_rank_url` becomes `rank_source_url`.
    - If `rank_source_url` belongs to **Springer**: Set `rank_source` to the Springer book series (for instance, `Springer LNAI` or `Springer CCIS`).
    - If `rank_source_url` belongs to **IEEE**: Set `rank_source` to the IEEE platform (for instance, `IEEE Xplore`).
    - For any other cases outside these two publishers, use the user's input directly for `rank_source` and mark the `rank_source_url` as `"#"` (for example, if `rank_source` is `"National"`, `rank_source_url` must be `"#"`).

---

### Step 4 — Map Topics to Tags

The project uses a fixed, closed set of tags. You **must only use tags from this list** — do not invent new ones.

Available tags (from `resources/available_tags.json`):

| Tag ID | Label |
|---|---|
| `machine-learning` | Machine Learning |
| `multimedia` | Multimedia |
| `robotics` | Robotics |
| `computer-vision` | Computer Vision |
| `data-mining` | Data Mining |
| `natural-language-processing` | Natural Language Processing |
| `signal-processing` | Signal Processing |
| `speech-processing` | Speech Processing |
| `human-computer-interaction` | Human Computer Interaction |
| `information-theory` | Information Theory |
| `information-retrieval` | Information Retrieval |
| `cryptography` | Cryptography |
| `security-and-privacy` | Security & Privacy |

**How to assign tags:**

1. Read the conference's "Call for Papers" / "Topics of Interest" page.
2. Map each listed topic area to the closest tag(s) above.
3. Assign **all** applicable tags — a conference may have multiple.
4. If a topic doesn't match any tag, **omit it** (do not add custom tags).

**Common mappings:**
- NLP / Text Mining / Computational Linguistics → `natural-language-processing`
- Vision / Image Recognition / Scene Understanding → `computer-vision`
- ML / Deep Learning / Reinforcement Learning → `machine-learning`
- Databases / KDD / Pattern Mining → `data-mining`
- Audio / Music / Acoustics → `signal-processing` or `speech-processing`
- HCI / User Interfaces / Accessibility → `human-computer-interaction`
- Network Security / Privacy / Adversarial ML → `security-and-privacy`
- Cryptographic protocols / Zero-knowledge proofs → `cryptography`
- Information Retrieval / Search / Recommendation → `information-retrieval`
- Video / Multimedia → `multimedia`
- Robotics / Autonomous systems → `robotics`

---

### Step 5 — Compose the YAML File

**File naming:** use the lowercase short name as the filename: `src/data/conferences/<short_name_lowercase>.yml`
(e.g., `emnlp.yml`, `acl.yml`, `neurips.yml`)

**Conference `id`:** `<short_name_lowercase><2-digit-year>` (e.g., `emnlp27`, `acl26`)

**Full YAML schema:**

```yaml
- title: <SHORT_NAME>
  year: <YYYY>
  id: <shortname><yy>
  full_name: <Full official conference name>
  link: "<conference_url>"
  deadlines:
    - type: <type>
      label: <Label from website>
      date: "<YYYY-MM-DD HH:MM:SS>"
      timezone: <TZ>
    # ... more deadlines
  timezone: <primary submission timezone>
  city: <City>
  country: <Country>
  venue: <Venue name or TBD>
  format: <in-person|hybrid>
  date: <Human-readable date, e.g. "November 5-9, 2027">
  start: <YYYY-MM-DD>
  end: <YYYY-MM-DD>
  tags:
      - <tag-id>
      # ... more tags
  rankings:
      rank_name: <A*|A|B|C>
      rank_source: <ICOREyyyy>
      rank_source_url: <core_ranking_url>
  note: "<optional note>"   # omit this field entirely if not applicable
```

> If there are multiple editions (e.g., both 2026 and 2027 entries), list the **most recent/upcoming** edition first, followed by older ones, each as a separate YAML list item (`- title: ...`) in the same file.

---

## Validation Checklist

Before writing **each** file, answer every question. A "no" on the first three is a hard failure — stop and fix it before proceeding.

**Research / source discipline (hard failures if violated):**
- [ ] Exactly **one** research agent/subagent session (or text-only retrieval tool execution) was used for this conference (conference site + CORE ranking, nothing else).
- [ ] Zero external URLs were visited — no Google, no Wikipedia, no aggregators, no unlisted URLs.
- [ ] No additional URL retrieval or lookup was performed after the session closed to verify or fill in gaps.

**Deadline content:**
- [ ] Only full/short paper deadlines are included. No workshops, challenges, camera-ready, final-version, or registration deadlines are in the YAML.
- [ ] All dates come exclusively from the two provided URLs — none fabricated.
- [ ] All dates are in `YYYY-MM-DD HH:MM:SS` format and quoted as strings.
- [ ] Timezone is present on both the top-level field and every individual deadline entry.
- [ ] If no timezone is stated on the website, `UTC-12` (AoE) is used — never `TBD`.

**Schema correctness:**
- [ ] `format` is `in-person` or `hybrid` — the word `virtual` does not appear anywhere.
- [ ] The `id` field is `<shortname><2-digit-year>` and is unique.
- [ ] All tags are from `available_tags.json` — no custom tags.
- [ ] `start` and `end` are unquoted ISO date strings (`YYYY-MM-DD`).
- [ ] `year` is an unquoted integer.
- [ ] `rank_source` is `ICOREXXXX` format (e.g., `ICORE2026`).
- [ ] The `note` field is omitted entirely if not applicable.

---

## Reference Example

See `.agent/skills/find-conference-dates/examples/example.yml` for a complete, valid example (ASIACCS 2026/2027 entries).

Key patterns illustrated in the example:
- Multi-round deadlines with clear round labels (e.g., `"(1st round) Paper Submission"`)
- Correct `final_decision` type for notification dates
- `rankings` block with `rank_name`, `rank_source`, and `rank_source_url`
- Top-level `timezone` matching the individual deadline timezones

---

## Output

Write the final YAML to:
```
/home/tlxuong/Documents/ai-deadlines/src/data/conferences/<short_name_lowercase>.yml
```

If the file already exists (older edition):
- **Prepend** the new edition entry at the top of the file rather than overwriting it.
- Follow the conference's structure in the past to identify details you might have missed.
- If the conference's rank remains unchanged and it has been tracked in the past, you can copy the past conference's `rankings` section directly.
- Your task is only updating yml files; do **NOT** try to rebuild the site (e.g. running builds/checks) to save tokens.

After writing, report back to the user with:
1. The file path created/updated.
2. A summary of all deadlines extracted.
3. The CORE ranking found.
4. The tags assigned and why.
5. Any information that was **not found** on the website (so the user can fill it in manually).
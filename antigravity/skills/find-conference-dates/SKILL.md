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

The user must provide all three of the following:

| Input | Description | Example |
|---|---|---|
| `conference_url` | Official conference website | `https://2027.emnlp.org` |
| `short_name` | Abbreviated name (used as file/id base) | `EMNLP` |
| `core_ranking_url` | Direct CORE portal link for this conference | `https://portal.core.edu.au/conf-ranks/1232/` |

---

## 🚨 Absolute Rules — No Exceptions, Ever

These are hard constraints. They apply to **every single conference**, whether you are processing one or twenty. There is no situation, edge case, or "just this once" that overrides them.

**RULE 1 — BROWSER BUDGET: EXACTLY 1 PER CONFERENCE.**
For each conference, you are allowed exactly **one** `browser_subagent` call. That single session MUST visit both the `conference_url` and the `core_ranking_url` before returning. After it returns, the browser is closed and you write the YAML. You do NOT open another browser to double-check, verify, fill gaps, or look for anything else. If data is missing, write `TBD` and move on.

**RULE 2 — ZERO EXTERNAL URLS.**
You may ONLY navigate to the exact URLs provided by the user. You MUST NOT visit Google, Bing, Wikipedia, DBLP, Semantic Scholar, any search engine, any conference aggregator, or any URL not explicitly given. If you find yourself tempted to "just quickly check" somewhere else — do not. Write `TBD` and report it.

**RULE 3 — NO VERIFICATION BROWSING AFTER THE FACT.**
Once the browser session for a conference has ended, you MUST NOT re-open a browser for that conference for any reason. Not to confirm a date. Not to check a venue. Not to validate a ranking. The data you got is the data you use.

**RULE 4 — FORMAT IS `in-person` OR `hybrid` ONLY.**
The value `virtual` does not exist in this project. Do not use it even if the website says the event is fully online.

**RULE 5 — NO CAMERA-READY OR REGISTRATION DEADLINES.**
Skip camera-ready, final-version, author registration, and early/late registration dates entirely. They must not appear in the YAML.

---

## Processing Multiple Conferences (Batch Input)

When the user provides a **list** of conferences, you MUST process them **one at a time, in order, with no parallelism**.

**Strictly sequential means:**
- Do NOT open browser sessions for multiple conferences at the same time.
- Do NOT collect data for conference N+1 before conference N is fully written and reported.
- Do NOT batch or pipeline any steps across conferences.

**The only allowed execution order:**

```
conference_list = [A, B, C, ...]

STEP 1: Process conference A
  → Open browser (A's conference_url + A's core_ranking_url) → collect data → browser CLOSED.
  → Write A's YAML file.
  → Report A's results.
  *** FULLY STOP. A is done. ***

STEP 2: Process conference B  ← only starts after STEP 1 is 100% complete
  → Open browser (B's conference_url + B's core_ranking_url) → collect data → browser CLOSED.
  → Write B's YAML file.
  → Report B's results.
  *** FULLY STOP. B is done. ***

... repeat for each remaining conference, one at a time.
```

**The browser budget is per-conference and non-transferable.** Each conference gets exactly 1 browser call, consumed the moment it returns. You cannot open a browser for a later conference while a previous one is still being processed, and you cannot re-open a browser for a conference that has already been processed.

---

## Step-by-Step Instructions

### Step 1 — Single Browser Session: Conference Site + CORE Ranking

Launch **one** browser subagent with a task that covers both URLs. This is your **entire browser budget for this conference** — once it returns, no more browsing.

1. Navigate to `conference_url`. Look for pages named "Important Dates", "Call for Papers", "Submission", or similar. Collect all data listed below.
2. **In the same browser session**, navigate to `core_ranking_url` and collect the ranking data.
3. Return **all** collected data in a single structured report. Do not stop early.
4. **Do not navigate to any other URL.** If a link on the conference site looks useful but was not explicitly given by the user, ignore it.

**Conference site — required fields to extract:**

- **`full_name`**: The complete official name of the conference (e.g., `"The 2027 Conference on Empirical Methods in Natural Language Processing"`).
- **`year`**: The year the conference *takes place* (integer, not the submission year).
- **`link`**: The canonical URL of the conference homepage.
- **`deadlines`**: A list of all important milestone dates (see deadline schema below).
- **`timezone`**: The timezone that applies to submission deadlines (e.g., `UTC-12`, `AoE`, `UTC`). If the site says "AoE" or "Anywhere on Earth", use `UTC-12`. **If the site does not state a timezone at all, default to `UTC-12` (AoE).**
- **`city`** and **`country`**: The conference venue location.
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

**Deadlines to skip entirely — do not include these:**

| Website language | Action |
|---|---|
| Camera-ready / Final version / Camera ready deadline | **Skip — do not add to YAML** |
| Author registration / Early registration / Late registration | **Skip — do not add to YAML** |

**Time formatting rules:**
- Deadlines (submission, abstract): use `23:59:00` unless stated otherwise.
- Notification / decision dates: use `07:59:00` unless stated otherwise.
- Rebuttal start: use `07:59:00`.
- Rebuttal end: use `23:59:00`.
- If the website gives an explicit time, use that time exactly.
- If the conference has multiple rounds, label them clearly (e.g., `"(1st round) Paper Submission"`).

---

### Step 3 — Extract CORE Ranking (from the same browser session)

The CORE ranking page must be visited inside the **same** browser session as Step 1. Extract:

- **`rank_name`**: The ranking letter (e.g., `A*`, `A`, `B`, `C`).
- **`rank_source`**: The edition label (e.g., `ICORE2026`). Look for the year on the CORE page — it is typically in the page title or the ranking table header.
- **`rank_source_url`**: Use exactly the URL the user provided as `core_ranking_url`.

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

**Browser / source discipline (hard failures if violated):**
- [ ] Exactly **one** browser session was used for this conference (conference site + CORE ranking, nothing else).
- [ ] Zero external URLs were visited — no Google, no Wikipedia, no aggregators, no unlisted URLs.
- [ ] No additional browser was opened after the session closed to verify or fill in gaps.

**Deadline content:**
- [ ] No camera-ready, final-version, author-registration, or event-registration deadlines are in the YAML.
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

If the file already exists (older edition), **prepend** the new edition entry at the top of the file rather than overwriting it.

After writing, report back to the user with:
1. The file path created/updated.
2. A summary of all deadlines extracted.
3. The CORE ranking found.
4. The tags assigned and why.
5. Any information that was **not found** on the website (so the user can fill it in manually).
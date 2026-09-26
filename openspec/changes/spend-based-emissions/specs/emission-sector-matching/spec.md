## ADDED Requirements

### Requirement: An invoice line SHALL carry the emission sector it was matched to

An invoice line SHALL have three new fields:
- `emission_sector_id`: an `emission_sectors` row, or none.
- `emission_sector_source`: `ai` or `human`.
- `emission_sector_confidence`: 0 to 1, AI matches only.

A line with no sector SHALL have neither a source nor a confidence.

#### Scenario: A new line has no sector

- **WHEN** a line is created by sync or document reading
- **THEN** its `emission_sector_id`, `emission_sector_source` and `emission_sector_confidence` are empty

### Requirement: Lines SHALL be matched to a sector by retrieval and then an LLM choice

The matcher SHALL match a line to a sector of the active factor set's classification in two steps.

**Retrieval.** It SHALL retrieve the sectors most similar to a query. The query is built from:
- the line's item name and description;
- its spend category path;
- its supplier's name, the supplier's enrichment description, and its country.

The sector names SHALL be embedded in a vector collection per classification, using the same embedding as categorization. The collection SHALL be built when missing.

**Choice.** It SHALL offer the top 12 sectors to the LLM as a numbered list and ask for a JSON answer with the chosen number and a confidence, or with no number when none fits.

- A chosen sector SHALL be stored with source `ai` and the confidence.
- "None fits" SHALL leave the line unmatched and be counted as `unmatched`.
- An answer that cannot be parsed, or names a number not offered, SHALL leave the line unmatched and be counted as `failed`.

#### Scenario: A hosting line is matched

- **WHEN** a line "Dedicated server AX41, monthly" from a German hosting company, categorized under Technology / Cloud & Hosting, is matched
- **THEN** it is matched to the offered sector the LLM chose, with source `ai` and its confidence

#### Scenario: Nothing fits

- **WHEN** the LLM answers that none of the offered sectors fits
- **THEN** the line keeps no sector and the run counts it as unmatched

#### Scenario: A malformed answer

- **WHEN** the LLM's answer cannot be parsed into a number and confidence
- **THEN** the line keeps no sector and the run counts it as failed

### Requirement: Identical questions SHALL be answered once

The matcher SHALL cache each answer, keyed by:
- the question's text;
- the set of sectors offered;
- the classification.

A line whose question and offered sectors match a cached answer SHALL take that answer without calling the LLM, and SHALL be counted as `cached`.

#### Scenario: A monthly subscription is matched once

- **WHEN** twelve monthly lines with the same text, supplier and category are matched
- **THEN** the LLM is called once and the other eleven lines are counted as cached

### Requirement: A human's sector SHALL never be overwritten by the matcher

The matcher SHALL only match lines that have no sector, or whose source is `ai` and whose sector belongs to a classification other than the active set's. It SHALL never change a line whose source is `human`.

#### Scenario: A corrected line is left alone

- **WHEN** a human set a line's sector and matching runs again
- **THEN** the line keeps the human's sector

#### Scenario: A new classification re-matches AI lines

- **WHEN** the active set changes to a different classification and matching runs
- **THEN** lines with `ai` sectors of the old classification are matched again, and `human` lines are kept

### Requirement: Editing what a line says SHALL clear an AI sector

When a human changes a line's item name, description or spend category, a sector with source `ai` SHALL be cleared, so that the next matching run matches the line again. A sector with source `human` SHALL be kept.

#### Scenario: Recategorizing clears the AI sector

- **WHEN** a human moves a line with an `ai` sector to another spend category
- **THEN** the line's sector, source and confidence are cleared

#### Scenario: A human sector survives an edit

- **WHEN** a human edits the description of a line whose sector source is `human`
- **THEN** the sector is kept

### Requirement: Matching SHALL be runnable for a company from the command line

`python -m ai_api.emissions.runner --company-id <id> [--limit N] [--rematch]` SHALL match the company's eligible lines and print the counts: matched, unmatched, cached and failed.

- `--limit` SHALL cap the number of lines considered.
- `--rematch` SHALL first clear the company's `ai` sectors. It SHALL leave `human` sectors alone.
- With no active factor set, it SHALL print that there is nothing to match against and exit successfully without changing a line.

#### Scenario: A company's lines are matched

- **WHEN** the runner runs for a company with unmatched lines and an active set
- **THEN** the lines are matched and the counts are printed

#### Scenario: No active set

- **WHEN** the runner runs with no active factor set
- **THEN** it reports that no factors are imported, changes nothing, and exits 0

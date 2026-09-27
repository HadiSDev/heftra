# emission-sector-matching Specification

## Purpose
Matches each invoice line to one emission sector of the active factor set, using a tool-using AI agent with a single-shot fallback, caching identical questions, marking low-confidence matches for review, never overwriting a human's choice, and running as a pipeline run kind and a CLI.

## Requirements
### Requirement: An invoice line SHALL carry the emission sector it was matched to

An invoice line SHALL have three new fields:
- `emission_sector_id`: an `emission_sectors` row, or none.
- `emission_sector_source`: `ai` or `human`.
- `emission_sector_confidence`: 0 to 1, AI matches only.
- `emission_sector_rationale`: one sentence saying why, AI matches only.

A line with no sector SHALL have no source, confidence or rationale.

#### Scenario: A new line has no sector

- **WHEN** a line is created by sync or document reading
- **THEN** its `emission_sector_id`, `emission_sector_source` and `emission_sector_confidence` are empty

### Requirement: Lines SHALL be matched by an agent that searches the sectors itself

The matcher SHALL match each line with an agent. The agent SHALL be given:
- the line's item name, description and amount;
- its spend category path;
- the supplier's name and country.

It SHALL have these tools:
- **search the sectors** of the active classification by free text, returning the closest sectors with code, name and a short description;
- **read one sector's full description**;
- **read the supplier's profile**: its enrichment description and website;
- **read the other lines** of the same invoice.

The sector search SHALL use a vector collection per classification, built from sector names and descriptions with the same embedding as categorization. The collection SHALL be built when it is missing.

The agent SHALL answer in JSON with a sector code, a confidence and a one-sentence rationale, or with no code when none fits. Its number of steps SHALL be bounded.

- A code that exists in the active classification SHALL be stored with source `ai`, the confidence and the rationale.
- An answer with no code SHALL leave the line unmatched, counted as `unmatched`.

#### Scenario: The agent matches a hosting line

- **WHEN** a line "Dedicated server AX41, monthly" from a German hosting company, categorized under Technology / Cloud & Hosting, is matched
- **THEN** the line gets the sector the agent chose, with source `ai`, its confidence and its rationale

#### Scenario: Nothing fits

- **WHEN** the agent answers that no sector fits
- **THEN** the line keeps no sector and the run counts it as unmatched

### Requirement: When the agent fails, a single-shot choice SHALL be made instead

When the agent raises, exceeds its steps or time, answers with something that can't be parsed, or names a code outside the active classification, the matcher SHALL fall back to a single choice:
- it retrieves the 12 sectors closest to the line's text, category and supplier description;
- it asks the LLM for the number of one of them and a confidence, or for none.

A fallback answer SHALL be stored like an agent answer. The run SHALL count agent answers and fallback answers separately. When the fallback also fails, the line SHALL stay unmatched and be counted as `failed`.

#### Scenario: A malformed agent answer falls back

- **WHEN** the agent's answer cannot be parsed and the fallback picks a sector
- **THEN** the line gets the fallback's sector and the run counts one fallback match

#### Scenario: Both fail

- **WHEN** the agent fails and the fallback's answer cannot be parsed either
- **THEN** the line keeps no sector and the run counts it as failed

### Requirement: A low-confidence match SHALL be suggested and marked for review

Every match SHALL be stored whatever its confidence. A match whose confidence is below the categorization review threshold SHALL be reported as needing review wherever lines are shown. Only a "none fits" answer SHALL leave a line unmatched.

#### Scenario: An unsure match is kept

- **WHEN** the agent matches a line with confidence 0.4 and the review threshold is 0.7
- **THEN** the line has the sector, and is marked as needing review

### Requirement: Identical questions SHALL be answered once

The matcher SHALL cache each answer, keyed by:
- the question, which covers the line's text, its category path and its supplier;
- the classification.

A line whose question matches a cached answer SHALL take that answer without running the agent or calling the LLM, and SHALL be counted as `cached`.

#### Scenario: A monthly subscription is matched once

- **WHEN** twelve monthly lines with the same text, supplier and category are matched
- **THEN** the agent runs once and the other eleven lines are counted as cached

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
- **THEN** the line's sector, source, confidence and rationale are cleared

#### Scenario: A human sector survives an edit

- **WHEN** a human edits the description of a line whose sector source is `human`
- **THEN** the sector is kept

### Requirement: Matching SHALL be runnable for a company from the command line

`python -m ai_api.emissions.runner --company-id <id> [--limit N] [--rematch]` SHALL match the company's eligible lines and print the counts: matched by the agent, matched by the fallback, unmatched, cached and failed.

- `--limit` SHALL cap the number of lines considered.
- `--rematch` SHALL first clear the company's `ai` sectors, then ask again rather than reuse cached answers, replacing them. It SHALL leave `human` sectors alone.
- With no active factor set, it SHALL print that there is nothing to match against and exit successfully without changing a line.

#### Scenario: A company's lines are matched

- **WHEN** the runner runs for a company with unmatched lines and an active set
- **THEN** the lines are matched and the counts are printed

#### Scenario: No active set

- **WHEN** the runner runs with no active factor set
- **THEN** it reports that no factors are imported, changes nothing, and exits 0

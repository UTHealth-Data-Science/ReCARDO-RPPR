---
title: ReCARDO CDE Naming Rules
version: 1.2
status: active
last_updated: 2026-07-29
---

# ReCARDO CDE Naming Rules

## Purpose

This document is the canonical naming standard for ReCARDO candidate Common Data Elements (CDEs).
Use it when creating or reviewing `suggested_naming`, `AI_generated_name`, or
`final_approved_name`.

The goal is to produce a concise, natural-English noun phrase that preserves the complete
source concept without inventing unsupported semantics.

## Required Inputs

Review all available fields before proposing a name:

| Priority | Field | Use |
| --- | --- | --- |
| 1 | `source_trace_json.name` | Original question or source element name; primary source for semantic context |
| 2 | Other `source_trace_json` metadata | Assessment, variable name, object, property, modifiers, units, form position, and permissible values |
| 3 | `comment` | Reviewer-requested clarification, reordering, qualifier preservation, or identified semantic problem |
| 4 | `candidate_name` | Existing decomposed concept; useful but not authoritative when it conflicts with the source |
| 5 | `final_approved_name` | Approved naming pattern and preferred wording for analogous concepts |
| 6 | Existing suggested name | Starting point only; it must still pass all rules in this document |

Do not generate a final suggestion from `candidate_name` alone when source metadata is available.

## Output Columns

Naming output must include these columns:

| Column | Requirement |
| --- | --- |
| `AI_generated_name` | Contains only the proposed formal CDE name. Do not place uncertainty labels, review instructions, or explanatory text in this field. |
| `AI comments` | Contains the reason for uncertainty, missing metadata, possible assessment attribution, decomposition concern, reviewer conflict, or other issue requiring human review. Leave blank when no explanation is needed. |

When a precise name is uncertain, use the most specific generic name supported by the source and
write the unresolved issue in `AI comments`. If the source does not support even a generic semantic
name, leave `AI_generated_name` blank and explain what evidence is missing in `AI comments`.

## Decision Precedence

When fields disagree, use this order:

1. Preserve the concept explicitly stated by the original source.
2. Preserve source-specific context, qualifiers, assessment names, units, and scientific notation.
3. Follow reviewer comments that clarify, reorder, or preserve semantics.
4. Follow established wording in comparable `final_approved_name` examples.
5. Use natural English word order.
6. Use conservative source-supported wording and document unresolved uncertainty in `AI comments`.

A reviewer suggestion must not be accepted when it removes source context, overgeneralizes the
concept, or guesses unsupported semantics. Preserve the supported concept and document the reason
in `AI comments`.

## Standard Name Structure

Use this default structure:

```text
Object -> Context or Modifier -> Measured Concept -> Property -> Unit
```

Example:

```text
Patient current donepezil prescription same dose and frequency stability duration in years
```

Names should be noun phrases, not questions or complete sentences. Do not add a terminal period.

## Core Rules

### OBJ-001: Use object-first naming

Place the data subject first when the source has an identifiable subject.

Preferred:

```text
Patient age in years at most recent coronary artery bypass surgery
Patient current antidepressant medication use presence
Caregiver distress severity associated with patient crying and tearfulness
```

Avoid:

```text
Age at surgery for patient
Current antidepressant medication use presence
Patient caregiver distress severity
```

### OBJ-002: Preserve the correct object

Use `Patient` unless the source explicitly identifies another object, such as:

- `Caregiver`
- `Informant`
- `Clinician`
- `Participant`
- `Study partner`

Do not remove `Patient` merely to shorten a name. Do not add `Patient` when the measured concept
clearly belongs to a caregiver, informant, clinician, or study partner.

### SEM-001: Name the measured concept, not the response action

Describe what the item measures rather than mechanically translating survey wording such as
agreement, endorsement, or response.

Source:

```text
I feel that I am part of the U.S. American culture.
```

Preferred:

```text
Patient sense of belonging to U.S. American culture
```

Avoid:

```text
Patient agreement that they feel part of U.S. American culture
```

Retain `agreement` only when the response scale itself is the measured property and the semantic
concept cannot be represented more directly.

### SEM-002: Do not invent semantics

Do not infer an assessment, subdomain, diagnosis, specimen, causal relationship, or measurement
property that is not supported by the source.

If metadata for a code such as `ADAS_Q2a` does not establish the measured subdomain, mark the item
for further review in `AI comments`. Do not guess memory, orientation, language, or another
construct.

### SEM-003: Keep uncertainty out of the proposed name

The proposed name must remain a clean CDE noun phrase. Do not embed uncertainty labels, temporary
review text, confidence statements, or instructions for reviewers in the name.

Use `AI comments` to state:

- which concept or assessment cannot be confirmed
- which source metadata is missing or conflicting
- which interpretation was used provisionally
- what a domain expert should verify

Preferred output:

| `AI_generated_name` | `AI comments` |
| --- | --- |
| `Patient cognitive assessment immediate word recall trial 2 target word church accuracy` | `The parent cognitive assessment could not be confirmed from source_trace_json; generic cognitive assessment wording was used.` |

Avoid placing explanatory text inside `AI_generated_name`.

### CTX-001: Preserve important qualifiers

Retain every qualifier needed to distinguish the concept, including:

- current
- most recent
- last
- primary
- same dose and frequency
- English-speaking or Spanish-speaking
- plasma
- FreeSurfer ROI
- Large HDL or Large VLDL
- female hormone replacement pills
- PET scan
- trial, list, position, sequence, or entry number

Preferred:

```text
Plasma specimen use for phospho-tau 181 assay
Patient total duration of female hormone replacement pill use in years
CBF voxel count in the right cerebral white matter FreeSurfer ROI
```

Avoid:

```text
Assay specimen type
Patient hormone therapy duration
Right cerebral white matter voxel count
```

### CTX-002: Preserve causal and conditional relationships

Retain relationships expressed by terms such as:

- following
- conditional on
- based on
- due to
- associated with
- resulting from

Preferred:

```text
Patient self-harm intention presence following disclosure of increased Alzheimer's disease risk based on PET scan results
Patient injury presence due to sleep dream-enactment behaviors
```

Avoid:

```text
Patient self-harm intention
Patient sleep injury presence
```

### CTX-003: Preserve numbered-series context

Keep the source's list, trial, position, sequence, treatment entry, drug entry, or episode number.
Do not silently combine or renumber repeated form elements.

Preferred:

```text
Patient AVLT version A trial 3 word list 2A position 3 target word nail recall presence
RxNorm identifier for medication sequence 23
Episode 7 end date month
```

If the number appears to be an artifact of incorrect decomposition, retain the supported context
and flag the item for decomposition review.

### PROP-001: Use the correct semantic property

Choose the property that matches the source question and permissible values.

| Property | Use when the source measures |
| --- | --- |
| `Presence` | Whether a condition, behavior, finding, or use exists |
| `History` | Whether something ever occurred, occurred previously, or is part of past history |
| `Status` | A current state represented by more than simple presence or absence |
| `Indicator` | A defined flag whose meaning is explicitly supported by metadata |
| `Type` | A category or kind |
| `Specification` | Free-text detail for an "Other, specify" response |
| `Duration` | Elapsed time |
| `Age` | Age at an event |
| `Year` | Calendar year of an event |
| `Frequency` | How often something occurs |
| `Severity` | Degree or intensity |
| `Count` | Number of occurrences or correct responses |
| `Percentage` | Proportion expressed as a percentage |
| `Concentration` | Analyte concentration |
| `Ratio` | Ratio between explicitly named quantities |

Do not substitute one property for another merely because both use numeric or binary values.

### PROP-002: Distinguish history from presence

Use `History` when the source explicitly asks `ever`, `history`, `previously`, or otherwise refers
to past receipt or occurrence.

Preferred:

```text
Patient history of hormone replacement therapy receipt
Patient history of sleep behavior-related injury presence
```

Avoid:

```text
Patient hormone replacement therapy presence
Patient sleep behavior-related injury presence
```

### PROP-003: Use presence for true binary existence variables

When a binary item measures whether a concept exists, end the name with `presence`.

Preferred:

```text
Patient current donepezil medication use presence
Patient study medical abnormality presence
Left basal ganglia abnormality presence
```

Do not use `presence` when the source is actually asking for a type, status, severity, frequency,
or historical occurrence.

### PROP-004: Name "Other, specify" variables as specifications

Place `other` immediately after the object or as close as natural English permits, and end with
`specification`.

Preferred:

```text
Patient other cancer treatment type specification
Patient other treatment administration frequency specification
Patient other race or ethnicity specification
```

Avoid:

```text
Patient cancer treatment type other specified
Patient treatment administration frequency other specification
```

### LANG-001: Use natural English word order

Avoid long stacks of modifiers. Add prepositions when they clarify semantic relationships.

Preferred:

```text
Patient distress severity associated with threatened self-harm
Patient knowledge of American history
Patient duration of residence in English-speaking environment in years
```

Avoid:

```text
Patient self-harm threat distress severity
Patient knowledge American history
Patient English-speaking environment residence duration
```

### LANG-002: Use sentence case with canonical terminology

Use sentence case for ordinary English words. Capitalize only the first word, proper names,
assessment names, abbreviations, and scientific notation that requires capitalization.

Preferred:

```text
Patient self-reported English reading proficiency
Patient Alzheimer disease neuropathologic change NIA-AA severity
```

Avoid arbitrary title case and lowercase forms of established abbreviations.

### SCI-001: Preserve scientific terminology and notation exactly

Preserve official spelling, punctuation, capitalization, hyphenation, and molecular notation.

Examples:

- ADAS
- MoCA
- MMSE
- CBF
- ROI
- FreeSurfer
- RxNorm
- ARTAG
- NIA-AA
- ARIA-E
- ARIA-H
- GM1(d18:1/16:0)
- SM(d18:1/18:0)

Preferred:

```text
GM1(d18:1/16:0) ganglioside concentration in nM
SM(d18:1/18:0)/SM(d16:1/20:0) sphingomyelin concentration in nM
```

Do not normalize scientific notation to ordinary title case.

### UNIT-001: Include units when they are part of the concept

Append a unit when the source metadata, question, or approved pattern establishes it.

Examples:

- `in years`
- `in months`
- `mm²`
- `cc`
- `nM`

Preferred:

```text
Patient hormone replacement therapy initiation age in years
Left superior frontal gyrus surface area in mm²
Right lateral temporal gray matter volume (cc)
```

Do not infer a unit when the source does not establish one.

### MED-001: Normalize current medication-use names

Use this pattern for current medication-use binary variables:

```text
Patient current [medication or medication class] medication use presence
```

Examples:

```text
Patient current donepezil medication use presence
Patient current antidepressant medication use presence
```

### MED-002: Normalize prescription-stability duration names

When the source asks how long a current prescription has remained at the same dose and frequency,
use:

```text
Patient current [medication] prescription same dose and frequency stability duration in [unit]
```

Example:

```text
Patient current paliperidone prescription same dose and frequency stability duration in months
```

Retain `same medication` when the source explicitly includes medication identity as part of the
stability condition.

### COG-001: Include the parent cognitive assessment name

Every neuropsychological or cognitive assessment item must identify its parent assessment when
known.

Examples of parent assessments include:

- NACC FTLD
- MoCA
- MMSE
- ADAS
- AVLT
- WRAT
- WASI
- WMS
- CDR
- FAQ
- Neuropsychiatric Inventory

Preferred:

```text
Patient NACC FTLD Semantic Word-Picture Matching Test total correct word-picture match count
Patient ADAS item 7g ideational praxis performance presence
Patient AVLT trial 6 word list A position 1 target word drum recall presence
```

Avoid:

```text
Word Reading score
Delayed Recall
Trails B
```

### COG-002: Use generic wording when the assessment is unknown

When an item is clearly cognitive but the parent assessment cannot be identified, use a generic
assessment phrase supported by the source, such as `cognitive assessment`, and explain the missing
attribution in `AI comments`.

| `AI_generated_name` | `AI comments` |
| --- | --- |
| `Patient cognitive assessment immediate word recall trial 2 target word church accuracy` | `The parent cognitive assessment could not be confirmed from source_trace_json.` |

Do not guess WRAT, NACC, MoCA, or another assessment.

### COG-003: Document uncertain assessment attribution separately

When metadata suggests a likely assessment but attribution remains uncertain, do not include the
unconfirmed assessment name in `AI_generated_name`. Use the source-supported generic concept and
record the possible attribution in `AI comments`.

| `AI_generated_name` | `AI comments` |
| --- | --- |
| `Patient verbal fluency non-L-initial word rule violation error count in 1 minute` | `The item may belong to NACC verbal fluency, but the parent assessment is not confirmed by source metadata.` |

The assessment name may be added to the proposed name only after source metadata or domain-expert
review confirms it.

### REV-001: Apply reviewer comments selectively

Normally accept comments requesting:

- reordering
- clarification
- restoration of an object
- restoration of a qualifier
- correction of a property or unit
- preservation of source terminology

Do not accept a comment that:

- overgeneralizes the source
- removes a meaningful qualifier
- changes the measured property without evidence
- guesses an assessment or scientific meaning
- drops causal, conditional, specimen, or modality context

Record the reason in `AI comments` when retaining the source-supported interpretation over a
reviewer suggestion.

### REV-002: Use only current review resolutions

When multiple review rows share a `candidate_key`, ignore rows marked `superseded`.
Use the single active resolution. If multiple non-superseded resolutions remain, stop and flag the
conflict instead of choosing silently.

## Naming Workflow

Use this sequence for each candidate:

1. Read `source_trace_json.name`, the complete source metadata, `candidate_name`, and `comment`.
2. Identify the true object: Patient, Participant, Caregiver, Informant, Clinician, or Study partner.
3. State the measured semantic concept without copying question syntax.
4. Extract distinguishing context, including timing, sequence, anatomy, specimen, modality,
   medication, culture, language, and assessment.
5. Select the correct property using `PROP-001`.
6. Preserve history, causal, and conditional relationships.
7. Add the parent cognitive assessment when confirmed; otherwise use generic source-supported
   wording and explain the uncertainty in `AI comments`.
8. Preserve scientific notation and add only supported units.
9. Draft the name using `Object -> Context -> Concept -> Property -> Unit`.
10. Populate `AI comments` when the name requires a provisional interpretation or human review.
11. Run the quality checklist below.

## Quality Checklist

A proposed name is ready only when every applicable item is satisfied:

- [ ] The object is present and correct.
- [ ] The name describes the measured concept rather than the response action.
- [ ] All context from `source_trace_json.name` is represented or intentionally excluded as
      non-semantic form wording.
- [ ] The `comment` field was reviewed.
- [ ] Current, most recent, last, primary, sequence, entry, trial, and position qualifiers are
      preserved.
- [ ] Presence, history, status, type, duration, age, year, frequency, severity, count, ratio, and
      specification are not conflated.
- [ ] Causal and conditional relationships are preserved.
- [ ] Cognitive items include the confirmed parent assessment or conservative generic wording.
- [ ] The proposed name contains no uncertainty labels or review instructions.
- [ ] Every unresolved naming issue is explained in `AI comments`.
- [ ] Scientific capitalization and notation are exact.
- [ ] Units are included only when supported and meaningful.
- [ ] The wording is natural English and does not contain stacked or duplicated modifiers.
- [ ] The suggestion does not introduce unsupported semantics.
- [ ] The result is a noun phrase with no terminal period.

## Regression Examples

Use these examples when testing future naming-generation changes:

| Source or candidate concept | Expected naming pattern |
| --- | --- |
| Current donepezil dose and frequency stable for a number of years | `Patient current donepezil prescription same dose and frequency stability duration in years` |
| Ever received hormone replacement therapy | `Patient history of hormone replacement therapy receipt` |
| Age at most recent coronary artery bypass surgery | `Patient age in years at most recent coronary artery bypass surgery` |
| Other cancer treatment, specify | `Patient other cancer treatment type specification` |
| Plasma used for phospho-tau 181 assay | `Plasma specimen use for phospho-tau 181 assay` |
| U.S. American cultural belonging | `Patient sense of belonging to U.S. American culture` |
| Motor-function change currently judged meaningful | `Patient current meaningful motor function change presence` |
| Increased Alzheimer's disease risk disclosed from PET results and conditional self-harm question | `Patient self-harm intention presence following disclosure of increased Alzheimer's disease risk based on PET scan results` |

## Maintenance Rules

Use the following process when changing this document:

1. Assign a stable rule ID to every new rule.
2. Do not renumber or reuse an existing rule ID.
3. Add at least one source-supported preferred example.
4. Add an avoid example when the failure mode is not obvious.
5. Add or update a regression example when a rule fixes a recurring error.
6. Record the change in the changelog.
7. Recheck existing approved examples before changing terminology used across many CDEs.

## Changelog

| Version | Date | Change |
| --- | --- | --- |
| 1.2 | 2026-07-29 | Renamed the proposed-name output column from `suggested_name_2` to `AI_generated_name`. |
| 1.1 | 2026-07-29 | Removed uncertainty markers from proposed names and added the required `AI comments` output column for uncertainty reasons and review notes. |
| 1.0 | 2026-07-29 | Consolidated the original CDE naming guidelines, cognitive-assessment rules, reviewer-comment rules, and patterns learned from `final_approved_name`. |

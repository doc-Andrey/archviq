# ARCHVIQ thematic analysis modules — v0.4 research

This package keeps four product questions separate:

1. `compatibility_analysis.py` — interaction architecture for two independently assessed partners.
2. `burnout_analysis.py` — current load/recovery plus architectural susceptibility.
3. `ai_work_analysis.py` — preferred format of human–AI collaboration.
4. `architecture_gap_analysis.py` — compares the Engine 43 prior, subjective expression and task-bound cognitive measurements axis by axis.

The frozen Engine 43 is not changed. These modules consume only its six practical axes:

`resource`, `switching`, `lock`, `novelty`, `control`, `processing_cost`.

`maturation / late consolidation` is intentionally excluded from client-facing thematic analyses.

## Architecture clarification and GAP logic

The three layers remain independent:

`Engine 43 prediction → questionnaire expression → cognitive measurement`.

For every practical axis the GAP module reports signed and absolute differences:

- questionnaire minus Engine 43;
- cognition minus Engine 43;
- cognition minus questionnaire.

No layer is treated as ground truth and no global tension percentage is produced. Tension is reported only through explicit patterns, for example `performance_maintained_with_high_compensatory_effort` or `current_state_may_be_suppressing_measured_performance`. Thresholds of 15 and 30 points are provisional research rules and cannot enter client mode until calibrated prospectively.

The architecture questionnaire separates six ordinary processing expressions from three contextual scales: compensatory effort, current state interference and context support. This prevents a temporary sleep/load problem from being silently relabeled as stable architecture.

## EEG-informed role-processing update

Version 0.2 incorporates one bounded conclusion from the final DeceptionGame EEG analysis: Player versus Observer is a reproducible task-state contrast (nested leave-one-dyad-out AUC 0.926; balanced accuracy 0.841), with `r_alpha_late` and `r_alpha_sustained` selected in all 12 outer folds. Truth versus lie was null (AUC 0.497).

Therefore the package adds questionnaire constructs for decision-role coordination and human–AI agency switching. EEG values are not inserted into client scores, Engine 43 is not recalibrated, and no lie or hallucination detector is claimed.

- Compatibility adds `decision_role_coordination`.
- AI work adds `agency_retention`, `verification_role`, `role_switch_flexibility`, and `passive_acceptance_risk`.
- Burnout adds an experimental `decision_load` block that is deliberately excluded from the integrated index until prospective validation.

## Validation gate

All four analyzers are `RESEARCH_ONLY` until their questionnaire and output model pass the validation gate. Client mode raises an error when an instrument is not marked `PASSED` in the validation registry.

The first pilot should collect item-level responses, not only final scale means. Recommended minimum:

- at least 100 people and at least 5 people per item for the first psychometric pass;
- preferably 200+ for stable factor work;
- at least 50 repeated cognitive sessions for test–retest reliability;
- for compatibility, both partners answer independently and the pair ID is retained;
- for burnout, repeat at 2–4 weeks and collect external outcomes such as absence, workload and recovery;
- for AI work, validate against task accuracy, completion time, verification errors and independent expert scoring.

`validate_measurements.py` calculates missingness, floor/ceiling effects, Cronbach alpha, a one-factor omega approximation, corrected item–total correlations, split-half reliability, a parallel-analysis signal and cognitive plausibility/retest checks.

Internal consistency alone never opens the gate. Each thematic scale must also correlate in the expected magnitude with at least one independent criterion listed under `validation_criteria` in the blueprint. Criterion items or licensed instruments are not copied into this repository; the pilot dataset supplies their final scores in the named `CRIT_*` columns.

## Files

- `config/thematic_questionnaires.json` — original pilot items and scale definitions.
- `config/validation_registry_unvalidated.json` — default closed gate.
- `score_questionnaires.py` — scores 1–5 item responses to 0–100 thematic scales.
- `validate_measurements.py` — produces the validation registry.
- `validate_domain_dimensionality.py` — tests whether final client-facing outputs collapse into one another; synthetic mode checks formula overlap and real mode checks the pilot.
- `compatibility_analysis.py` — five relationship domains, including decision-role coordination; deliberately no global compatibility percentage.
- `burnout_analysis.py` — separates architecture, current self-report, recovery pressure and optional cognitive strain.
- `ai_work_analysis.py` — interaction modes and recommendations, not intelligence or employability.
- `architecture_gap_analysis.py` — layer-by-layer discrepancy and compensation patterns.
- `cognitive_tools/rdm_perception_test.html` — balanced browser RDM task with trial-level export.
- `cognitive_tools/fit_ddm_ez.py` — session-safe exploratory EZ-DDM fitting with uncertainty intervals.
- `QUESTIONNAIRES_AND_GAP_MODEL_RU.md` — full Russian design rationale and interpretation rules.
- `examples/` — input structures for one person and a pair.

## Typical commands

Score a pilot questionnaire:

```bash
python3 -m analysis_modules.score_questionnaires \
  --responses pilot_responses.csv \
  --blueprint analysis_modules/config/thematic_questionnaires.json \
  --instrument burnout_questionnaire \
  --out burnout_scores.csv
```

Validate item-level questionnaires and cognitive exports:

```bash
python3 -m analysis_modules.validate_measurements \
  --questionnaire pilot_responses.csv \
  --scale-map analysis_modules/config/thematic_questionnaires.json \
  --cognitive cognitive_sessions.csv \
  --cognitive-trials cognitive_trials.csv \
  --out validation_registry.json
```

Run research analyses before validation:

```bash
python3 -m analysis_modules.compatibility_analysis \
  --input analysis_modules/examples/pair_example.json \
  --validation analysis_modules/config/validation_registry_unvalidated.json \
  --out compatibility_result.json

python3 -m analysis_modules.burnout_analysis \
  --input analysis_modules/examples/person_example.json \
  --validation analysis_modules/config/validation_registry_unvalidated.json \
  --out burnout_result.json

python3 -m analysis_modules.ai_work_analysis \
  --input analysis_modules/examples/person_example.json \
  --validation analysis_modules/config/validation_registry_unvalidated.json \
  --out ai_work_result.json

python3 -m analysis_modules.architecture_gap_analysis \
  --input analysis_modules/examples/person_example.json \
  --validation analysis_modules/config/validation_registry_unvalidated.json \
  --out architecture_gap_result.json
```

Add `--client-mode` only after the corresponding registry status is `PASSED`.

Client mode now requires two independent gates per product: the thematic questionnaire and the final output model (`compatibility_outputs`, `burnout_outputs`, or `ai_work_outputs`).

Before the pilot, run the structural check:

```bash
python3 -m analysis_modules.validate_domain_dimensionality \
  --module ai_work \
  --synthetic 5000 \
  --validation analysis_modules/config/validation_registry_unvalidated.json \
  --out ai_work_structural_check.json
```

After collecting data, replace `--synthetic 5000` with `--records pilot_records.jsonl`. Synthetic independence is only a formula audit; it cannot validate psychological constructs.

## Cognitive limitation to fix before full validation

The current browser battery exports aggregate metrics. This is sufficient for plausibility checks and repeated-session ICC, but not for proper split-half reliability, lapse analysis or reaction-time distribution cleaning. The production validation battery should additionally export trial-level rows with:

`CLIENT_ID, SESSION_ID, TEST, TRIAL_INDEX, CONDITION, CORRECT, RT_MS, TIMESTAMP`.

The summary CSV should remain for the website; the trial CSV is the research validation layer.

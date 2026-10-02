# Engine 43 reproducibility benchmark

The packaged `archviq_engine43.py` was compared against the frozen 150-person calculation used to prepare this release.

Compared coordinates:

- all 9 X9 outputs
- all 7 practical output coordinates

Result:

```text
N = 150
coordinates per participant = 16
maximum absolute numerical difference = 7.105427357601002e-15
rows above 1e-9 difference = 0
```

This check confirms that renaming and packaging the engine did not alter the calculation mathematics.

It is a software reproducibility test, not a claim that external cognitive or EEG outcomes have already been established for every output.

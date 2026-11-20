# Roadmap

Items below are **not yet implemented**; they describe planned future work.

## Near term

- [ ] Load the resource library from a user-supplied CSV instead of a
      hardcoded module (`quota_db.py`).
- [ ] Add a command to export top-k matches for a batch of queries from a CSV
      file (batch mode).
- [ ] Add a small labeled benchmark corpus with cross-validation to report
      accuracy more rigorously.

## Medium term

- [ ] Replace / augment the TF-IDF core with a sentence-embedding model
      (e.g. BERT-family) to improve colloquial and paraphrase coverage.
- [ ] Add compound-pricing logic (e.g. an exterior wall decomposes into
      masonry + insulation + finishing).
- [ ] Tune the fusion weights (0.40 / 0.25 / 0.25 / 0.10) on a held-out
      labeled set, and parameterize them via configuration rather than
      hardcoding them (the ablation study already shows the parameter signal
      over-penalizes at the current defaults).

## Long term

- [ ] Integrate with a BIM export pipeline (Revit/Dynamo) for end-to-end
      "component → quota code + unit price" automation.
- [ ] Add a persistence layer for user-customized resource libraries.
- [ ] Provide a packaged web service / API.

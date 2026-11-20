# Examples

Run from the project root:

```bash
python examples/example.py
```

`example.py` demonstrates the three primary use cases of the public API:

1. **Standard matching** — a well-formed engineering description is matched
   against the resource library, returning the top-k candidates ranked by
   combined score.
2. **Colloquial normalization** — a shorthand description
   (e.g. `老楼砖墙370厚 抹水泥20 翻新`) is normalized to standard terms before
   matching.
3. **Change-cost prediction** — a change type + area + component is mapped to
   a predicted cost band and amount using TF-IDF similarity.

For an interactive browser demo, run `python main.py --web` (requires `gradio`).

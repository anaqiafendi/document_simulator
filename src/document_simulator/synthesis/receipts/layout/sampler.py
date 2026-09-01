"""Draw a *diverse* batch of layout specs, not just a representative one.

Weighted sampling reproduces the corpus, which is the wrong objective for
training data. ``MERCHANT_COPY`` is 92% of the corpus, so 200 weighted draws
yield roughly 184 of one font and would miss ``BOTTOM`` logo placement (2 of 979
templates) almost every time. A model trained on that never learns the rare
cases, which are exactly the ones it fails on in production.

``stratified_specs`` therefore guarantees a floor: every value of every style
axis that clears a share threshold appears at least once, with the remainder of
the batch filled by weight so the bulk still looks like real receipts.
"""

from __future__ import annotations

import random

from document_simulator.synthesis.receipts.layout.prior import Prior, load_prior, sample_spec
from document_simulator.synthesis.receipts.layout.spec import STYLE_FIELDS, LayoutSpec


def _force_style_value(
    rng: random.Random, field: str, value: str, prior: Prior, attempts: int = 24
) -> LayoutSpec:
    """Sample a spec, then pin one style axis to a required value.

    Sampling first keeps the rest of the spec a genuine replayed combination;
    only the targeted axis is overridden.
    """
    spec = sample_spec(rng, perturb=1, prior=prior)
    if getattr(spec.style, field) == value:
        return spec
    style = spec.style.model_copy(update={field: value})
    return spec.model_copy(
        update={"style": style, "perturbed": tuple(sorted({*spec.perturbed, field}))}
    )


def stratified_specs(
    n: int,
    seed: int,
    *,
    perturb: int = 2,
    min_share: float = 0.01,
    prior: Prior | None = None,
) -> list[LayoutSpec]:
    """Draw ``n`` specs covering every reasonably-common style value.

    Args:
        n: Batch size.
        seed: Reproducibility seed.
        perturb: Style axes re-rolled per weighted draw.
        min_share: Style values rarer than this share of the corpus are not
            guaranteed a slot. At the 1% default the coverage set is small
            enough to leave most of the batch weighted.
        prior: Override the shipped prior (used by tests).

    Returns:
        Exactly ``n`` specs. Coverage slots come first, then weighted draws.
    """
    if n <= 0:
        return []

    prior = prior or load_prior()
    rng = random.Random(seed)
    total = prior.template_count

    # Coverage set: (axis, value) pairs that clear the share threshold.
    required: list[tuple[str, str]] = [
        (field, value)
        for field in STYLE_FIELDS
        if field in prior.marginals
        for value, count in sorted(prior.marginals[field].items())
        if count / total >= min_share
    ]
    rng.shuffle(required)

    specs: list[LayoutSpec] = [
        _force_style_value(rng, field, value, prior) for field, value in required[:n]
    ]
    specs.extend(sample_spec(rng, perturb=perturb, prior=prior) for _ in range(n - len(specs)))
    return specs

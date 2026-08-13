"""FSTAT-compatible Weir & Cockerham (1984) pairwise theta for diploid loci.

This module is response-format agnostic.  It was implemented after the Zhoushan EOG
predictors and inference rule were frozen but before the released raw genotype workbook
was parsed or any empirical pairwise FST value was computed.

For each multiallelic locus and each allele, the variance components ``a``, ``b`` and
``c`` follow the Weir & Cockerham sample-size-corrected estimator.  Pairwise multilocus
theta is ``sum(a) / sum(a + b + c)`` across all usable alleles/loci.  Missing diploid
genotypes are excluded locus-wise.  Values are not clipped to [0, 1].
"""
from __future__ import annotations

from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass
import math

Allele = Hashable
Genotype = tuple[Allele, Allele] | None


@dataclass(frozen=True)
class WeirCockerhamPairResult:
    population_a: str
    population_b: str
    theta: float
    numerator_a: float
    denominator_abc: float
    n_usable_loci: int
    n_allele_components: int
    n_complete_genotypes_a: int
    n_complete_genotypes_b: int


def _complete(genotype: Genotype) -> bool:
    return genotype is not None and len(genotype) == 2


def _allele_frequency_and_heterozygote_fraction(
    genotypes: Sequence[Genotype],
    allele: Allele,
) -> tuple[int, float, float]:
    complete = [genotype for genotype in genotypes if _complete(genotype)]
    n = len(complete)
    if n == 0:
        return 0, math.nan, math.nan
    allele_count = sum(int(a == allele) + int(b == allele) for a, b in complete)
    frequency = allele_count / (2.0 * n)
    # h_i in Weir & Cockerham is the observed frequency of heterozygotes
    # carrying the focal allele.  A heterozygote contributes to each of its two alleles.
    heterozygote_count = sum(int(a != b and (a == allele or b == allele)) for a, b in complete)
    heterozygote_fraction = heterozygote_count / float(n)
    return n, frequency, heterozygote_fraction


def _locus_components(
    genotypes_a: Sequence[Genotype],
    genotypes_b: Sequence[Genotype],
) -> tuple[float, float, int, int, int] | None:
    complete_a = [genotype for genotype in genotypes_a if _complete(genotype)]
    complete_b = [genotype for genotype in genotypes_b if _complete(genotype)]
    n1 = len(complete_a)
    n2 = len(complete_b)
    if n1 == 0 or n2 == 0:
        return None

    alleles = sorted(
        {allele for genotype in (*complete_a, *complete_b) for allele in genotype},
        key=lambda value: (type(value).__name__, repr(value)),
    )
    if not alleles:
        return None

    r = 2.0
    n_bar = (n1 + n2) / r
    if n_bar <= 1.0:
        return None
    n_c = (r * n_bar - (n1 * n1 + n2 * n2) / (r * n_bar)) / (r - 1.0)
    if not math.isfinite(n_c) or n_c <= 0.0:
        return None

    sum_a = 0.0
    sum_total = 0.0
    components = 0
    for allele in alleles:
        n_a, p1, h1 = _allele_frequency_and_heterozygote_fraction(complete_a, allele)
        n_b, p2, h2 = _allele_frequency_and_heterozygote_fraction(complete_b, allele)
        if n_a != n1 or n_b != n2:
            raise RuntimeError("internal complete-genotype accounting drift")

        p_bar = (n1 * p1 + n2 * p2) / (r * n_bar)
        s2 = (n1 * (p1 - p_bar) ** 2 + n2 * (p2 - p_bar) ** 2) / ((r - 1.0) * n_bar)
        h_bar = (n1 * h1 + n2 * h2) / (r * n_bar)

        common = p_bar * (1.0 - p_bar) - ((r - 1.0) / r) * s2
        a = (n_bar / n_c) * (
            s2 - (common - 0.25 * h_bar) / (n_bar - 1.0)
        )
        b = (n_bar / (n_bar - 1.0)) * (
            common - ((2.0 * n_bar - 1.0) / (4.0 * n_bar)) * h_bar
        )
        c = 0.5 * h_bar
        total = a + b + c
        if not all(math.isfinite(value) for value in (a, b, c, total)):
            raise RuntimeError("non-finite Weir-Cockerham component")
        sum_a += a
        sum_total += total
        components += 1

    return sum_a, sum_total, components, n1, n2


def pairwise_weir_cockerham_theta(
    population_a: str,
    population_b: str,
    loci_a: Mapping[str, Sequence[Genotype]],
    loci_b: Mapping[str, Sequence[Genotype]],
    *,
    locus_order: Sequence[str],
) -> WeirCockerhamPairResult:
    """Estimate multilocus pairwise Weir-Cockerham theta without clipping."""

    if population_a == population_b:
        raise ValueError("pairwise FST requires two distinct populations")
    if len(set(locus_order)) != len(locus_order) or not locus_order:
        raise ValueError("locus_order must contain unique loci")
    if any(locus not in loci_a or locus not in loci_b for locus in locus_order):
        raise ValueError("both populations must contain every declared locus key")

    numerator = 0.0
    denominator = 0.0
    n_usable_loci = 0
    n_components = 0
    complete_a_total = 0
    complete_b_total = 0
    for locus in locus_order:
        result = _locus_components(loci_a[locus], loci_b[locus])
        if result is None:
            continue
        a, total, components, n_a, n_b = result
        numerator += a
        denominator += total
        n_components += components
        complete_a_total += n_a
        complete_b_total += n_b
        n_usable_loci += 1

    if n_usable_loci == 0 or not math.isfinite(denominator) or abs(denominator) <= 1e-15:
        theta = math.nan
    else:
        theta = numerator / denominator

    return WeirCockerhamPairResult(
        population_a=str(population_a),
        population_b=str(population_b),
        theta=float(theta),
        numerator_a=float(numerator),
        denominator_abc=float(denominator),
        n_usable_loci=n_usable_loci,
        n_allele_components=n_components,
        n_complete_genotypes_a=complete_a_total,
        n_complete_genotypes_b=complete_b_total,
    )


def all_pairwise_theta(
    populations: Mapping[str, Mapping[str, Sequence[Genotype]]],
    *,
    population_order: Sequence[str],
    locus_order: Sequence[str],
) -> tuple[WeirCockerhamPairResult, ...]:
    """Compute every unordered population pair using a frozen order."""

    ids = tuple(str(value) for value in population_order)
    if len(ids) < 2 or len(set(ids)) != len(ids):
        raise ValueError("population_order must contain unique populations")
    if tuple(populations) != ids:
        # Require exact declared order to prevent an outcome-dependent subset/reordering.
        raise ValueError("population mapping must exactly follow frozen population_order")
    output = []
    for i, population_a in enumerate(ids):
        for population_b in ids[i + 1 :]:
            output.append(
                pairwise_weir_cockerham_theta(
                    population_a,
                    population_b,
                    populations[population_a],
                    populations[population_b],
                    locus_order=locus_order,
                )
            )
    return tuple(output)

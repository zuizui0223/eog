# Sweden river-barrier external M-world bridge v1

## Role

This is a retrospective external bridge for a **movement-only finite BAM subfamily**.
A and B remain unrestricted.

The source is the public Dryad dataset accompanying the Swedish 24-catchment study of
river barriers and population synchrony. Published synchrony results are already known,
so they are not used as endpoints.

## Frozen cohort

All three study species are retained:

- *Salmo trutta*;
- *Phoxinus phoxinus*;
- *Esox lucius*.

No species is selected by result.

## Frozen calendar split

The README reports that 90% of sampling occurred after 1988. The bridge therefore uses
two equal 17-year calendar blocks:

- calibration: 1988–2004;
- heldout: 2005–2021.

Rows before 1988 are outside the bridge by calendar rule, not by response.

## Frozen M family

Physical sites are identified by river ID and released RT90 coordinates. Fragment IDs
encode the published barrier-derived fragmentation.

Four geometry thresholds are derived from all within-river physical-site distances.
Each is crossed with two connectivity assumptions:

- barrier closed: edges cannot cross fragment identity;
- barrier open: edges may cross fragments.

One fully open within-river world is added, for nine M worlds total.

Calibration-positive sites are movement sources. Later positive sites are hard
falsification witnesses.

The primary bridge never uses the response-derived `all_data_synchrony.csv` table.

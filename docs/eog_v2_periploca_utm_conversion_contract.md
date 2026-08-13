# EOG v2.1 Periploca response-free UTM conversion contract

## Status

**Response-free geography conversion only. Microsatellite contents remain unopened.**

The released geography file has already been byte-identified as SHA-256
`d54af743f39332aab753964ee0d6950550097d7b29216d155a50967153d5d233`.

The frozen response-free UTM-row extraction contains exactly 33 unique populations across 14 declared island/region labels, fingerprint:

`01ebd21add5c912c9420807c68229f76a8fb0f5f2fa0b59158911802322e915a`.

Every row uses compact syntax such as `28R 64269 322216`: UTM zone number, latitude-band letter, a five-digit easting token and a six-digit northing token.

## Conversion problem

The release does not include separate decimal latitude/longitude columns. Therefore the compact numeric precision must be resolved before graph construction.

No genetic data or genetic result may be used to choose the conversion.

## Frozen scale-selection rule

Test exactly three response-free numeric multipliers for both easting and northing:

`1, 10, 100`.

For a candidate multiplier to be admissible, **all 33 released rows** must satisfy all of the following after conversion with WGS84 UTM for the declared zone and latitude-band hemisphere:

1. scaled easting is in `[100000, 900000]` metres;
2. scaled northing is in `[0, 10000000]` metres;
3. conversion to WGS84 longitude/latitude is finite;
4. converted longitude is inside the nominal six-degree UTM longitude zone (central meridian ±3.25 degrees; small tolerance only);
5. converted latitude is inside the standard eight-degree latitude band encoded by the released letter, with 0.25-degree numerical tolerance.

Latitude bands use the standard UTM/MGRS sequence `CDEFGHJKLMNPQRSTUVWX`; `X` spans 72–84°N and all other bands span eight degrees. Bands `N` and later are northern hemisphere; earlier bands are southern.

The scale is accepted only if **exactly one** of the three candidates satisfies all rows. If zero or multiple candidates survive, geography is `non_estimable_utm_scale_ambiguous`; no genetic file is opened to resolve it.

## Coordinate output

For the uniquely admitted scale, freeze for every population:

- released `Island/region`;
- released population code;
- released UTM string;
- zone and latitude-band;
- scaled easting/northing in metres;
- WGS84 latitude/longitude.

The output must contain exactly 33 unique population IDs and 33 finite coordinate pairs.

## Island-focused validation subset

Before genetic-response access, the primary EOG validation subset is frozen as the **Canary Archipelago** populations whose released `Island/region` is exactly one of:

- `Lanzarote`;
- `Fuerteventura`;
- `Gran Canaria`;
- `Tenerife`;
- `La Gomera`;
- `La Palma`;
- `El Hierro`.

This geographic rule is chosen because it defines one coherent island archipelago relevant to EOG's island-reachability estimand. It is not based on genetic diversity or differentiation.

Under the already frozen response-free geography rows this subset contains exactly 20 population codes:

`FAM, COF, CAR, GUA, BAN, AMA, CHO, GUI, ANA, PHI, HER, RAS, TEN, BVI, VAL, ARG, TIM, FAG, SAB, RES`.

The 13 Mediterranean/mainland/Morocco/Western-Sahara populations are excluded from the primary island-network validation by geography alone and are not reinstated after genetic-response access.

## Stage-2 boundary

Only after the UTM conversion and 20-node Canary subset are frozen may a later commit construct:

- response-free Canary node coordinates;
- EOG graph/operator and exact-eventual predictors;
- the complete conventional-reference candidate family;
- response transform, ridge penalty, nested outer/inner folds and empirical bootstrap/GO rule.

Those predictors must be byte-archived before `Periploca_nSSR.txt` is decoded or parsed.

## Hard response firewall

This conversion contract does not authorize reading `Periploca_nSSR.txt`. The microsatellite file remains an opaque checksum-provenanced byte object until the Stage-2 predictor artifact has been frozen.

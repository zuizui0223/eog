# Frozen Thalassia response-free Stage-1 geography

This directory freezes the 17-site response-free geography for the Indo-Australian Archipelago `Thalassia hemprichii` candidate **before** microsatellite workbook contents are opened.

Authoritative Stage-1 workflow:

- run `31667178363`;
- head `1967d206bb32fcd864e7ddbc3cbd76a0543050c0`;
- artifact `9168352573`;
- artifact digest `sha256:281795b720741a28eeb70a6191a80696d8ac519c3d539488243538add6e586aa`.

Provenance route: the University of Western Australia repository lists Zenodo record `4937634` as an access route for Dryad DOI `10.5061/dryad.404rm`. The workflow verified the record title and exact expected file names, and verified Zenodo-released MD5/size before use.

Frozen released objects:

- GPS workbook SHA-256 `b97e910aa7f9fb52aeeebf434a5480e91995575bc77178d73503d4462fcd9132`, MD5 `22801051462bdccbe2f0a9f29c4b3940`, 10,091 bytes;
- microsatellite workbook SHA-256 `aaaab9e302c9be8cf4e108d2aee5867c0b64ed70b6d3b81bad4d60168ee7f2f3`, MD5 `ec25c053161d4d62b86c860193475784`, 118,400 bytes.

Only the GPS workbook cells were inspected. The microsatellite workbook was downloaded as opaque bytes for checksum/size only; its container, worksheet names, cell values, genotypes and genetic response were not accessed.

The GPS workbook contains one `IAA` sheet with `Site name`, `Code`, `Lat`, `Long`. All 17 rows have finite coordinates. `population_coordinates.csv` uses the `Code` column as the stable primary population ID and retains `Site name` only as a label.

- coordinate CSV SHA-256 `7311e561ec2dbeecc57b0b6d8b83b4819697f23480303bcb4478e5750660ce49`;
- coordinate fingerprint `334948e6af43c50d5fb7bfec3396065a1c39d64e0bab7eb5f4a767a42249245d`;
- Stage-1 manifest fingerprint `12a34c597dbf4130ad1dcda8a9822504291a0ac7d4f34fa31c43d8d373d49764`.

These coordinates are not regenerated after genetic-response access.

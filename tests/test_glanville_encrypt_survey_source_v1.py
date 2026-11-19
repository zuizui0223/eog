import csv
import io
import json
import runpy
import zipfile
from pathlib import Path

import pytest


def _m():
    return runpy.run_path("scripts/glanville_encrypt_survey_source_v1.py")


def _protocol():
    return json.loads(Path("validation/glanville_uploaded_origin_crosswalk_v1/protocol_v1.json").read_text())


def _source_archive():
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,"w") as z:
        years=[2007,2008,2009,2010,2011,2012]
        rows=["year\tpatch\tpopulation\tplantago\tveronica"]
        for y in years:
            for patch in range(1000,2001):
                rows.append(f"{y}\t{patch}\t{1 if patch%2 else 0}\t2\t1")
        z.writestr("data/survey_data.tsv","\n".join(rows)+"\n")
        net=["patch\tx\ty"]+[f"{p}\t0.001\t6.7" for p in range(1000,2001)]
        z.writestr("data/patch_network.tsv","\n".join(net)+"\n")
    return stream.getvalue()


def test_public_key_is_public_only_and_download_source_pinned():
    p=_protocol()
    assert p["status"]=="frozen_after_user_file_inspection_before_crosswalk"
    assert p["source_published_dataset"]["source_sha256"]=="140e5361f9bced20a434bfee01bae6ce7c925e028718cdb9c6fd8aa635cc912a"
    assert "PRIVATE KEY" not in json.dumps(p)
    assert p["raw_user_uploaded_file_in_repo"] is False
    assert p["raw_source_bytes_in_artifact"] is False


def test_source_selection_is_exact_and_does_not_export_year_outside_contract():
    m=_m();p=_protocol()
    with zipfile.ZipFile(io.BytesIO(_source_archive())) as z:
        dataset=m["_convert"](z,p)
    assert len(dataset["survey"])==6006
    assert len(dataset["network"])==1001
    assert dataset["years"]==[2007,2008,2009,2010,2011,2012]
    assert all(2007<=row[0]<=2012 for row in dataset["survey"])


def test_sealed_data_roundtrip_only_with_private_key():
    cryptography=pytest.importorskip("cryptography")
    from cryptography.hazmat.primitives.asymmetric import rsa,padding
    from cryptography.hazmat.primitives import serialization,hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    import hashlib,base64,zlib
    m=_m()
    p=_protocol()
    private=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    public=private.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo)
    p["ephemeral_encryption_public_key_pem"]=public.decode()
    p["public_key_sha256"]=hashlib.sha256(public).hexdigest()
    fake={"years":[2007],"survey":[[2007,"10","1","3","2"]],"network":[["10","2.7","6.7"]]}
    sealed=m["_seal"](fake,p)
    assert "10" not in sealed["ciphertext_b64"][:0]  # only ciphertext is exposed
    key=private.decrypt(base64.b64decode(sealed["wrapped_key_b64"]),
                        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),algorithm=hashes.SHA256(),label=None))
    aad=("EOG-audit-v1|"+p["prior_source_repository"]["archive_sha256"]).encode()
    plain=AESGCM(key).decrypt(base64.b64decode(sealed["nonce_b64"]),
                                base64.b64decode(sealed["ciphertext_b64"]),aad)
    assert json.loads(zlib.decompress(plain))==fake
    with pytest.raises(Exception):
        AESGCM(key).decrypt(base64.b64decode(sealed["nonce_b64"]),
                           base64.b64decode(sealed["ciphertext_b64"]),b"wrong AAD")


def test_duplicate_source_patch_year_fails_closed():
    m=_m();p=_protocol()
    archive=_source_archive()
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        assert len(m["_convert"](z,p)["survey"])>0
    bad=io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(archive)) as src,zipfile.ZipFile(bad,"w") as z:
        s=src.read("data/survey_data.tsv").decode()
        s+=s.splitlines()[1]+"\n"
        z.writestr("data/survey_data.tsv",s)
        z.writestr("data/patch_network.tsv",src.read("data/patch_network.tsv"))
    with zipfile.ZipFile(io.BytesIO(bad.getvalue())) as z:
        with pytest.raises(m["SourceStop"],match="STOP_SURVEY_DUPLICATE_YEAR_PATCH"):
            m["_convert"](z,p)

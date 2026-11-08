"""NEON trap-night join qualification is not an occupancy model."""
import csv
from benchmarks.neon_mammal_source_gate_v1 import check

def write(path,fields,rows):
    with path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def example(tmp_path):
    p=tmp_path/"mam_perplotnight.csv";t=tmp_path/"mam_pertrapnight.csv"
    write(p,["nightuid","eventID","namedLocation","collectDate"],[
        dict(nightuid="n1",eventID="bout",namedLocation="HARV_001",collectDate="2023-06-01"),
        dict(nightuid="n2",eventID="bout",namedLocation="HARV_001",collectDate="2023-06-02")])
    write(t,["nightuid","trapCoordinate","trapStatus"],[
        dict(nightuid="n1",trapCoordinate="A1",trapStatus="3"),
        dict(nightuid="n2",trapCoordinate="A1",trapStatus="5")])
    return p,t

def test_two_nights_pass_source_structure_only(tmp_path):
    p,t=example(tmp_path);r=check(p,t)
    assert r["status"]=="PASS_SOURCE_STRUCTURE_ONLY"
    assert r["repeated_trap_bout_keys"]==1
    assert r["multi_night_bouts"]==1

def test_unmatched_trap_night_stops(tmp_path):
    p,t=example(tmp_path)
    with t.open("a") as f:f.write("unknown,A2,3\n")
    r=check(p,t)
    assert r["status"]=="STOP"
    assert r["unmatched_trap_nights"]==1

def test_duplicate_plot_night_stops(tmp_path):
    p,t=example(tmp_path)
    with p.open("a") as f:f.write("n1,bout,HARV_001,2023-06-01\n")
    assert check(p,t)["status"]=="STOP"

def test_single_night_cannot_qualify_repeated_detection(tmp_path):
    p,t=example(tmp_path)
    write(t,["nightuid","trapCoordinate","trapStatus"],[
        dict(nightuid="n1",trapCoordinate="A1",trapStatus="3")])
    assert "no_repeated_trap_nights" in check(p,t)["errors"]

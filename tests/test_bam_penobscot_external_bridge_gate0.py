from validation.bam_penobscot_external_bridge_v1.gate0_archive_architecture import (
    canonical_sha256,
    normalized_names,
    parse_links,
)


def test_directory_parser_normalizes_module_names():
    html = """
    <html><body>
      <a href="x">Name</a>
      <a href="a">FishCommunity /</a>
      <a href="b">WaterQuality /</a>
      <a href="c">Geomorphology /</a>
    </body></html>
    """
    names = normalized_names(parse_links(html))
    assert names == ("FishCommunity", "Geomorphology", "WaterQuality")


def test_directory_parser_preserves_file_names():
    html = """
    <a href="a">Penobscot Fish Data 2010 to 2012.accdb</a>
    <a href="b">_Fish Community - README.pdf</a>
    """
    names = normalized_names(parse_links(html))
    assert "Penobscot Fish Data 2010 to 2012.accdb" in names
    assert "_Fish Community - README.pdf" in names


def test_canonical_hash_is_order_independent_for_mappings():
    assert canonical_sha256({"a": 1, "b": 2}) == canonical_sha256({"b": 2, "a": 1})

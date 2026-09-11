import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "validation/btnw_selective_promotion/stage0_terminal_stop_certificate.json"


class BtnwStage0StopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = json.loads(P.read_text(encoding="utf-8"))

    def test_terminal_stop_is_nonempirical(self):
        self.assertEqual(cls := self.r["status"], "stop_pre_response_metadata_identity_transport_or_geometry")
        self.assertFalse(self.r["counts_as_predictive_evidence"])
        self.assertFalse(self.r["counts_as_empirical_conclusion"])
        self.assertEqual(self.r["empirical_ledger_increment"], 0)

    def test_response_firewall_remained_closed(self):
        self.assertEqual(self.r["response_payload_requests"], 0)
        self.assertEqual(self.r["response_payload_bytes"], 0)
        self.assertEqual(self.r["response_header_bytes"], 0)
        self.assertEqual(self.r["response_rows"], 0)
        self.assertFalse(self.r["response_values_opened"])
        self.assertEqual(self.r["model_fits"], 0)
        self.assertEqual(self.r["selector_decisions"], 0)
        self.assertEqual(self.r["heldout_scores"], 0)

    def test_no_post_manifest_rescue(self):
        self.assertFalse(self.r["rerun_or_identity_relaxation_authorized"])
        self.assertFalse(self.r["changes_closed_eog_wf"])


if __name__ == "__main__":
    unittest.main()

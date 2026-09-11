import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CERT = ROOT / "validation" / "snapshot_usa_selective_promotion" / "terminal_pre_response_stop_certificate.json"


class SnapshotUsaPreResponseStopRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = json.loads(CERT.read_text(encoding="utf-8"))

    def test_is_terminal_but_nonempirical(self):
        self.assertEqual(
            self.r["terminal_status"],
            "stop_pre_response_deployment_transport_schema_or_structure",
        )
        self.assertFalse(self.r["counts_as_predictive_evidence"])
        self.assertFalse(self.r["counts_as_empirical_conclusion"])
        self.assertEqual(self.r["empirical_ledger_increment"], 0)

    def test_response_firewall_remained_closed(self):
        self.assertFalse(self.r["response_consumed"])
        self.assertFalse(self.r["response_values_opened"])
        self.assertEqual(self.r["sequence_payload_requests"], 0)
        self.assertEqual(self.r["sequence_header_bytes_opened"], 0)
        self.assertEqual(self.r["model_fits"], 0)
        self.assertEqual(self.r["heldout_scores"], 0)
        self.assertTrue(self.r["claim_boundary"]["response_firewall_intact"])

    def test_authoritative_identity_is_frozen(self):
        a = self.r["authoritative_run"]
        self.assertEqual(a["run_id"], 34454196324)
        self.assertEqual(a["job_id"], 102796644160)
        self.assertEqual(a["artifact_id"], 10142755954)
        self.assertEqual(
            a["artifact_digest"],
            "sha256:72e6e1b48c1a46db2ed263fb8100b3a88058d7e6e64ac72b54356666780255c4",
        )
        self.assertEqual(
            a["result_fingerprint"],
            "4c98b01aa7172a16897f0c11e8b1b206a1ca03b23837c7d9f341f52f2bc0aa77",
        )

    def test_no_rescue_path_is_claimed(self):
        self.assertTrue(self.r["next_gate"].startswith("none"))
        self.assertFalse(self.r["claim_boundary"]["predictive_result_reached"])
        self.assertFalse(self.r["claim_boundary"]["selective_promotion_real_translation_resolved"])


if __name__ == "__main__":
    unittest.main()

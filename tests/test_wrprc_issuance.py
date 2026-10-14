# SPDX-License-Identifier: Apache-2.0
"""WRPRC handler regression tests with synthetic DB and signing dependencies.

Load the actual functions without the application's import-time configuration
and trust-store setup. No database, network, certificate or key is used here.
Run with: python -m unittest discover -s tests -v
"""

import ast
import base64
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, mock_open
import urllib.parse


ROOT = Path(__file__).resolve().parents[1]


def load_functions(path, names, namespace):
    tree = ast.parse(path.read_text())
    functions = [node for node in tree.body
                 if isinstance(node, ast.FunctionDef) and node.name in names]
    for function in functions:
        function.decorator_list = []
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), "exec"), namespace)


class WrprcIssuanceTests(unittest.TestCase):
    def setUp(self):
        self.privacy_url = "https://example.test/privacy"
        cursor = Mock()
        cursor.fetchall.return_value = [(
            1, "synthetic-use", "2026-10-14", "2027-10-14",
            "en", "Synthetic identity verification", 1, self.privacy_url,
            "http://data.europa.eu/eudi/policy/privacy-policy",
            1, "mso_mdoc", json.dumps({"doctype_value": "eu.europa.ec.eudi.pid.1"}),
            json.dumps(["eu.europa.ec.eudi.pid.1", "given_name"]),
        )]
        connection = Mock()
        connection.cursor.return_value = cursor
        model_namespace = {
            "conn": lambda: connection,
            "json": json,
            "pymysql": SimpleNamespace(MySQLError=RuntimeError),
        }
        load_functions(ROOT / "app/models.py",
                       {"get_intended_use_id", "deserialize_json"}, model_namespace)
        self.legal_entity = {
            "infoURI": ["https://example.test/info"], "country": "DE",
            "identifier": [{"identifier": "DE000000000",
                            "type": "http://data.europa.eu/eudi/id/VATIN"}],
            "LegalPerson": {"legalName": ["Synthetic Test RP"]},
        }
        self.db = SimpleNamespace(
            check_user=Mock(return_value=(1,)),
            check_intendedUse=Mock(return_value=(1,)),
            get_intended_use_id=model_namespace["get_intended_use_id"],
            get_wrp_intended_id=Mock(return_value=[{
                "wrp_id": 1, "provider_id": 1, "trade_name": "Synthetic Test Service",
                "supportURI": ["https://example.test/support"],
                "entitlements": ["https://uri.etsi.org/19475/Entitlement/Service_Provider"],
                "isPSB": False, "srvDescription": [],
            }]),
            get_legal_entity_id=Mock(return_value=[self.legal_entity]),
            insert_registration_certificate=Mock(),
        )
        signed_document = base64.b64encode(json.dumps({
            "payload": "synthetic-payload",
            "signatures": [{"protected": "synthetic-header", "signature": "synthetic-signature"}],
        }).encode()).decode()
        self.post = Mock(side_effect=[
            Mock(json=lambda: {"status_list": {"idx": 1, "uri": "https://example.test/status"}}),
            Mock(json=lambda: {"hashes": ["aGFzaA==", "aGFzaA=="], "signature_date": "2026-10-14"}),
            Mock(json=lambda: {"documentWithSignature": ["c3ludGhldGljLWNvc2U=", signed_document]}),
        ])
        certificate = Mock()
        certificate.public_bytes.return_value = b"synthetic-certificate"
        private_key = Mock()
        private_key.sign.return_value = b"synthetic-signature"
        self.namespace = {
            "request": SimpleNamespace(get_json=lambda **kwargs: {"hash_pid": "synthetic-hash", "intended_use_id": 1}),
            "db": self.db,
            "cfgserv": SimpleNamespace(
                service_url="https://example.test/", statuslist_apikey="synthetic-key",
                url_statuslist="https://example.test/status/take", sca_signer_url="https://example.test/signer",
                wrprc_certificate="synthetic.der", wrprc_intermediate="synthetic-ca.der",
                wrprc_privateKey="synthetic-key.pem",
            ),
            "datetime": datetime, "timedelta": timedelta, "timezone": timezone,
            "requests": SimpleNamespace(post=self.post), "json": json, "base64": base64,
            "urllib": urllib, "open": mock_open(read_data=b"synthetic"),
            "x509": SimpleNamespace(load_der_x509_certificate=Mock(return_value=certificate)),
            "serialization": SimpleNamespace(
                Encoding=SimpleNamespace(PEM="PEM"),
                load_pem_private_key=Mock(return_value=private_key),
            ),
            "default_backend": Mock(), "ec": SimpleNamespace(ECDSA=Mock()),
            "utils": SimpleNamespace(Prehashed=Mock()), "hashes": SimpleNamespace(SHA256=Mock()),
            "jsonify": lambda value: value,
        }
        load_functions(ROOT / "app/RPR_routes.py", {
            "intended_use_registration_certificate", "validate_required_fields",
            "error_response", "error_invalid",
        }, self.namespace)

    def assert_issued_policy(self):
        result = self.namespace["intended_use_registration_certificate"]()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["code"], 200)
        self.assertTrue(result["data"]["file_base64"])
        self.assertTrue(result["data"]["cose_base64"])
        signing_request = json.loads(self.post.call_args_list[1].kwargs["data"])
        payload = json.loads(base64.b64decode(signing_request["documents"][0]["document"]))
        self.assertEqual(payload["privacy_policy"], self.privacy_url)
        self.assertEqual(payload["credentials"][0]["meta"], {"doctype_value": "eu.europa.ec.eudi.pid.1"})
        self.db.insert_registration_certificate.assert_called_once()
        return payload

    def test_model_policy_uri_is_included_in_the_wrprc_signing_payload(self):
        payload = self.assert_issued_policy()
        self.assertEqual(payload["info_uri"], "https://example.test/info")

    def test_optional_information_uri_can_be_absent(self):
        self.legal_entity.pop("infoURI")
        payload = self.assert_issued_policy()
        self.assertNotIn("info_uri", payload)


if __name__ == "__main__":
    unittest.main()

import os
import unittest
from unittest.mock import patch

from pipeline.ingestao.config import resolve_runtime_config, validate_runtime_config


class ConfigTests(unittest.TestCase):
    def test_resolve_runtime_config_prefers_explicit_args(self):
        with patch.dict(os.environ, {"STORAGE_ACCOUNT_NAME": "env-account", "TABLE_NAME": "env-table"}, clear=False):
            config = resolve_runtime_config({"storage_account": "arg-account", "table_name": "arg-table"})
            self.assertEqual(config["storage_account"], "arg-account")
            self.assertEqual(config["table_name"], "arg-table")

    def test_resolve_runtime_config_supports_environment_aliases(self):
        with patch.dict(os.environ, {"AZURE_STORAGE_ACCOUNT_NAME": "alias-account", "EVENTHUB_NAME": "alias-hub"}, clear=False):
            config = resolve_runtime_config({})
            self.assertEqual(config["storage_account"], "alias-account")
            self.assertEqual(config["eventhub_name"], "alias-hub")

    def test_validate_runtime_config_requires_key_fields(self):
        with self.assertRaises(ValueError):
            validate_runtime_config({"storage_account": "", "table_name": ""}, required_keys=["storage_account", "table_name"], context="batch")


if __name__ == "__main__":
    unittest.main()

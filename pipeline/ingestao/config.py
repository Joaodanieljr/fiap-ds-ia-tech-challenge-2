import os
from typing import Any, Dict, List, Optional


def resolve_runtime_config(args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    args = args or {}

    storage_account = (
        args.get("storage_account")
        or args.get("STORAGE_ACCOUNT")
        or os.getenv("STORAGE_ACCOUNT_NAME")
        or os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        or ""
    )

    table_name = (
        args.get("table_name")
        or args.get("TABLE_NAME")
        or os.getenv("TABLE_NAME")
        or ""
    )

    eventhub_name = (
        args.get("eventhub_name")
        or args.get("EVENTHUB_NAME")
        or os.getenv("EVENTHUB_NAME")
        or ""
    )

    eventhub_connection_string = (
        args.get("eventhub_connection_string")
        or args.get("EH_CONNECTION_STRING")
        or os.getenv("EH_CONNECTION_STRING")
        or ""
    )

    return {
        "storage_account": storage_account,
        "table_name": table_name,
        "eventhub_name": eventhub_name,
        "eventhub_connection_string": eventhub_connection_string,
    }


def validate_runtime_config(config: Dict[str, Any], required_keys: Optional[List[str]] = None, context: str = "pipeline") -> Dict[str, Any]:
    required_keys = required_keys or ["storage_account", "table_name"]
    missing = [key for key in required_keys if not str(config.get(key, "")).strip()]

    if missing:
        raise ValueError(f"Configuração inválida para {context}: faltam os campos: {', '.join(missing)}")

    return config

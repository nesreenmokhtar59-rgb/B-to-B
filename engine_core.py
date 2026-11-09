
# engine_core.py
import re
import hashlib
import secrets  
import threading  
from datetime import datetime

try:
    import pandas as pd
    HAS_DATA_LIB = True
except ImportError:
    HAS_DATA_LIB = False

MODULE_SECRET_TOKEN = b"GENERIC_SYSTEM_CRYPTOGRAPHIC_SALT_FOR_TESTING_ONLY_XYZ"
internal_lock = threading.Lock()

INTERNAL_USER_REGISTRY = {
    hashlib.sha256(b"USER_PHONE_A" + MODULE_SECRET_TOKEN).hexdigest(): {
        "profile_label": "GENERIC_CLIENT_A", "mode_flag": True, "service_tokens": 10
    },
    hashlib.sha256(b"USER_PHONE_B" + MODULE_SECRET_TOKEN).hexdigest(): {
        "profile_label": "GENERIC_CLIENT_B", "mode_flag": False, "service_tokens": 40
    }
}

PUBLIC_INDEX_STORE = []
ACTIVE_POOL_STORE = {
    "pool_id_01": {
        "item_label": "STANDARD_MATERIAL_A", "zone_label": "STANDARD_ZONE_A",
        "base_unit_rate": 50.0, "target_limit_units": 100, "current_total_units": 95,
        "pool_status": "OPEN", "records_list": []
    }
}

class BaseProcessingSystem:
    def __init__(self):
        self.trigger_keywords = [r"kw_1", r"kw_2", r"kw_3", r"kw_4", r"\+", r"digit"]
        self.validated_item_list = ["ITEM_A", "ITEM_B", "ITEM_C", "ITEM_D"]
        self.system_margin_rate = 0.05  

    def evaluate_incoming_payload(self, secure_account_id: str, raw_input_string: str) -> dict:
        account_profile = INTERNAL_USER_REGISTRY.get(secure_account_id)
        if not account_profile:
            return {"status": "error", "message": "INVALID_OR_UNREGISTERED_ACCOUNT_ID"}
        clean_string = raw_input_string.strip().lower()
        is_triggered = any(re.search(kw, clean_string) for kw in self.trigger_keywords)
        has_numeric_data = bool(re.search(r'\d+', clean_string))
        if is_triggered and has_numeric_data:
            if account_profile["mode_flag"]:
                return {"status": "success", "target_route": "PIPELINE_ROUTE_ALPHA"}
            else:
                label_prefix = account_profile["profile_label"].split("_")[0]
                return {"status": "success", "target_route": "PIPELINE_ROUTE_BETA", "client": label_prefix}
        return self._fallback_routing_procedure(secure_account_id, account_profile, raw_input_string)

    def _fallback_routing_procedure(self, secure_account_id: str, account_profile: dict, raw_input_string: str) -> dict:
        with internal_lock:  
            if account_profile["service_tokens"] <= 0:
                return {"status": "insufficient_tokens", "message": "TOKEN_LIMIT_REACHED"}
            INTERNAL_USER_REGISTRY[secure_account_id]["service_tokens"] -= 1
        return {"status": "success", "target_route": "PIPELINE_ROUTE_GAMMA", "remaining": INTERNAL_USER_REGISTRY[secure_account_id]["service_tokens"]}

    def process_telemetry_report(self, secure_account_id: str, raw_telemetry_data: dict) -> dict:
        account_profile = INTERNAL_USER_REGISTRY.get(secure_account_id)
        if not account_profile: return {"status": "error", "message": "AUTHENTICATION_FAILED"}
        anonymized_user_hash = hashlib.pbkdf2_hmac('sha256', secure_account_id.encode(), MODULE_SECRET_TOKEN, 100000).hex()
        anonymized_data_record = {
            "record_uuid": secrets.token_hex(16), "anonymized_fingerprint": anonymized_user_hash,
            "captured_value": float(raw_telemetry_data.get("numerical_value", 0)), "system_timestamp": datetime.now().strftime("%Y-%m-%d %H:00:00")
        }
        with internal_lock:
            PUBLIC_INDEX_STORE.append(anonymized_data_record)
            INTERNAL_USER_REGISTRY[secure_account_id]["service_tokens"] += 2
        return {"status": "success", "data_preview": anonymized_data_record}

    def register_pool_transaction(self, secure_account_id: str, target_pool_id: str, allocation_units: float) -> dict:
        with internal_lock:
            pool_object = ACTIVE_POOL_STORE.get(target_pool_id)
            if not pool_object or pool_object["pool_status"] != "OPEN":
                return {"status": "error", "message": "POOL_CLOSED_OR_NOT_FOUND"}
            available_pool_delta = pool_object["target_limit_units"] - pool_object["current_total_units"]
            sanitized_allowed_units = min(allocation_units, available_pool_delta)
            calculated_gross_total = round(sanitized_allowed_units * pool_object["base_unit_rate"] * (1 + self.system_margin_rate), 2)
            transaction_receipt_record = {
                "transaction_uuid": secrets.token_hex(16), "allocated_units": sanitized_allowed_units, "gross_total_amount": calculated_gross_total
            }
            pool_object["current_total_units"] += sanitized_allowed_units
            pool_object["records_list"].append(transaction_receipt_record)
            if pool_object["current_total_units"] >= pool_object["target_limit_units"]:
                pool_object["pool_status"] = "CLOSED"
        return {"status": "success", "transaction_details": transaction_receipt_record, "updated_pool_status": pool_object["pool_status"]}

    def generate_chart_dataframe(self):
        if not HAS_DATA_LIB: return None
        data = {
            "DIMENSION_X": ["ITEM_A", "ITEM_B", "ITEM_C", "ITEM_D"],
            "SERIES_1_ERROR_MARGIN":,
            "SERIES_2_OPTIMIZED_PATH": [5, 12, 18, 25]
        }
        df = pd.DataFrame(data)
        return df.melt(id_vars=["DIMENSION_X"], var_name="METRIC_TYPE", value_name="METRIC_VALUE")

import os
import sys
import unittest
from pathlib import Path
from datetime import datetime, date, timedelta

# Set paths
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "TheQuest_Customer_MobileApp"))
sys.path.insert(0, str(BASE_DIR / "TheQuest_Company_MobileApp"))

from database.key_service import (
    init_key_system, get_daily_super_key, rotate_daily_super_key,
    mint_room_key, revoke_room_key, verify_door_access,
    get_all_rooms_door_status, set_door_state, get_door_access_logs,
    hash_key, STAFF_WIFI_SSID
)
from TheQuest_Customer_MobileApp.backend.hotel_data import (
    create_reservation, extend_reservation
)
from TheQuest_Customer_MobileApp.backend.db import get_active_stay


class TestHotelKeyAndDoorSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_key_system()

    def test_01_daily_super_key_and_rotation(self):
        """Test daily super key retrieval, hashing, and rotation."""
        sk1 = get_daily_super_key()
        self.assertIsNotNone(sk1["plain_key"])
        self.assertIsNotNone(sk1["key_hash"])
        self.assertEqual(hash_key(sk1["plain_key"]), sk1["key_hash"])

        # Rotate super key
        sk2 = rotate_daily_super_key()
        self.assertNotEqual(sk1["plain_key"], sk2["plain_key"])
        self.assertEqual(hash_key(sk2["plain_key"]), sk2["key_hash"])

        # Fetching again should return the rotated key
        sk3 = get_daily_super_key()
        self.assertEqual(sk2["plain_key"], sk3["plain_key"])

    def test_02_regular_key_mint_and_revoke(self):
        """Test regular key minting, hashing, and checkout revocation."""
        room_id = 5  # Room 202 (Vacant)
        cust_id = 1
        res_id = 8888

        # Mint regular key
        res = mint_room_key(room_id, cust_id, res_id)
        self.assertEqual(res["status"], "active")
        self.assertEqual(hash_key(res["plain_key"]), res["key_hash"])

        # Test unlocking with this key
        granted, msg, details = verify_door_access(
            room_id=room_id,
            key_token=res["plain_key"],
            method="wifi",
            wifi_ssid="Quest_Room_202",
            user_type="customer",
            user_id=cust_id,
            user_name="Amelia Watson"
        )
        self.assertTrue(granted, msg)
        self.assertEqual(details["door_state"], "unlocked")

        # Now revoke key (customer checks out)
        revoke_room_key(room_id, res_id)

        # Same key should now be DENIED
        granted_after, msg_after, _ = verify_door_access(
            room_id=room_id,
            key_token=res["plain_key"],
            method="wifi",
            wifi_ssid="Quest_Room_202",
            user_type="customer",
            user_id=cust_id
        )
        self.assertFalse(granted_after)
        self.assertIn("revoked", msg_after.lower())

    def test_03_wifi_proximity_restrictions(self):
        """Test Wi-Fi proximity matching: door only unlocks if connected to room Wi-Fi."""
        room_id = 2  # Room 102
        cust_id = 1
        res_id = 1

        # Mint active key
        key_info = mint_room_key(room_id, cust_id, res_id)

        # Attempt 1: Connected to wrong Wi-Fi (e.g. Lobby Wi-Fi)
        granted, msg, _ = verify_door_access(
            room_id=room_id,
            key_token=key_info["plain_key"],
            method="wifi",
            wifi_ssid="Quest_Lobby_Guest_WiFi",
            user_type="customer"
        )
        self.assertFalse(granted)
        self.assertIn("WiFi Mismatch", msg)

        # Attempt 2: Connected to matching room Wi-Fi (Quest_Room_102)
        granted, msg, details = verify_door_access(
            room_id=room_id,
            key_token=key_info["plain_key"],
            method="wifi",
            wifi_ssid="Quest_Room_102",
            user_type="customer"
        )
        self.assertTrue(granted, msg)
        self.assertEqual(details["door_state"], "unlocked")

    def test_04_nfc_proximity_tap(self):
        """Test NFC tap proximity: verifies key hash directly, ignores Wi-Fi."""
        room_id = 2  # Room 102
        cust_id = 1
        res_id = 1

        key_info = mint_room_key(room_id, cust_id, res_id)

        # NFC tap with valid key
        granted, msg, details = verify_door_access(
            room_id=room_id,
            key_token=key_info["plain_key"],
            method="nfc",
            wifi_ssid="",  # No Wi-Fi required for NFC
            user_type="customer"
        )
        self.assertTrue(granted, msg)
        self.assertEqual(details["door_state"], "unlocked")

        # NFC tap with fake key
        granted_fake, msg_fake, _ = verify_door_access(
            room_id=room_id,
            key_token="FAKE-UNAUTHORIZED-NFC-KEY",
            method="nfc",
            wifi_ssid="",
            user_type="unknown"
        )
        self.assertFalse(granted_fake)
        self.assertIn("denied", msg_fake.lower())

    def test_05_staff_super_key_master_access(self):
        """Test that staff super key can unlock rooms via Wi-Fi and NFC."""
        sk = get_daily_super_key()
        room_id = 2  # Room 102

        # 1. Staff unlock via Staff Wi-Fi
        granted, msg, details = verify_door_access(
            room_id=room_id,
            key_token=sk["plain_key"],
            method="wifi",
            wifi_ssid=STAFF_WIFI_SSID,
            user_type="staff",
            user_name="Eleanor Vance (Admin)"
        )
        self.assertTrue(granted, msg)
        self.assertEqual(details["key_type"], "super_key")

        # 2. Staff unlock via NFC
        granted_nfc, msg_nfc, details_nfc = verify_door_access(
            room_id=room_id,
            key_token=sk["plain_key"],
            method="nfc",
            user_type="staff",
            user_name="Sophia Laurent (Cashier)"
        )
        self.assertTrue(granted_nfc, msg_nfc)
        self.assertEqual(details_nfc["key_type"], "super_key")

    def test_06_audit_logging(self):
        """Test that all door access events are logged in door_access_logs."""
        logs = get_door_access_logs(limit=5)
        self.assertGreater(len(logs), 0)
        latest = logs[0]
        self.assertIn(latest["status"], ("granted", "denied"))
        self.assertIn(latest["method"], ("wifi", "nfc", "manual"))


if __name__ == "__main__":
    unittest.main()

"""Offline tests for the update loop (no network, no Discord).
Run with: python -m unittest discover tests"""

import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import check_update  # noqa: E402


class MainLoopTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_path = os.path.join(self.tmp.name, "version_data.json")
        self.version = "1.0"
        self.sent = []
        self.patches = [
            mock.patch.object(check_update, "STATE_FILE", self.state_path),
            mock.patch.object(check_update, "DISCORD_TOKEN", "token"),
            mock.patch.object(check_update, "CHANNEL_ID", "123"),
            mock.patch.object(check_update, "GAMES", [{
                "slug": "game", "name": "Game",
                "check": lambda: {"version": self.version, "release": self.version},
                "embed": lambda info: {"title": info["release"]},
            }]),
            mock.patch.object(check_update, "send_discord_embed", side_effect=self._send),
        ]
        for p in self.patches:
            p.start()
        self.send_ok = True

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def _send(self, embed):
        self.sent.append(embed)
        return self.send_ok

    def run_once(self):
        check_update.main()
        with open(self.state_path, encoding="utf-8") as f:
            return f.read()

    def test_first_run_seeds_without_notifying(self):
        state = json.loads(self.run_once())
        self.assertEqual(state["game"]["version"], "1.0")
        self.assertEqual(self.sent, [])

    def test_quiet_run_leaves_state_file_unchanged(self):
        first = self.run_once()
        second = self.run_once()
        self.assertEqual(first, second, "no version change must mean no diff (no commit)")
        self.assertEqual(self.sent, [])

    def test_new_version_notifies_and_updates_state(self):
        self.run_once()
        self.version = "1.1"
        state = json.loads(self.run_once())
        self.assertEqual([e["title"] for e in self.sent], ["1.1"])
        self.assertEqual(state["game"]["version"], "1.1")

    def test_failed_send_keeps_old_version_for_retry(self):
        self.run_once()
        self.version = "2.0"
        self.send_ok = False
        with self.assertRaises(SystemExit):
            check_update.main()
        with open(self.state_path, encoding="utf-8") as f:
            self.assertEqual(json.load(f)["game"]["version"], "1.0")


class Cs2CheckTests(unittest.TestCase):
    def test_picks_first_patchnotes_item(self):
        news = {"appnews": {"newsitems": [
            {"gid": "1", "title": "Event", "tags": ["event"]},
            {"gid": "2", "title": "Release Notes", "url": "u", "tags": ["patchnotes"]},
        ]}}
        with mock.patch.object(check_update, "fetch_json", return_value=news):
            self.assertEqual(check_update.cs2_check(),
                             {"version": "2", "title": "Release Notes", "url": "u"})


if __name__ == "__main__":
    unittest.main()

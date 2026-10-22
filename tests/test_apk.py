import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from package_apk import prepare


class ApkTests(unittest.TestCase):
    def test_plugin_manifest(self):
        root = ET.parse(ROOT / "android-plugin/AndroidManifest.xml").getroot()
        ns = "{http://schemas.android.com/apk/res/android}"
        app = root.find("application")
        self.assertEqual(app.get(ns + "hasCode"), "false")
        self.assertEqual(app.get(ns + "extractNativeLibs"), "true")
        metadata = {n.get(ns + "name"): n.get(ns + "value") for n in app.findall("meta-data")}
        self.assertEqual(metadata["zalithRendererPlugin"], "true")
        self.assertEqual(metadata["renderer"], "opengles3:libpowervr.so:libEGL.so")
        self.assertEqual(root.findall("uses-permission"), [])

    def test_universal_layout_and_hash_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            paths = []
            for abi, cls, machine in [("arm64-v8a", 2, 183), ("armeabi-v7a", 1, 40)]:
                data = bytearray(20)
                data[:6] = b"\x7fELF" + bytes([cls, 1])
                data[16:18] = (3).to_bytes(2, "little")
                data[18:20] = machine.to_bytes(2, "little")
                path = tmp / (abi + ".zip")
                with zipfile.ZipFile(path, "w") as archive:
                    archive.writestr("libpowervr.so", data)
                    archive.writestr("build.json", json.dumps({"abi": abi, "sha256": hashlib.sha256(data).hexdigest()}))
                    archive.writestr("corresponding-source.tar.gz", "mock source")
                paths.append(path)
            prepare(paths, tmp / "stage", tmp / "release")
            self.assertTrue((tmp / "stage/lib/arm64-v8a/libpowervr.so").exists())
            self.assertTrue((tmp / "stage/lib/armeabi-v7a/libpowervr.so").exists())
            self.assertEqual(len(list((tmp / "release").glob("*.zip"))), 2)
            with self.assertRaises(ValueError):
                prepare(paths[:1], tmp / "partial", tmp / "partial-release")
            with self.assertRaises(ValueError):
                prepare([paths[0], paths[0]], tmp / "duplicate", tmp / "duplicate-release")

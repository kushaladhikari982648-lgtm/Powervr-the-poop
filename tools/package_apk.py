#!/usr/bin/env python3
"""Build a signed ARM-universal, resource-only original-Zalith plugin APK."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import tempfile
import zipfile
from build import ROOT, ABIS, verify_elf


def prepare(build_zips, staging, release):
    staging, release = Path(staging), Path(release)
    staging.mkdir(parents=True, exist_ok=True)
    release.mkdir(parents=True, exist_ok=True)
    seen, provenance = set(), {}
    for filename in build_zips:
        with zipfile.ZipFile(filename) as archive:
            metadata = json.loads(archive.read("build.json"))
            abi = metadata["abi"]
            if abi not in ABIS or abi in seen:
                raise ValueError("Unexpected or duplicate ABI")
            seen.add(abi)
            data = archive.read("libpowervr.so")
            if hashlib.sha256(data).hexdigest() != metadata["sha256"]:
                raise ValueError("Native artifact hash mismatch")
            library = staging / "lib" / abi / "libpowervr.so"
            library.parent.mkdir(parents=True)
            library.write_bytes(data)
            verify_elf(library, abi)
            # Exact original archive includes modified corresponding source,
            # all upstream submodules, licenses, metadata and rebuild notes.
            if "corresponding-source.tar.gz" not in archive.namelist():
                raise ValueError("Missing modified corresponding source")
            shutil.copy2(filename, release / f"powervr-r2-{abi}-source-and-native.zip")
            provenance[abi] = metadata
    if seen != set(ABIS):
        raise ValueError("Universal ARM APK requires both ARM64 and ARMv7")
    assets = staging / "assets"
    shutil.copytree(ROOT / "licenses", assets / "licenses")
    (assets / "native-builds.json").write_text(json.dumps(provenance, indent=2) + "\n")
    shutil.copy2(ROOT / "docs/APK.md", assets / "README.txt")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-zip", action="append", required=True, type=Path)
    parser.add_argument("--sdk", default=os.environ.get("ANDROID_HOME"), type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/release")
    args = parser.parse_args()
    if not args.sdk:
        parser.error("Android SDK required")
    tools = args.sdk / "build-tools/35.0.0"
    android = args.sdk / "platforms/android-35/android.jar"
    def run(*command, **kwargs):
        subprocess.run([str(arg) for arg in command], check=True, **kwargs)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        staging = tmp / "staging"
        prepare(args.build_zip, staging, args.output)
        unsigned, aligned = tmp / "unsigned.apk", tmp / "aligned.apk"
        run(tools / "aapt", "package", "-f", "-M", ROOT / "android-plugin/AndroidManifest.xml",
            "-I", android, "-F", unsigned)
        with zipfile.ZipFile(unsigned, "a", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(staging.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(staging))
        run(tools / "zipalign", "-f", "-P", "16", "4", unsigned, aligned)
        # No signing secret is configured. This explicit one-release key never
        # enters Git/artifacts/logs; future releases require uninstall/reinstall.
        environment = dict(os.environ, APK_SIGNING_PASSWORD=secrets.token_urlsafe(32))
        keystore = tmp / "release.p12"
        run("keytool", "-genkeypair", "-keystore", keystore, "-storetype", "PKCS12",
            "-storepass:env", "APK_SIGNING_PASSWORD", "-alias", "powervr-experimental",
            "-keyalg", "RSA", "-keysize", "3072", "-validity", "3650",
            "-dname", "CN=PowerVR Unified Experimental", "-noprompt", env=environment)
        apk = args.output / "powervr-unified-r2-arm-universal.apk"
        run(tools / "apksigner", "sign", "--ks", keystore,
            "--ks-pass", "env:APK_SIGNING_PASSWORD", "--out", apk, aligned, env=environment)
        run(tools / "apksigner", "verify", "--verbose", "--print-certs", apk)
        run(tools / "zipalign", "-c", "-P", "16", "4", apk)
        run(tools / "aapt", "dump", "badging", apk)
        shutil.copy2(ROOT / "docs/APK.md", args.output / "README.txt")
        files = sorted(p for p in args.output.iterdir() if p.is_file() and p.name != "SHA256SUMS")
        (args.output / "SHA256SUMS").write_text("".join(
            f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in files))
        print(apk)


if __name__ == "__main__":
    main()

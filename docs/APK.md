# PowerVR Unified r2 — experimental original-Zalith plugin

One installable APK includes ARM64 (arm64-v8a) and ARMv7 (armeabi-v7a).
"ARM-universal" does NOT mean x86, every GPU, every launcher, or every Minecraft
version. It packages the same r2 native libraries previously built successfully
in Actions run 39445672159, commit 8ad4affab77acae64df40de7aac49af6a9d02295.
No new performance improvement over the r2 local-import ZIP is claimed.

## Install

1. Download powervr-unified-r2-arm-universal.apk from the GitHub prerelease.
2. Permit installation from your browser/file manager if Android prompts.
3. Install the APK, then fully close and reopen original Zalith Launcher.
4. Select the APK plugin named PowerVR Unified r2 (experimental) in renderer
   settings. Distinguish it from any previously locally imported copy.
5. Restart Minecraft. Revert to a working renderer if it crashes.

This APK is a native-library plugin, not a standalone app: it deliberately has
no launcher icon, game, UI, network permission, Java bytecode, or background service.
Android chooses the installed ABI; a mismatched 32-bit JVM on a 64-bit installation
may need the existing architecture-specific local-import ZIP instead.
Requires actual GLES 3 support. Intended for original Zalith's APK-plugin metadata
contract; Zalith 2, stock Pojav and other forks are not certified compatible.

## Signing and updates

Signed with a freshly generated experimental release key, checked by apksigner.
No persistent signing secret was available, and the private key is not published.
A future separately signed release will require uninstalling this plugin first;
this does not uninstall Zalith or its Minecraft data. Do not expect in-place APK
updates. Fingerprint verification is in the packaging job logs, and SHA256SUMS
is included with the release. This signature proves package integrity, not safety
or Android gameplay compatibility. No claim of reproducible APK bytes is made.

## Source and licenses

The two *-source-and-native.zip release assets contain complete modified
corresponding source, bundled dependencies, licenses and native build metadata.
Rebuild instructions are in their README.md and docs/UNIFIED.md in this repo.
APK build recipe: tools/package_apk.py and android-plugin/AndroidManifest.xml.
Our tooling is MIT; the LTW-derived module is LGPL-3.0-only and other code retains
its upstream licenses. Preserve source/notices and permit renderer replacement.

## Performance status

An earlier build loaded successfully for one user on GE8300, but Minecraft 1.20.1
was reported around an unstable 25 FPS. r2 removes repeated indirect-multidraw
extension discovery; no measured on-device FPS improvement has been established.
See docs/GE8300.md. This is an experimental prerelease, not a universal speed fix.

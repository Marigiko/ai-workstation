"""Cross-platform validation: verify platform-specific code is properly guarded."""



def test_menu_objc2_guarded():
    """menu.rs must gate objc2-app-kit code behind macos cfg."""
    menu_path = "/mnt/e/Projects/terax-ai/src-tauri/src/menu.rs"
    with open(menu_path) as f:
        content = f.read()
    assert '#[cfg(target_os = "macos")]' in content, "Missing macOS guard in menu.rs"
    assert "#[cfg(not(target_os = \"macos\"))]" in content, "Missing non-macOS guard in menu.rs"


def test_voice_macos_guarded():
    """voice.rs must gate NSEvent code behind macos cfg with non-macOS no-op."""
    voice_path = "/mnt/e/Projects/terax-ai/src-tauri/src/modules/voice.rs"
    with open(voice_path) as f:
        content = f.read()
    assert '#[cfg(target_os = "macos")]' in content, "Missing macOS guard in voice.rs"
    assert "#[cfg(not(target_os = \"macos\"))]" in content, "Missing non-macOS no-op in voice.rs"


def test_claude_code_no_platform_specific():
    """claude_code.rs is pure std (no platform-specific deps)."""
    cc_path = "/mnt/e/Projects/terax-ai/src-tauri/src/modules/claude_code.rs"
    with open(cc_path) as f:
        content = f.read()
    # Should compile on all platforms — no objc2 or platform-specific imports
    assert "objc2" not in content.lower(), "claude_code.rs should not use objc2"


def test_cargo_toml_objc2_macos_only():
    """Cargo.toml must gate objc2-app-kit behind target_os = macos."""
    cargo_path = "/mnt/e/Projects/terax-ai/src-tauri/Cargo.toml"
    with open(cargo_path) as f:
        content = f.read()
    # Find objc2-app-kit line and verify it's in a target cfg block
    lines = content.split("\n")
    in_macos_target = False
    objc2_app_kit_guarded = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[target.") and 'macos"' in stripped:
            in_macos_target = True
            continue
        if stripped.startswith("[target.") and in_macos_target:
            in_macos_target = False
        if "objc2-app-kit" in stripped:
            if in_macos_target or "cfg(" in stripped or "target" in stripped:
                objc2_app_kit_guarded = True
    assert objc2_app_kit_guarded, "objc2-app-kit must be gated behind macOS target"

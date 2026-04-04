"""Vietnamese IME patch for Claude Code CLI."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

PATCH_MARKER = "/* Vietnamese IME fix */"

# DEL char (0x7F) used by Vietnamese IMEs
_DEL = "\x7f"


def _find_cli_js() -> Path | None:
    """Find Claude Code's cli.js file."""
    claude_bin = shutil.which("claude")
    if not claude_bin:
        return None
    cli_path = Path(claude_bin).resolve()
    if cli_path.suffix == ".js":
        return cli_path
    # Check if it's a symlink to cli.js
    try:
        target = Path(claude_bin).resolve()
        if target.suffix == ".js":
            return target
    except OSError:
        pass
    return None


def is_patched() -> bool:
    """Check if Claude Code is already patched for Vietnamese IME."""
    cli_js = _find_cli_js()
    if not cli_js:
        return False
    try:
        content = cli_js.read_text(encoding="utf-8")
        return PATCH_MARKER in content
    except OSError:
        return False


def apply_patch() -> tuple[bool, str]:
    """Apply Vietnamese IME patch to Claude Code's cli.js.

    Returns (success, message).
    """
    cli_js = _find_cli_js()
    if not cli_js:
        return False, "Claude Code cli.js not found"

    try:
        content = cli_js.read_text(encoding="utf-8")
    except OSError as e:
        return False, f"Cannot read cli.js: {e}"

    if PATCH_MARKER in content:
        return True, "Already patched"

    # Find the block: if(!key.backspace&&!key.delete&&input.includes("\x7f"))
    # The actual DEL byte is embedded in the .includes() call
    includes_pattern = f'.includes("{_DEL}")'
    pos = content.find(includes_pattern)
    if pos == -1:
        # Try with \b (backspace)
        includes_pattern = '.includes("\\b")'
        pos = content.find(includes_pattern)
    if pos == -1:
        return False, "Cannot find IME input handler pattern in cli.js"

    # Scan backward to find "if(!" start of block
    block_start = content.rfind("if(!", 0, pos)
    if block_start == -1:
        return False, "Cannot find block start"

    # Scan forward from block_start to find matching closing brace
    brace_count = 0
    i = block_start
    block_end = -1
    found_first_brace = False
    while i < len(content):
        if content[i] == "{":
            brace_count += 1
            found_first_brace = True
        elif content[i] == "}":
            brace_count -= 1
            if found_first_brace and brace_count == 0:
                block_end = i + 1  # include closing }
                break
        i += 1

    if block_end == -1:
        return False, "Cannot find block end"

    original_block = content[block_start:block_end]

    # Extract variable names from the block
    key_var_m = re.search(r"if\(!([a-zA-Z0-9_$]+)\.backspace", original_block)
    input_var_m = re.search(r"([a-zA-Z0-9_$]+)\.includes\(", original_block)
    cursor_var_m = re.search(r",([a-zA-Z0-9_$]+)=([a-zA-Z0-9_$]+);for", original_block)
    text_func_m = re.search(r"\.text!==\w+\.text\)([a-zA-Z0-9_$]+)\(", original_block)
    offset_func_m = re.search(r"\.text\);([a-zA-Z0-9_$]+)\(\w+\.offset\)", original_block)
    callbacks_m = re.search(r"([a-zA-Z0-9_$]+)\(\),([a-zA-Z0-9_$]+)\(\);return", original_block)

    if not all([key_var_m, input_var_m, cursor_var_m, text_func_m, offset_func_m, callbacks_m]):
        return False, "Cannot extract variable names from block"

    key_var = key_var_m.group(1)  # type: ignore[union-attr]
    input_var = input_var_m.group(1)  # type: ignore[union-attr]
    cursor_var = cursor_var_m.group(2)  # type: ignore[union-attr]
    text_func = text_func_m.group(1)  # type: ignore[union-attr]
    offset_func = offset_func_m.group(1)  # type: ignore[union-attr]
    cb1 = callbacks_m.group(1)  # type: ignore[union-attr]
    cb2 = callbacks_m.group(2)  # type: ignore[union-attr]

    # Build replacement
    replacement = (
        f"if(!{key_var}.backspace&&!{key_var}.delete&&"
        f'({input_var}.includes("\\x7f")||{input_var}.includes("\\x08")))'
        f"{{{PATCH_MARKER}"
        f"let _v={cursor_var};"
        f"for(let _i=0;_i<{input_var}.length;_i++){{"
        f"let _c={input_var}.charCodeAt(_i);"
        f"if(_c===127||_c===8){{_v=_v.deleteTokenBefore?.()??_v.backspace()}}"
        f"else{{_v=_v.insert({input_var}[_i])}}}}"
        f"if(!{cursor_var}.equals(_v)){{"
        f"if({cursor_var}.text!==_v.text){text_func}(_v.text);"
        f"{offset_func}(_v.offset)}}"
        f"{cb1}(),{cb2}();return}}"
    )

    # Create backup
    backup_path = cli_js.with_suffix(".js.bak")
    try:
        if not backup_path.exists():
            cli_js.rename(backup_path)
            backup_path.rename(cli_js)  # restore original name
            import shutil as sh

            sh.copy2(cli_js, backup_path)
    except OSError:
        pass  # backup is best-effort

    # Apply patch
    patched = content[:block_start] + replacement + content[block_end:]
    try:
        cli_js.write_text(patched, encoding="utf-8")
        return True, f"Patched {cli_js}"
    except PermissionError:
        return False, "Permission denied — try: sudo ccc account patch-ime"
    except OSError as e:
        return False, f"Write failed: {e}"

"""Optional request-flow breakpoints for learning.

Enable with environment variable:
  CAREPLAN_DEBUG_BREAKPOINTS=1

Then run under a debugger (Cursor/VS Code F5, or pdb).
When disabled, these calls are no-ops.
"""

import os


def debug_break(label, **watch):
    if os.environ.get("CAREPLAN_DEBUG_BREAKPOINTS") != "1":
        return

    print(f"\n{'=' * 60}")
    print(f"BREAKPOINT: {label}")
    for name, value in watch.items():
        preview = repr(value)
        if len(preview) > 400:
            preview = preview[:400] + "..."
        print(f"  {name}: {preview}")
    print("=" * 60)
    breakpoint()

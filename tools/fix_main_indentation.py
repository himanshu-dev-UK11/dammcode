#!/usr/bin/env python3
"""
Quick fix script to properly indent the heavy initialization block in main.py

This script indents all code between "if not OPTIMIZED_STARTUP:" and "# ── Shutdown"
to complete the optimization integration.

Usage:
    python tools/fix_main_indentation.py

This will:
1. Backup main.py to main.py.before_indent_fix
2. Fix the indentation
3. Verify the syntax
"""

import sys
from pathlib import Path

def fix_indentation():
    """Fix the indentation in main.py"""
    
    project_root = Path(__file__).parent.parent
    main_py = project_root / "main.py"
    backup_py = project_root / "main.py.before_indent_fix"
    
    print("=" * 70)
    print("main.py Indentation Fix Tool")
    print("=" * 70)
    
    if not main_py.exists():
        print(f"❌ Error: {main_py} not found!")
        return False
    
    # Backup
    print(f"\n📋 Creating backup: {backup_py.name}")
    with open(main_py, 'r') as f:
        content = f.read()
    with open(backup_py, 'w') as f:
        f.write(content)
    print("✅ Backup created")
    
    # Read lines
    with open(main_py, 'r') as f:
        lines = f.readlines()
    
    # Find the block boundaries
    start_line = None
    end_line = None
    
    for i, line in enumerate(lines):
        # Look for the start marker
        if 'if not OPTIMIZED_STARTUP:' in line and i > 330:  # Around line 340
            # Check if next few lines need indentation
            if i + 1 < len(lines) and not lines[i + 1].startswith('        '):
                start_line = i + 1
                print(f"\n🔍 Found start of block at line {start_line + 1}")
        
        # Look for the end marker
        if start_line and '# ── Shutdown' in line and line.strip().startswith('#'):
            end_line = i
            print(f"🔍 Found end of block at line {end_line + 1}")
            break
    
    if not start_line or not end_line:
        print(f"\n❌ Could not find block boundaries")
        print(f"   Start: {start_line}, End: {end_line}")
        return False
    
    print(f"\n📝 Will indent {end_line - start_line} lines")
    
    # Indent the block
    fixed_lines = lines[:start_line]
    
    for i in range(start_line, end_line):
        line = lines[i]
        # Skip empty lines and already properly indented lines
        if line.strip() == '':
            fixed_lines.append(line)
        elif line.startswith('        '):  # Already indented by 8+ spaces
            fixed_lines.append(line)
        else:
            # Add 4 spaces of indentation
            fixed_lines.append('    ' + line)
    
    fixed_lines.extend(lines[end_line:])
    
    # Write fixed version
    print(f"\n💾 Writing fixed version...")
    with open(main_py, 'w') as f:
        f.writelines(fixed_lines)
    
    print("✅ Indentation fixed!")
    
    # Verify syntax
    print(f"\n🔍 Verifying Python syntax...")
    try:
        import py_compile
        py_compile.compile(str(main_py), doraise=True)
        print("✅ Syntax is valid!")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ Syntax error detected:")
        print(f"   {e}")
        print(f"\n⚠️  Restoring backup...")
        with open(backup_py, 'r') as f:
            content = f.read()
        with open(main_py, 'w') as f:
            f.write(content)
        print("✅ Backup restored")
        return False

def main():
    print("\nThis script will fix the indentation in main.py to enable")
    print("the optimized startup mode.\n")
    
    response = input("Proceed with fix? [Y/n]: ").strip().lower()
    if response and response != 'y':
        print("\n❌ Cancelled")
        return
    
    success = fix_indentation()
    
    if success:
        print("\n" + "=" * 70)
        print("✅ SUCCESS!")
        print("=" * 70)
        print("\nThe optimization is now fully integrated.")
        print("\nYou can now run:")
        print("  python main.py                    # Optimized mode (fast)")
        print("  OPTIMIZED_STARTUP=false python main.py  # Legacy mode")
        print("\nBackup saved as: main.py.before_indent_fix")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("❌ FIX FAILED")
        print("=" * 70)
        print("\nThe original main.py has been restored from backup.")
        print("You can try manual indentation instead.")
        print("=" * 70)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Install Android Tool

## What gets installed
- `.shared/commands/android.md`
- `.shared/scripts/android-shell-pull-fallback.sh`
- optional thin wrappers for Codex / Claude / Antigravity

## Install
```bash
python3 install-tool.py install android -p <path>
python3 install-tool.py -i android -p <path>
```

## Uninstall
```bash
python3 install-tool.py uninstall android -p <path>
python3 install-tool.py -u android -p <path>
```

## After install
- prepare device/emulator and `adb`
- use `/android init`
- verify fallback evidence path under `.tmp/android-test/`

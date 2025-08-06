# Monster Tool Auto-Update Server

This repository hosts the auto-update files for the Monster Soul Retrieval Tool.

## Files:
- `version.json` - Contains version information and changelog
- `monster_tooltest.py` - Latest version of the application

## How it works:
1. The Monster Tool checks this repository for updates
2. If a newer version is available, it downloads the updated Python file
3. The app automatically restarts with the new version

## For developers:
To release a new version:
1. Update the Python file with your changes
2. Update `version.json` with the new version number and changelog
3. Commit and push the changes

The GitHub Pages URL will be: `https://YOUR-USERNAME.github.io/monster-tool-updates/`

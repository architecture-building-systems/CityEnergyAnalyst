# How to set up NSIS

This guide shows you how to set up your environment to build the CEA Windows installer.

The installer is built with [NSIS](https://nsis.sourceforge.io/Main_Page) (Nullsoft Scriptable Install System). Download the latest stable release (3.x) from the NSIS site and install it with the default settings.

## Required plugins

The CEA ships its Python environment as a `.7z` archive and uses the `Nsis7z` plugin to extract it (see `setup/cityenergyanalyst.nsi:174`). Without it the installer fails with:

```
Plugin not found, cannot call Nsis7z::ExtractWithDetails
```

Install both plugins by extracting them into the NSIS installation folder (typically `C:\Program Files (x86)\NSIS`):

- [`NSIS7z` plugin](https://nsis.sourceforge.io/Nsis7z_plug-in) — 7-Zip archive extraction
- [`Inetc` plugin](https://nsis.sourceforge.io/Inetc_plug-in) — HTTP downloads (used to fetch the VC++ redistributable)

## Compiling the installer

Right-click `setup/cityenergyanalyst.nsi` in Windows Explorer and choose **Compile NSIS Script**.

If you get `Can't open output file`, create the `setup/Output/` folder manually and retry.

> ℹ️ Installer scripts that read `$%CEA_VERSION%` (an environment variable) expect that env var to be set in the shell before compilation. The CI workflows in `.github/workflows/` set this automatically; for local builds, set it yourself before invoking the compile.

Privacy
=======

Installer telemetry
--------------------

Official Windows installer builds of the City Energy Analyst send a small
amount of anonymous, aggregate telemetry (for example: install outcome, CEA
version, and coarse location derived from the network connection at install
time). This is used only to help us understand and fix problems with the
installer itself.

No personal details — your name, email, account, files, or anything else
that identifies you — are collected. Nothing is linked back to you, shared
with third parties, or used to profile or track individual users.

No telemetry is sent when running the CEA application itself, only during
installation. Builds from source, or forks that do not embed a telemetry
key, send no telemetry at all.

CEA Desktop (the app the installer sets up) also reports its own anonymous
install/update outcome and a short internal code identifying which step
failed, if any, using the same principles above. This covers installs and
updates the main installer above never sees, such as an in-app update or a
standalone download of CEA Desktop. Separately, CEA Desktop keeps a local
log of its own install/update steps on your machine, at
``%APPDATA%\CEA-4 Desktop\logs\installer.log`` - this file is never uploaded
automatically; it stays on your machine unless you choose to attach it to a
bug report.

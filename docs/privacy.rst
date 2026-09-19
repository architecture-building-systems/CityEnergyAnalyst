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
with third parties, or used to profile or track individual users. Every
event is sent with a fresh, random, one-time identifier that is never
stored anywhere and never reused — events cannot be linked to each other,
to a specific machine, or to you, and we cannot tell whether two events
came from the same install or two different ones.

A small amount of local, never-transmitted bookkeeping (a retry count, and
whether an installation had previously completed) lets telemetry
distinguish "many separate one-off failures" from "one install stuck
retrying the same step", and report roughly how long an installation had
been in place if it's removed. This bookkeeping never leaves your machine
and is deleted on success or removal — only the derived counts/buckets are
ever sent as part of an already-anonymous event.

No telemetry is sent when running the CEA application itself, only during
installation and removal. Builds from source, or forks that do not embed a
telemetry key, send no telemetry at all.

CEA Desktop (the app the installer sets up) also reports its own anonymous
install/update outcome and a short internal code identifying which step
failed, if any, using the same principles above. This covers installs and
updates the main installer above never sees, such as an in-app update or a
standalone download of CEA Desktop. Separately, CEA Desktop keeps a local
log of its own install/update steps on your machine, at
``%APPDATA%\CEA-4 Desktop\logs\installer.log`` - this file is never uploaded
automatically; it stays on your machine unless you choose to attach it to a
bug report.

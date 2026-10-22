Privacy
=======

Installer telemetry
--------------------

Official Windows installer builds of the City Energy Analyst send a small
amount of anonymous telemetry (for example: install outcome, CEA version, the
installer step that failed, and a coarse, country-level location). This is
used only to help us understand and fix problems with the installer itself.

No personal details — your name, email, account, files, or anything else
that identifies you — are collected, and events are not used to profile or
track individual users.

Events are sent to `PostHog <https://posthog.com>`_ (EU Cloud), a third-party
analytics service that we use to receive and store them. As with any network
request, PostHog receives your IP address along with each event. It uses it
only to work out a coarse, country-level location, and our PostHog project is
configured to discard the IP address rather than store it with the event.

Every event is sent with a fresh, random, one-time identifier that is never
stored anywhere or reused, so events are not linked to a user or account. The
retry information described below is the only thing that lets us tell that
repeated failures may come from the same installation attempt.

A small amount of local, never-transmitted bookkeeping (a retry count, and
whether an installation had previously completed) lets telemetry
distinguish "many separate one-off failures" from "one install stuck
retrying the same step", and report roughly how long an installation had
been in place if it's removed. This bookkeeping is stored only on your
machine and is deleted on success or removal — only the derived
counts/buckets are sent, as part of an already-anonymous event.

Builds from source, or forks that do not embed a telemetry key, send no
telemetry at all.

CEA Desktop (the app the installer sets up) also reports its own anonymous
install/update outcome and a short internal code identifying which step
failed, if any, using the same principles above. This covers installs and
updates the main installer above never sees, such as an in-app update or a
standalone download of CEA Desktop. Separately, CEA Desktop keeps a local
log of its own install/update steps on your machine, at
``%APPDATA%\CEA-4 Desktop\logs\installer.log``. This file is never uploaded;
when an install fails, only the name of the last step it reached (one of a
fixed list, such as ``extracted``) is included in the telemetry event. The
file stays on your machine unless you choose to attach it to a bug report.

Application error reporting
---------------------------

Official CEA Desktop builds also report anonymous error and job-outcome
events while the application is running, to help us find and fix crashes and
failing tools:

* ``ui_error``: sent when the user interface hits an unexpected error. It
  contains diagnostic information about the error, not your data.
* ``job_finished``: sent when a tool finishes. It contains the tool name,
  whether it succeeded, failed or was cancelled, how long it ran, and the
  platform. For a failed job only the exception class (for example
  ``ValueError``) is sent, never the error message.
* ``app_startup_failed``: sent when CEA Desktop cannot start, for example if
  the CEA environment cannot be set up or the CEA backend exits or does not
  respond. It contains a fixed step name (such as ``env_create`` or
  ``backend_exit``), an exit code or error class name, the CEA version, and
  the operating system and architecture. Error messages, logs and file paths
  are never sent.

These events carry no project, scenario, file, parameter or user
information. They are sent to the same PostHog project described above, with
cookies and local storage disabled, so no identifier is stored on your
machine and events cannot be linked to a person. Autocapture, session
recording and page-view tracking are turned off.

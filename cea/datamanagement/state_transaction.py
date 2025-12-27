import os
from dataclasses import dataclass, field

from cea.datamanagement.database.assemblies import Envelope
from cea.inputlocator import InputLocator


@dataclass
class FileSnapshot:
    """Snapshot and restore a set of files.

    Stores file bytes for existing files and remembers which paths did not exist.
    """

    _files: dict[str, bytes | None] = field(default_factory=dict)

    def capture(self, paths: list[str]) -> None:
        for path in paths:
            if path in self._files:
                continue
            if os.path.exists(path) and os.path.isfile(path):
                with open(path, "rb") as f:
                    self._files[path] = f.read()
            else:
                self._files[path] = None

    def capture_tree(self, root: str) -> None:
        if not os.path.exists(root):
            # Track non-existent root so restore can delete it if it gets created.
            self._files.setdefault(root, None)
            return

        for current_root, _, filenames in os.walk(root):
            for filename in filenames:
                self.capture([os.path.join(current_root, filename)])

    def restore(self) -> None:
        # Restore files and remove newly created ones.
        for path, content in self._files.items():
            if content is None:
                if os.path.exists(path):
                    if os.path.isdir(path):
                        # Only remove empty dirs we tracked explicitly.
                        try:
                            os.rmdir(path)
                        except OSError:
                            pass
                    else:
                        os.remove(path)
                continue
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(content)


def snapshot_state_year_files(locator: InputLocator) -> FileSnapshot:
    """Snapshot files commonly modified by district timeline state operations."""
    snapshot = FileSnapshot()

    # Building-properties (envelope, hvac, comfort, internal loads, supply, schedules)
    snapshot.capture_tree(locator.get_building_properties_folder())

    # Archetype construction mapping (the per-archetype type_* codes)
    snapshot.capture([locator.get_database_archetypes_construction_type()])

    # Envelope assemblies databases
    for method_name in Envelope._locator_mapping().values():
        snapshot.capture([getattr(locator, method_name)()])

    return snapshot

"""Establish test storage before collection imports any backend database module."""

import os
import tempfile

# Module-level test_api setup is too late when alphabetically earlier tests import db.
# Always use a fresh directory, even if the caller inherited a production LAB_STORAGE.
_TEST_STORAGE = tempfile.TemporaryDirectory(prefix="lab-backend-isolated-")
os.environ["LAB_STORAGE"] = _TEST_STORAGE.name

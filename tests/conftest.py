
from copy import deepcopy
import json
import os

import pytest


_SAMPLE_STATUS = {
    "User": {
        "Email": "user@example.com",
        "Fullname": "Example User",
        "Hostname": "workstation",
        "AccountInfo": {
            "Capacity": 1_000_000,
            "Usage": 250_000,
            "SubscriptionNameLocalized": "Personal",
        },
    },
    "Sync": {
        "Enabled": True,
        "RootPath": "/home/user/Jotta",
        "Count": {"Files": 12, "Bytes": 1_000},
        "RemoteCount": {"Files": 14, "Bytes": 1_200},
        "FolderCount": 3,
    },
    "Backup": {
        "State": {
            "Enabled": {
                "Backups": [
                    {
                        "Name": "Documents",
                        "Path": "/home/user/Documents",
                        "Count": {"Files": 5, "Bytes": 500},
                        "DeviceID": "device-1",
                        "LastUpdateMS": 100,
                        "LastScanStartedMS": 90,
                        "NextBackupMS": 200,
                    }
                ]
            }
        }
    },
}


@pytest.fixture
def status_payload() -> dict:
    return deepcopy(_SAMPLE_STATUS)


@pytest.fixture
def status_output(status_payload: dict) -> str:
    return json.dumps(status_payload)


@pytest.fixture
def qt_app():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    widgets = pytest.importorskip("PySide6.QtWidgets")
    app = widgets.QApplication.instance() or widgets.QApplication([])
    yield app

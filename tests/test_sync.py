import pytest
from stdapi import sync


def test_sync_tools_hash():
    res = sync.tools.hash("test sync", algo="md5")
    assert res.algorithm == "md5"
    assert res.digest is not None


def test_sync_tools_uuid_and_password():
    u = sync.tools.uuid()
    pwd = sync.tools.password(length=12)
    assert len(u) == 36
    assert len(pwd) == 12


def test_sync_nsfw_text():
    res = sync.nsfw.check_text("Safe educational sentence about coding.")
    assert res.is_toxic is False

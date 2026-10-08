import pytest
from stdapi.results import Result


def test_result_dot_access():
    data = {
        "title": "Amazing Video",
        "nested": {"author": "STD-DEEPANSHU", "stats": {"views": 1000}},
        "streams": [{"name": "stream1"}, {"name": "stream2"}]
    }
    res = Result(data)

    assert res.title == "Amazing Video"
    assert res.nested.author == "STD-DEEPANSHU"
    assert res.nested.stats.views == 1000
    assert res.streams[0].name == "stream1"
    assert res.streams[1].name == "stream2"


def test_result_dict_methods():
    res = Result({"key": "val"})
    assert res.get("key") == "val"
    assert res.get("missing", "default") == "default"
    assert "key" in res
    assert len(list(res.items())) == 1


def test_result_serialization():
    data = {"name": "test", "active": True}
    res = Result(data)
    d = res.to_dict()
    assert isinstance(d, dict)
    assert not isinstance(d, Result)
    assert d == data

    j = res.to_json()
    assert '"name": "test"' in j

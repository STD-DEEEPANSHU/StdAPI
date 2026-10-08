"""
StdAPI Dynamic Dot-Accessible Result Schema
Allows accessing dictionary keys as attributes (res.title, res.download_url)
with recursive nesting and clean string representation.
"""
import json
from typing import Any, Dict, List, Optional


class Result(dict):
    """
    A smart dictionary that supports dot notation access (e.g. res.title),
    safe item retrieval (.get), and JSON serialization.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, value in list(self.items()):
            if isinstance(value, dict) and not isinstance(value, Result):
                self[key] = Result(value)
            elif isinstance(value, list):
                self[key] = [Result(v) if isinstance(v, dict) and not isinstance(v, Result) else v for v in value]

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'Result' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        if isinstance(value, dict) and not isinstance(value, Result):
            value = Result(value)
        elif isinstance(value, list):
            value = [Result(v) if isinstance(v, dict) and not isinstance(v, Result) else v for v in value]
        self[name] = value

    def __delattr__(self, name: str) -> None:
        try:
            del self[name]
        except KeyError:
            raise AttributeError(f"'Result' object has no attribute '{name}'")

    def to_dict(self) -> Dict[str, Any]:
        """Convert Result object recursively to a standard Python dictionary."""
        out = {}
        for k, v in self.items():
            if isinstance(v, Result):
                out[k] = v.to_dict()
            elif isinstance(v, list):
                out[k] = [item.to_dict() if isinstance(item, Result) else item for item in v]
            else:
                out[k] = v
        return out

    def to_json(self, indent: int = 2) -> str:
        """Convert Result object to formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def __repr__(self) -> str:
        items_str = ", ".join(f"{k}={repr(v)}" for k, v in list(self.items())[:6])
        if len(self) > 6:
            items_str += ", ..."
        return f"Result({items_str})"

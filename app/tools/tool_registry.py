from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class ToolSpec:
    name: str
    description: str
    args_schema: dict[str, Any]
    function: Callable[..., Any]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        self._tools[spec.name] = spec

    def get(self, name: str) -> ToolSpec:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name]

    def list(self) -> list[dict[str, Any]]:
        return [
            {
                "name": spec.name,
                "description": spec.description,
                "args_schema": spec.args_schema,
            }
            for spec in self._tools.values()
        ]

    def call(self, name: str, **kwargs: Any) -> Any:
        return self.get(name).function(**kwargs)


registry = ToolRegistry()


def register_tool(name: str, description: str, args_schema: dict[str, Any]):
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        registry.register(ToolSpec(name, description, args_schema, func))
        return func

    return decorator

from dataclasses import InitVar, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class FlatMapEntry:
    """Represents a single entry in a flattened map with its metadata"""

    key: str
    original_key: str
    data: Dict[str, Any]
    parent_key: Optional[str] = None
    ancestors: List[str] = field(default_factory=list)
    depth: int = 0
    has_children: bool = False
    nested_keys: List[str] = field(default_factory=list)

    @property
    def is_root(self) -> bool:
        """Check if this is a root level entry"""
        return self.parent_key is None

    @property
    def clean_data(self) -> Dict[str, Any]:
        """Return the data without any nested map keys"""
        return {k: v for k, v in self.data.items() if k not in self.nested_keys}


@dataclass
class FlatMapContainer:
    """Container for flattened map data with metadata tracking"""

    source_map: InitVar[Dict[str, Any]]
    delimiter: str = "_"
    use_parent_in_child_keys: bool = False
    use_all_ancestors_in_child_keys: bool = False

    # These get populated during __post_init__
    entries: Dict[str, FlatMapEntry] = field(default_factory=dict, init=False)
    max_depth: int = field(default=0, init=False)

    def __post_init__(self, source_map: Dict[str, Any]):
        """Initialize the flattened map from source data"""
        if self.use_all_ancestors_in_child_keys:
            self.use_parent_in_child_keys = True

        self.entries = self._flatten_recursive(source_map)
        self.max_depth = max((entry.depth for entry in self.entries.values()), default=0)

    def _find_nested_maps(self, data: Dict[str, Any]) -> List[str]:
        """Find all keys in data that contain nested map structures"""
        nested_keys = []
        for key, value in data.items():
            if isinstance(value, dict) and len(value) > 0:
                # Check if this looks like a nested map structure
                dict_count = sum(1 for v in value.values() if isinstance(v, dict))
                if dict_count > 0:
                    nested_keys.append(key)
        return nested_keys

    def _flatten_recursive(
        self, data: Dict[str, Any], parent_key: str = "", ancestors: Optional[List[str]] = None
    ) -> Dict[str, FlatMapEntry]:
        """Recursively flatten the nested structure"""
        if ancestors is None:
            ancestors = []

        flattened = {}

        for key, value in data.items():
            if not isinstance(value, dict):
                continue

            # Determine the new key based on options
            if self.use_all_ancestors_in_child_keys and ancestors:
                new_key = self.delimiter.join(ancestors + [key])
            elif self.use_parent_in_child_keys and parent_key:
                new_key = f"{parent_key}{self.delimiter}{key}"
            else:
                new_key = key

            # Auto-detect nested map keys
            nested_map_keys = self._find_nested_maps(value)

            # Create the entry with metadata separate from data
            entry = FlatMapEntry(
                key=new_key,
                original_key=key,
                data=value,
                parent_key=parent_key if parent_key else None,
                ancestors=ancestors.copy(),
                depth=len(ancestors),
                has_children=len(nested_map_keys) > 0,
                nested_keys=nested_map_keys,
            )

            flattened[new_key] = entry

            # Recursively process all detected nested maps
            for nested_key in nested_map_keys:
                nested_data = value[nested_key]
                if isinstance(nested_data, dict) and len(nested_data) > 0:
                    # For ancestors, track original keys to prevent duplication
                    if self.use_all_ancestors_in_child_keys:
                        new_ancestors = ancestors + [key]
                    else:
                        new_ancestors = ancestors + [new_key]

                    child_flattened = self._flatten_recursive(nested_data, new_key, new_ancestors)
                    flattened.update(child_flattened)

        return flattened

    @property
    def flattened_data(self) -> Dict[str, Dict[str, Any]]:
        """Return the clean flattened data without metadata"""
        return {key: entry.clean_data for key, entry in self.entries.items()}

    @property
    def root_entries(self) -> Dict[str, FlatMapEntry]:
        """Return only root level entries"""
        return {key: entry for key, entry in self.entries.items() if entry.is_root}

    @property
    def child_entries(self) -> Dict[str, FlatMapEntry]:
        """Return only child entries (non-root)"""
        return {key: entry for key, entry in self.entries.items() if not entry.is_root}

    def entries_at_depth(self, depth: int) -> Dict[str, FlatMapEntry]:
        """Return entries at a specific depth"""
        return {key: entry for key, entry in self.entries.items() if entry.depth == depth}

    def get_children(self, parent_key: str) -> Dict[str, FlatMapEntry]:
        """Get direct children of a specific parent"""
        return {key: entry for key, entry in self.entries.items() if entry.parent_key == parent_key}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation for debugging"""
        return {
            "flattened_data": self.flattened_data,
            "metadata": {
                "max_depth": self.max_depth,
                "total_entries": len(self.entries),
                "root_count": len(self.root_entries),
                "child_count": len(self.child_entries),
                "entries_by_depth": {depth: len(self.entries_at_depth(depth)) for depth in range(self.max_depth + 1)},
            },
        }

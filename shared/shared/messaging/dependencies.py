# shared/messaging/dependencies.py
from typing import Any, Dict, Literal, get_args

# Define all valid dependency keys across the platform
DepKeys = Literal[
    "credit_service",
    "credit_transaction_service", 
    "notification_service",
    "logger",
    # Test-only keys
    "test_service",
]

class ServiceDependencies:
    """Service-scoped dependency container with typed key constraints"""
    
    def __init__(self):
        self._deps: Dict[str, Any] = {}
    
    def register(self, key: DepKeys, instance: Any) -> None:
        """Register a dependency - prevents accidental shadowing"""
        if key in self._deps:
            raise RuntimeError(f"Dependency '{key}' already registered")
        self._deps[key] = instance
    
    def get(self, key: DepKeys) -> Any:
        """Get a dependency with type-constrained keys"""
        if key not in self._deps:
            available = list(self._deps.keys())
            raise KeyError(
                f"Dependency '{key}' not registered. Available: {available}"
            )
        return self._deps[key]
    
    def has(self, key: DepKeys) -> bool:
        """Check if dependency is registered"""
        return key in self._deps
    
    def clear(self) -> None:
        """Clear all dependencies (for testing)"""
        self._deps.clear()
        
    def register_many(self, **kwargs) -> None:
        """Bulk register dependencies for cleaner lifecycle code"""
        for key, instance in kwargs.items():
            if key not in get_args(DepKeys):
                raise ValueError(f"Invalid dependency key: {key}")
            self.register(key, instance)
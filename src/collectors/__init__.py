"""Collectors package for cloud infrastructure compliance scanning."""

from src.collectors.azure_collector import AzureCollector
from src.collectors.base_collector import BaseCollector

__all__ = ["AzureCollector", "BaseCollector"]

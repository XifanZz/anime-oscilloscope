"""External metadata and rating source connectors."""

from anime_oscilloscope.connectors.bangumi import BangumiConnector
from anime_oscilloscope.connectors.base import SourceConnector

__all__ = ["BangumiConnector", "SourceConnector"]

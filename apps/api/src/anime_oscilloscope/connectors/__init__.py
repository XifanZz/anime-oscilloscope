"""External metadata and rating source connectors."""

from anime_oscilloscope.connectors.bangumi import BangumiConnector
from anime_oscilloscope.connectors.base import SourceConnector
from anime_oscilloscope.connectors.mal import MALConnector

__all__ = ["BangumiConnector", "MALConnector", "SourceConnector"]

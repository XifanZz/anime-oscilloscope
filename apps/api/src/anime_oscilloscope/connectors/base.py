from abc import ABC, abstractmethod
from datetime import date
from enum import StrEnum

from anime_oscilloscope.domain import NormalizedAnime, NormalizedEpisode, SourceCode, SubjectPage


class ConnectorError(RuntimeError):
    """A source request failed after the connector's retry policy."""


class ConnectorResponseError(ConnectorError):
    """A source returned data that cannot satisfy the connector contract."""


class ConnectorCapabilityError(ConnectorError):
    """A connector does not expose the requested operation."""


class ConnectorCapability(StrEnum):
    DISCOVERY = "discovery"
    SEARCH = "search"
    SUBJECT = "subject"
    EPISODES = "episodes"
    RATINGS = "ratings"


class SourceConnector(ABC):
    source: SourceCode
    capabilities: frozenset[ConnectorCapability]

    @abstractmethod
    async def discover(
        self,
        *,
        start_date: date,
        end_date: date,
        limit: int = 50,
        offset: int = 0,
    ) -> SubjectPage:
        """Discover animation titles whose air dates fall in [start_date, end_date)."""

    @abstractmethod
    async def fetch_subject(self, external_id: str) -> NormalizedAnime:
        """Fetch one source title and normalize it."""

    @abstractmethod
    async def search(self, query: str, *, limit: int = 10) -> list[NormalizedAnime]:
        """Search source titles for cross-source matching or user search."""

    @abstractmethod
    async def fetch_episodes(self, external_id: str) -> list[NormalizedEpisode]:
        """Fetch all main and supplemental episodes for one source title."""

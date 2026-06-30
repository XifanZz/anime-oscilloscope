from datetime import UTC, date, datetime

from anime_oscilloscope.catalog import CatalogAnime, InMemoryCatalogRepository
from anime_oscilloscope.domain import AirStatus, MediaType, RatingObservation, SourceCode

UPDATED_AT = datetime(2026, 6, 30, 8, 0, tzinfo=UTC)


def rating(source: SourceCode, score: float, count: int) -> RatingObservation:
    return RatingObservation(source=source, score=score, rating_count=count, sampled_at=UPDATED_AT)


DEMO_CATALOG = InMemoryCatalogRepository(
    [
        CatalogAnime(
            id="demo-aurora",
            canonical_name="Aurora Frequency",
            name_cn="极光频率",
            aliases=["オーロラ周波数"],
            summary="用于验证多源排行榜交互的虚构动画条目，不代表任何真实平台数据。",
            air_date=date(2026, 4, 4),
            media_type=MediaType.TV,
            status=AirStatus.AIRING,
            regions={"JP"},
            episode_count=12,
            tags=["科幻", "音乐"],
            ratings=[rating(SourceCode.BANGUMI, 8.8, 12480), rating(SourceCode.MAL, 8.6, 84210)],
            external_links={},
            updated_at=UPDATED_AT,
        ),
        CatalogAnime(
            id="demo-tidal",
            canonical_name="Tidal Archive",
            name_cn="潮汐档案",
            aliases=["潮汐アーカイブ"],
            summary="用于验证地区、类型与门槛筛选的虚构中日合拍 WEB 动画。",
            air_date=date(2026, 5, 16),
            media_type=MediaType.WEB,
            status=AirStatus.AIRING,
            regions={"CN", "JP"},
            episode_count=10,
            tags=["悬疑", "合拍"],
            ratings=[rating(SourceCode.BANGUMI, 8.6, 7021), rating(SourceCode.MAL, 8.2, 46908)],
            external_links={},
            updated_at=UPDATED_AT,
        ),
        CatalogAnime(
            id="demo-lantern",
            canonical_name="Lanterns Beyond Orbit",
            name_cn="轨道外的灯",
            aliases=["궤도 밖의 등불"],
            summary="用于验证单一来源、数据完整度和电影筛选的虚构韩国动画。",
            air_date=date(2025, 10, 2),
            end_date=date(2025, 10, 2),
            media_type=MediaType.MOVIE,
            status=AirStatus.FINISHED,
            regions={"KR"},
            tags=["太空", "剧情"],
            ratings=[rating(SourceCode.BANGUMI, 8.3, 2604)],
            external_links={},
            updated_at=UPDATED_AT,
        ),
        CatalogAnime(
            id="demo-paper-moon",
            canonical_name="Paper Moon Protocol",
            name_cn="纸月协议",
            aliases=["ペーパームーン・プロトコル"],
            summary="用于验证默认门槛会过滤低评分人数条目的虚构 OVA。",
            air_date=date(2026, 6, 1),
            end_date=date(2026, 6, 1),
            media_type=MediaType.OVA,
            status=AirStatus.FINISHED,
            regions={"JP"},
            episode_count=2,
            tags=["奇幻"],
            ratings=[rating(SourceCode.BANGUMI, 7.9, 480), rating(SourceCode.MAL, 8.1, 6500)],
            external_links={},
            updated_at=UPDATED_AT,
        ),
    ]
)

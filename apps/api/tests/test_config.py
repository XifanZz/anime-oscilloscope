from anime_oscilloscope.config import Settings


def test_cors_origins_accepts_comma_separated_environment_value(monkeypatch) -> None:
    monkeypatch.setenv(
        "APP_CORS_ORIGINS",
        "https://xifanzz.github.io, https://preview.example.com",
    )

    settings = Settings()

    assert settings.cors_origins == [
        "https://xifanzz.github.io",
        "https://preview.example.com",
    ]


def test_cors_origins_accepts_json_environment_value(monkeypatch) -> None:
    monkeypatch.setenv("APP_CORS_ORIGINS", '["https://xifanzz.github.io"]')

    settings = Settings()

    assert settings.cors_origins == ["https://xifanzz.github.io"]

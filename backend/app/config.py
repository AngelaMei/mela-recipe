from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Either a full DATABASE_URL, or the POSTGRES_* parts (as set in Kubernetes).
    database_url: str | None = None
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "mela"
    postgres_user: str = "mela"
    postgres_password: str = "mela"

    # Household. MELA_MEMBERS is "English name|中文名稱" pairs separated by commas.
    mela_household: str = "Mei & Paul"
    mela_household_zh: str = "Mei 與 Paul"
    mela_members: str = "Mei,Paul"
    mela_passcode: str = "change-me"

    session_secret: str = "dev-only-secret-change-me"
    cookie_secure: bool = True
    session_days: int = 365

    youtube_api_key: str | None = None
    max_photo_bytes: int = 8 * 1024 * 1024

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def members(self) -> list[dict[str, str]]:
        out = []
        for pair in self.mela_members.split(","):
            if not pair.strip():
                continue
            en, _, zh = pair.partition("|")
            out.append({"name": en.strip(), "name_zh": (zh or en).strip()})
        return out


@lru_cache
def get_settings() -> Settings:
    return Settings()

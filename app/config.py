from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_host: str = "172.17.5.229"
    db_port: int = 5432
    db_name: str = "cleancheck"
    db_user: str = "cleancheck_read_only"
    db_password: str = "6E8LQ0m`/HhA"
    default_company_id: int = 15
    cors_origins: str = "*"

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        return origins if origins else ["*"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

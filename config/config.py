from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class ImapSettings(Settings):
    model_config = SettingsConfigDict(env_prefix="IMAP_")
    LOGIN: str
    PASSWORD: str
    HOST: str
    PORT: int = 993
    FOLDER: str = "Backup"
    TIMEOUT: int = 30
    POLL_INTERVAL: int = 60


class SmtpSettings(Settings):
    model_config = SettingsConfigDict(env_prefix="SMTP_")
    LOGIN: str
    PASSWORD: str
    HOST: str
    PORT: int = 587
    TIMEOUT: int = 30
    RECIPIENTS: str = ""
    NOTIFY_ON: str = "error,warning"

    def get_recipients_list(self) -> list[str]:
        return [r.strip() for r in self.RECIPIENTS.split(",") if r.strip()]

    def get_notify_on_list(self) -> list[str]:
        return [s.strip() for s in self.NOTIFY_ON.split(",") if s.strip()]


class DatabaseSettings(Settings):
    model_config = SettingsConfigDict(env_prefix="DB_")
    PATH: str


class LogSettings(Settings):
    model_config = SettingsConfigDict(env_prefix="LOG_")
    LEVEL: str
    FORMAT: str
    DIR: str = "./logs"
    TO_FILE: bool = False
    FILENAME: str = "bot_{date}_{time}.log"


class ApiSettings(Settings):
    model_config = SettingsConfigDict(env_prefix="API_")
    HOST: str = "0.0.0.0"
    PORT: int = 8000


class Config:
    imap = ImapSettings()
    smtp = SmtpSettings()
    db = DatabaseSettings()
    logging = LogSettings()
    api = ApiSettings()


config = Config()

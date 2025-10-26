from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Paths
    project_root: Path = Field(default=Path(__file__).parent.parent.parent)
    data_raw: Path = Field(default=Path("data/raw"))
    data_processed: Path = Field(default=Path("data/processed"))
    models_dir: Path = Field(default=Path("models"))
    model_file: str = Field(default="model.pt")
    class_names_file: str = Field(default="class_names.json")

    # Training
    img_size: int = 224
    batch_size: int = 16
    epochs: int = 10
    lr: float = 1e-3
    seed: int = 42
    # Fine-tuning options
    freeze_backbone: bool = False
    unfreeze_last_block: bool = False  # effective when freeze_backbone is True
    # Imbalance handling
    use_balanced_sampler: bool = True
    use_class_weights: bool = False
    class_weight_alpha: float = 0.5  # 0=no weighting, 1=full inverse frequency

    # App
    db_path: Path = Field(default=Path("cancer_app.db"))
    reports_dir: Path = Field(default=Path("reports"))
    model_version: str = Field(default="v1")
    admin_users: list[str] = Field(default=["admin"])  # List of admin usernames

    # Logging
    log_level: str = Field(default="INFO")

    def model_path(self) -> Path:
        return self.models_dir / self.model_file

    def class_names_path(self) -> Path:
        return self.models_dir / self.class_names_file

settings = Settings()

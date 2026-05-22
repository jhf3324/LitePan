from .driver import GuangYaDriver
from .config import GuangYaConfig

DRIVER_INFO = {
    "name": "guangya",
    "display_name": "光鸭云盘",
    "version": "0.1.0",
    "description": "光鸭云盘接入",
    "author": "LitePan",
    "capabilities": ["list", "info", "download", "create_folder", "delete", "batch_delete", "rename", "move", "upload"],
    "driver_class": GuangYaDriver,
    "config_class": GuangYaConfig,
    "card_color": "#FF7A1A",
    "card_name": "光鸭",
    "card_logo": "/logos/guangya.png",
    "icon": "fa-cloud",
    "sort_order": 6,
    "auto_oauth": 1
}

__all__ = [
    "GuangYaDriver",
    "GuangYaConfig",
    "DRIVER_INFO",
]

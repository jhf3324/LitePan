"""缓存键生成与校验：统一 key 结构，避免散落的 f-string 拼 key。"""

import hashlib
from typing import List, Optional, Union
from .cache_types import CacheConstants, AccountId, FileId, ParentId


class CacheKeyGenerator:
    @staticmethod
    def _build_key(*parts: Union[str, int]) -> str:
        return CacheConstants.KEY_SEPARATOR.join(str(part) for part in parts if part is not None)

    @staticmethod
    def directory_key(account_id: AccountId, parent_id: ParentId, page: int = 1,
                     search: Optional[str] = None) -> str:
        """dir:account_id:parent_id:page[:search_xxx]。parent_id='0' 要传账号的 root_folder_id，避免硬编码。"""
        parts = [CacheConstants.KEY_PREFIX_DIRECTORY, account_id, parent_id, page]
        if search:
            parts.append(f"search_{search}")
        return CacheKeyGenerator._build_key(*parts)

    @staticmethod
    def dir_folder_sizes_key(account_id: AccountId, parent_id: ParentId) -> str:
        return CacheKeyGenerator._build_key(
            CacheConstants.KEY_PREFIX_DIR_FOLDER_SIZES, account_id, parent_id
        )

    @staticmethod
    def dir_folder_sizes_prefix(account_id: AccountId, parent_id: Optional[ParentId] = None) -> str:
        parts = [CacheConstants.KEY_PREFIX_DIR_FOLDER_SIZES, account_id]
        if parent_id is not None:
            parts.append(parent_id)
        return CacheKeyGenerator._build_key(*parts)

    @staticmethod
    def file_info_key(account_id: AccountId, file_id: FileId) -> str:
        return CacheKeyGenerator._build_key(
            CacheConstants.KEY_PREFIX_FILE_INFO, account_id, file_id
        )

    @staticmethod
    def path_mapping_key(account_id: AccountId, path: str) -> str:
        path_hash = hashlib.md5(path.encode()).hexdigest()[:16]
        return CacheKeyGenerator._build_key(
            CacheConstants.KEY_PREFIX_PATH, account_id, path_hash
        )

    @staticmethod
    def webdav_metadata_key(account_id: AccountId, path: str) -> str:
        path_hash = hashlib.md5(path.encode()).hexdigest()[:16]
        return CacheKeyGenerator._build_key(
            CacheConstants.KEY_PREFIX_WEBDAV, account_id, path_hash
        )

    @staticmethod
    def download_mode_key(account_id: AccountId) -> str:
        return CacheKeyGenerator._build_key(
            CacheConstants.KEY_PREFIX_DOWNLOAD_MODE, account_id
        )

    @staticmethod
    def download_url_key(account_id: AccountId, file_id: FileId) -> str:
        return CacheKeyGenerator._build_key(
            CacheConstants.KEY_PREFIX_DOWNLOAD_URL, account_id, file_id
        )

    @staticmethod
    def account_config_key(account_id: AccountId) -> str:
        return CacheKeyGenerator._build_key(
            CacheConstants.KEY_PREFIX_ACCOUNT_CONFIG, account_id
        )

    @staticmethod
    def directory_prefix(account_id: AccountId, parent_id: Optional[ParentId] = None) -> str:
        """批量清理用的目录前缀；parent_id=None 时匹配该账号所有目录缓存。"""
        parts = [CacheConstants.KEY_PREFIX_DIRECTORY, account_id]
        if parent_id is not None:
            parts.append(parent_id)
        return CacheKeyGenerator._build_key(*parts)

    @staticmethod
    def file_info_prefix(account_id: AccountId) -> str:
        return CacheKeyGenerator._build_key(
            CacheConstants.KEY_PREFIX_FILE_INFO, account_id
        )

    @staticmethod
    def path_mapping_prefix(account_id: AccountId) -> str:
        return CacheKeyGenerator._build_key(
            CacheConstants.KEY_PREFIX_PATH, account_id
        )

    @staticmethod
    def webdav_metadata_prefix(account_id: AccountId) -> str:
        return CacheKeyGenerator._build_key(
            CacheConstants.KEY_PREFIX_WEBDAV, account_id
        )

    @staticmethod
    def get_related_keys_for_file_operation(account_id: AccountId, parent_id: ParentId,
                                          file_id: Optional[FileId] = None) -> List[str]:
        """列出一次写操作可能需要一起清理的 key 前缀/具体 key。"""
        keys = []

        keys.append(CacheKeyGenerator.directory_prefix(account_id, parent_id))

        if file_id:
            keys.append(CacheKeyGenerator.file_info_key(account_id, file_id))

        keys.append(CacheKeyGenerator.webdav_metadata_prefix(account_id))

        return keys


class CacheKeyValidator:
    @staticmethod
    def is_valid_key(key: str) -> bool:
        if not key or not isinstance(key, str):
            return False

        parts = key.split(CacheConstants.KEY_SEPARATOR)
        if len(parts) < 2:
            return False

        valid_prefixes = [
            CacheConstants.KEY_PREFIX_DIRECTORY,
            CacheConstants.KEY_PREFIX_DIR_FOLDER_SIZES,
            CacheConstants.KEY_PREFIX_FILE_INFO,
            CacheConstants.KEY_PREFIX_PATH,
            CacheConstants.KEY_PREFIX_WEBDAV,
            CacheConstants.KEY_PREFIX_DOWNLOAD_MODE,
            CacheConstants.KEY_PREFIX_DOWNLOAD_URL,
            CacheConstants.KEY_PREFIX_ACCOUNT_CONFIG
        ]

        if parts[0] not in valid_prefixes:
            return False

        return True

    @staticmethod
    def extract_account_id(key: str) -> Optional[AccountId]:
        if not CacheKeyValidator.is_valid_key(key):
            return None

        parts = key.split(CacheConstants.KEY_SEPARATOR)
        if len(parts) >= 2:
            try:
                return int(parts[1])
            except ValueError:
                return parts[1]

        return None

    @staticmethod
    def extract_cache_type(key: str) -> Optional[str]:
        if not CacheKeyValidator.is_valid_key(key):
            return None

        parts = key.split(CacheConstants.KEY_SEPARATOR)
        return parts[0] if parts else None

    @staticmethod
    def match_prefix(key: str, prefix: str) -> bool:
        return key.startswith(prefix + CacheConstants.KEY_SEPARATOR) or key == prefix


def generate_session_cache_key(session_id: str, operation: str, **params) -> str:
    param_str = "_".join(f"{k}={v}" for k, v in sorted(params.items()))
    return f"session:{session_id}:{operation}:{hash(param_str)}"


def generate_temp_cache_key(prefix: str, identifier: str) -> str:
    return f"temp:{prefix}:{identifier}"


def is_account_cache_key(key: str, account_id: AccountId) -> bool:
    extracted_account_id = CacheKeyValidator.extract_account_id(key)
    return extracted_account_id == account_id if extracted_account_id is not None else False

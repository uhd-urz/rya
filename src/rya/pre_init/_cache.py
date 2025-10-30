import json
from datetime import datetime

from pydantic import ValidationError

from ..names import CacheFileProperties, CacheModel, cache_path
from ..pre_utils import get_logger

logger = get_logger()


def get_cached_data() -> CacheModel:
    def _new_cache() -> CacheModel:
        cache_ = CacheModel(date=datetime.now())
        update_cache(cache_)
        return cache_

    raw_cache = json.loads(
        cache_path.get_text(encoding=CacheFileProperties.encoding, default="{}")
    )
    try:
        cache = CacheModel(**raw_cache)
    except ValidationError:
        logger.debug(
            f"Cache found in '{cache_path}' is either empty or invalid. "
            f"New cache will be created."
        )
        return _new_cache()
    else:
        if (datetime.now() - cache.date).days > CacheFileProperties.expires_in_days:
            logger.debug(
                f"Cache found in '{cache_path}' is older than "
                f"{CacheFileProperties.expires_in_days} days. "
                f"New cache will be created."
            )
            return _new_cache()
        else:
            return cache


def update_cache(cache: CacheModel) -> None:
    cache.date = datetime.now()
    cache_path.write_text(
        cache.model_dump_json(indent=CacheFileProperties.indent),
        encoding=CacheFileProperties.encoding,
    )

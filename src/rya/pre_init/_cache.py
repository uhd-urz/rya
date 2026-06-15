import json
from datetime import datetime

from pydantic import ValidationError
from pydantic.experimental.missing_sentinel import MISSING

from ..kernel import get_logger, CacheFileProperties, AppMetaCacheModel
from ..names import CacheModel, app_locations

logger = get_logger()


def get_cached_data() -> CacheModel:
    def _new_cache() -> CacheModel:
        update_cache(cache_ := CacheModel())
        return cache_

    raw_cache = json.loads(
        app_locations.cache_path.get_text(
            encoding=CacheFileProperties.encoding,
        )
        or "{}"
    )
    try:
        cache = CacheModel(**raw_cache)
    except ValidationError:
        logger.debug(
            f"Cache found in '{app_locations.cache_path}' is either empty or invalid. "
            f"New cache will be created."
        )
        return _new_cache()
    else:
        if (datetime.now() - cache.date).days > CacheFileProperties.expires_in_days:
            logger.debug(
                f"Cache found in '{app_locations.cache_path}' is older than "
                f"{CacheFileProperties.expires_in_days} days. "
                f"New cache will be created."
            )
            return _new_cache()
        else:
            return cache


def update_cache(cache: CacheModel) -> None:
    if not app_locations.cache_path.exists():
        app_locations.cache_path.create(verbose=False)
    cache.date = datetime.now()
    app_locations.cache_path.write_text(
        cache.model_dump_json(indent=CacheFileProperties.indent),
        encoding=CacheFileProperties.encoding,
    )


def update_meta_cache(cache: CacheModel, /, **kwargs) -> None:
    if cache.app_meta is MISSING:
        app_meta_dump = kwargs
    else:
        app_meta_dump = {
            **kwargs,
            **cache.app_meta.model_dump(exclude={*kwargs.keys()}),
        }
    cache.app_meta = AppMetaCacheModel(**app_meta_dump)
    update_cache(cache)

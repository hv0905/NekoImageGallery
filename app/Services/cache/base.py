from abc import ABC, abstractmethod


class CacheServiceBase(ABC):

    def get_by_id(self, entity_id: str):
        """
        Get an entity by its ID from the cache.

        :param entity_id: The ID of the entity to retrieve.
        :return: The cached entity or None if not found.
        """
        raise NotImplementedError

    def set_by_id(self, entity_id: str, entity: object):
        """
        Set an entity in the cache by its ID.

        :param entity_id: The ID of the entity to set.
        :param entity: The entity to cache.
        """
        raise NotImplementedError
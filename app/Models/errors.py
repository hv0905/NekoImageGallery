from uuid import UUID


class PointDuplicateError(ValueError):
    def __init__(self, message: str, entity_id: UUID | None = None):
        self.message = message
        self.entity_id = entity_id
        super().__init__(message)

    pass

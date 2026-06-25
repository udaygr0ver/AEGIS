from abc import ABC, abstractmethod
from typing import Optional
from app.schemas import LogCreate

class BaseParser(ABC):
    @abstractmethod
    def parse(self, raw_message: str, source_host: Optional[str] = "localhost") -> Optional[LogCreate]:
        """Parse raw log line into normalized LogCreate object."""
        pass

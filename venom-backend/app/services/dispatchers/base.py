import base64
from abc import ABC, abstractmethod

class BaseDispatcher(ABC):
    @staticmethod
    def safe_base64_decode(data: str) -> bytes:
        padding = 4 - (len(data) % 4)
        if padding != 4:
            data += '=' * padding
        return base64.b64decode(data)
    
    @abstractmethod
    def can_handle(self, function_name: str) -> bool:
        pass
    
    @abstractmethod
    async def execute(self, tool_call, arguments: dict, company_id: str) -> dict:
        pass
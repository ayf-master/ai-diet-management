"""领域异常：service 层只描述“业务上哪里错了”，由 app 统一翻译成 HTTP。"""


class DomainError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message

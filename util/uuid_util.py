import uuid


def getUUIDWithoutLine() -> str:
    return uuid.uuid4().__str__().replace('-', '')

from dataclasses import dataclass


@dataclass(frozen=True)
class ResolveObjectShareQuery:
    # The opaque share token is itself the authorization — no JWT required.
    # Share token vốn đã là phần xác thực - không cần JWT.
    token: str

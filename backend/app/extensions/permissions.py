from .registry import get_extension

VALID_PERMISSIONS = {
    "read:conversations",
    "read:world_info",
    "write:conversations",
    "hook:chat",
    "register:provider",
    "network",
}


def validate_permissions(declared):
    return [p for p in declared if p in VALID_PERMISSIONS]


def check_permission(ext_id, permission):
    ext = get_extension(ext_id)
    if not ext or not ext.get("enabled", False):
        return False
    return permission in ext.get("permissions_granted", [])

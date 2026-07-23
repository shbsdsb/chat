from app.utils.response import fail


def get_or_404(fetcher, id, name="资源"):
    """通用「取或404」守卫。返回 (row, error_response)。"""
    row = fetcher(id)
    if not row:
        return None, fail(404, f"{name}不存在")
    return row, None

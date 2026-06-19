class DistributionNotFound(Exception):
    pass

class _Dist:
    def __init__(self, version="0"):
        self.version = version

def get_distribution(name):
    # best-effort shim: return a dummy distribution with version
    return _Dist("0")

def require(*args, **kwargs):
    return []

def resource_stream(*args, **kwargs):
    raise IOError("resource not available in shim")

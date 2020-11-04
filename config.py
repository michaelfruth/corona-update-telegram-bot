_config = None


def get_config():
    global _config
    if _config is None:
        import json
        with open("example/config.json") as f:
            _config = json.load(f)
    return _config

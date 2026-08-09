COMMAND_REGISTRY = {}

def command(*phrases):
    def decorator(func):
        for phrase in phrases:
            COMMAND_REGISTRY[phrase] = func
        return func
    return decorator
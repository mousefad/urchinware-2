"""Nottinghack Creepy Urchin Software"""

__version__ = "2.0"


def singleton(class_name):
    """Singleton decorator.

    This is a simple re-implementation of the singleton_decorator PIP module
    to reduce the number of external dependencies in these days of rampant
    supply chain attacks...
    """
    instances = {}
    def getinstance(*args, **kwargs):
        if class_name not in instances:
            instances[class_name] = class_name(*args, **kwargs)
        return instances[class_name]
    return getinstance


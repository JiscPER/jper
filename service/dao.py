from octopus.modules.es import dao
from octopus.core import app

class UnroutedNotification(dao.ESDAO):
    __type__ = 'unrouted'

class RoutedNotification(dao.ESDAO):
    __type__ = 'routed'

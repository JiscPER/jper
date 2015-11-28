"""
This module contains all of the fixtures that are used throughout the testing.

The fixtures from each of the sub-modules are imported here for convenience, so instead of

::

    from service.tests.fixtures.notifications import NotificationFactory
    from service.tests.fixtures.repository import RepositoryFactory

you can do

::

    from service.tests.fixtures import NotificationFactory, RepositoryFactory
"""

from service.tests.fixtures.notifications import NotificationFactory
from service.tests.fixtures.repository import RepositoryFactory
from service.tests.fixtures.api import APIFactory
from service.tests.fixtures.packages import TestPackageHandler, PackageFactory
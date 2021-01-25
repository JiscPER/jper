# absolute paths, or relative paths from root application directory (ie. above the magnificent-octopus directory),
# to the desired config files (in the order you want them loaded)
CONFIG_FILES = [
    # octopus.lib config files
    "jper/standalone_octopus/config/cli.py",
    "jper/standalone_octopus/config/dates.py",
    "jper/standalone_octopus/config/http.py",
    "jper/standalone_octopus/config/mail.py",
    "jper/standalone_octopus/config/webapp.py",

    # octopus.module config files
    "jper/standalone_octopus/modules/account/settings.py",
    "jper/standalone_octopus/modules/clientjs/settings.py",
    "jper/standalone_octopus/modules/es/settings.py",
    "jper/standalone_octopus/modules/jper/settings.py",
    "jper/standalone_octopus/modules/store/settings.py",
    "jper/standalone_octopus/modules/swordv2/settings.py",

    # local service configuration
    "jper/config/service.py",
    "jper/local.cfg"
]

# absolute paths, or relative paths from root directory, to the template directories (in the order you want them looked at)
TEMPLATE_PATHS = [
    # local service templates
    "jper/service/templates",

    # octopus standard bootstrap layout templates
    "jper/standalone_octopus/templates",

    # octopus modules templates
    "jper/standalone_octopus/modules/account/templates",
    "jper/standalone_octopus/modules/clientjs/templates"
]

# absolute paths, or relative paths from the root directory, to the static file directories (in the order you want them looked at)
STATIC_PATHS = [
    # local service static directory
    "service/static",

    # octopus standard static directory - contains all vendor JS, plus the core Octopus JS
    "jper/standalone_octopus/static",

    # octopus modules static directories
    "jper/standalone_octopus/modules/account/static",
    "jper/standalone_octopus/modules/clientjs/static",
    "jper/standalone_octopus/modules/es/static"
]

# module import paths for the app initialisation modules that need to run at flask app creation
# (e.g. to do things like add login management support)
SETUP_MODULES = [
    "standalone_octopus.modules.account.setup_app",     # NOTE that you will also need to set ACCOUNT_ENABLE=True for this to run
    "service.setup_app"
]

# module import paths for the startup modules that need to run at application startup (in the order you want them run)
# (e.g. to do things like create/pre-populate the database)
INITIALISE_MODULES = [
    "standalone_octopus.modules.es.initialise",
    "service.initialise"
]

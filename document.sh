#!/usr/bin/env bash
# In order to run this you need to have epydoc (http://epydoc.sourceforge.net/) installed, which can be done
# on Ubuntu with
#
# sudo apt-get install python-epydoc

rm docs/code/*
epydoc --html -o docs/code/ --name "Jisc Publications Router" --url https://github.com/JiscPER/jper --graph all --inheritance grouped --docformat restructuredtext service config

# Generate the model documentation in markdown
python octopus/lib/modeldoc.py -k service.models.UnroutedNotification -o docs/system/UnroutedNotification.md -f docs/system/field_descriptions.txt
python octopus/lib/modeldoc.py -k service.models.RoutingMetadata -o docs/system/RoutingMetadata.md -f docs/system/field_descriptions.txt
python octopus/lib/modeldoc.py -k service.models.RepositoryConfig -o docs/system/RepositoryConfig.md -f docs/system/field_descriptions.txt
python octopus/lib/modeldoc.py -k service.models.MatchProvenance -o docs/system/MatchProvenance.md -f docs/system/field_descriptions.txt
python octopus/lib/modeldoc.py -k service.models.FailedNotification -o docs/system/FailedNotification.md -f docs/system/field_descriptions.txt
python octopus/lib/modeldoc.py -k service.models.RoutedNotification -o docs/system/RoutedNotification.md -f docs/system/field_descriptions.txt

python octopus/lib/modeldoc.py -k service.models.IncomingNotification -o docs/api/IncomingNotification.md -f docs/system/field_descriptions.txt
python octopus/lib/modeldoc.py -k service.models.OutgoingNotification -o docs/api/OutgoingNotification.md -f docs/system/field_descriptions.txt
python octopus/lib/modeldoc.py -k service.models.ProviderOutgoingNotification -o docs/api/ProviderOutgoingNotification.md -f docs/system/field_descriptions.txt

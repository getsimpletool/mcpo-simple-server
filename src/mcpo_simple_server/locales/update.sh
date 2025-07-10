#!/bin/bash



# Update existing translations
pybabel update --previous -i messages.pot -d ../locales


# Compile translations
pybabel compile -f -d ../locales
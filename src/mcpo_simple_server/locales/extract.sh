#!/bin/bash


# If you need extract new string to translate from the source code, 
# execute the following command:


# Warning: This will overwrite the messages.pot file
echo "WARNING: This will overwrite the messages.pot file."
echo "Do you want to continue? (YES/no)"
read answer

if [[ "$answer" != "YES" ]]; then
    echo "Operation cancelled."
    exit 1
fi


pybabel extract --previous -F babel.cfg -k lazy_gettext -o messages.pot ..

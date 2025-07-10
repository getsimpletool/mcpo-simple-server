#!/bin/bash


# If you need initialize new language, 
# execute the following command:

# Ask user for language code
echo "Please enter the language code (e.g., en_US, es_PY, fr_FR, zh_CN):"
read lang_code

# Check if language directory already exists
if [ -d "../locales/$lang_code" ]; then
    echo "Error: Language directory for $lang_code already exists."
    echo "Using this command would overwrite existing translations."
    echo "If you want to update existing translations, use update.sh instead."
    exit 1
fi

# Initialize the language with example
echo "Initializing new language: $lang_code"
pybabel init -i messages.pot -d ../locales -l $lang_code



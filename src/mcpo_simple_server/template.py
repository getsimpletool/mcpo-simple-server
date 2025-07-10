import os
from datetime import date
from typing import Any, cast
from urllib.parse import urlencode

from jinja2 import pass_context
from starlette.requests import Request
from starlette.templating import Jinja2Templates

from .config import APP_PATH, APP_VERSION
from . import i18n


templates = Jinja2Templates(directory=os.path.join(APP_PATH, "templates"))
templates.env.globals["VERSION"] = APP_VERSION
templates.env.globals["NOW_YEAR"] = date.today().year
templates.env.add_extension("jinja2.ext.i18n")

# Setup i18n translations for Jinja2 templates
i18n.setup_jinja2_translation(templates.env)

# Add translation helpers to template globals
templates.env.globals["_"] = i18n.translate
templates.env.globals["gettext"] = i18n.translate
templates.env.globals["ngettext"] = i18n.ngettext
templates.env.globals["get_locale"] = i18n.get_locale
templates.env.globals["set_locale"] = i18n.set_locale


@pass_context
def current_page_with_params(context: dict, params: dict):
    req = context.get("request")
    request = cast(Request, req)
    full_path = request.scope["raw_path"].decode()
    query_params = dict(request.query_params)
    for k, v in params.items():
        query_params[k] = v
    return full_path + "?" + urlencode(query_params)


templates.env.filters["current_page_with_params"] = current_page_with_params


def set_global_env(name: str, value: Any):
    templates.env.globals[name] = value


def add_template_folder(*folders: str):
    for folder in folders:
        templates.env.loader.searchpath.insert(0, folder)

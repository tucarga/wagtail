from wagtail.wagtailsearch.index import Indexed
from wagtail.wagtailsearch.signal_handlers import register_signal_handlers
from wagtail.wagtailsearch.backends import get_search_backend

default_app_config = 'wagtail.wagtailsearch.apps.WagtailSearchAppConfig'

default_app_config = 'bwp.contrib.reports.apps.AppConfig'

import os
from bwp.conf import settings


WEBODT_TEMPLATE_PATH = getattr(
    settings,
    'WEBODT_TEMPLATE_PATH',
    os.path.abspath(
        os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'templates',
            'webodt',
        )
    )
)

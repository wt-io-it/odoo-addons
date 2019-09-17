from . import models


def is_demomode():
    from odoo.tools import config
    return not config.get('without_demo')


if is_demomode():
    from . import demo_models
    import logging
    logging.getLogger(__name__).debug("Enabled demo imports")

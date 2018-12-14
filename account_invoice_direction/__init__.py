# -*- coding: utf-8 -*-
from . import models


def is_testmode():
    from odoo.tools import config
    return config.get('test_enable') or config.get('test_file')


if is_testmode():
    from . import test_models
    import logging
    logging.getLogger(__name__).debug("Enabled test imports")

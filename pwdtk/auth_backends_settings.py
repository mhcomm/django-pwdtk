import logging


logger = logging.getLogger()

from pwdtk.settings import *  # noqa: F401,F403

logger.warning("This module is obosolete. Please use pwdtk.settings instead")

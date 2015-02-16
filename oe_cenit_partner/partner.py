# -*- coding: utf-8 -*-

from openerp import models
from openerp.addons.oe_cenit_client import mixin


class ResPartner(mixin.SenderMixin, models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

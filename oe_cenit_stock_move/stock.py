# -*- coding: utf-8 -*-

from openerp import models
from openerp.osv import fields
from openerp.addons.oe_cenit_client import mixin


class StockMove(mixin.SenderMixin, models.Model):
    _name = 'stock.move'
    _inherit = 'stock.move'

    def _set_partner(self, cr, uid, oid, name, value, args, context=None):
        pass

    def _get_parnter(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = {'firstname': obj.location_id.company_id.partner_id.name}
        return result

    _columns = {
        'partner': fields.function(_get_parnter, method=True, type='char',
                                    fnct_inv=_set_partner, priority=1),
    }

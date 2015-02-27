# -*- coding: utf-8 -*-

from openerp import models
from openerp.osv import fields


class MarketRequest(models.Model):
    _name = 'market.request'
    _inherit = 'market.request'

    def _get_resource(self, cr, uid, model_name, resource_name):
        model = self.pool.get('market.%s' % model_name)
        res_ids = model.search(cr, uid, [('name', '=', resource_name)])
        return res_ids and res_ids[0] or False

    def _set_lines(self, cr, uid, oid, name, value, args, context=None):
        line = self.pool.get('market.request.line')
        context = context or {}
        for var in value:
            vals = {}
            vals['request_id'] = oid
            vals['quantity'] = var['quantity']
            vals['schedule_date'] = var['schedule_date']
            for x in ['commodity', 'variety', 'package']:
                vals['%s_id' % x] = self._get_resource(cr, uid, x, var[x])
            line.create(cr, uid, vals)
        return True

    def _get_lines(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            lines = []
            for line in obj.line_ids:
                var = {}
                var['commodity'] = line.commodity_id.name
                var['variety'] = line.variety_id.name
                var['package'] = line.package_id.name
                var['quantity'] = line.quantity
                var['schedule_date'] = line.schedule_date
                lines.append(var)
            result[obj.id] = str(lines)
        return result

    _columns = {
        'request_detail': fields.function(_get_lines, method=True,
                                           type='char', fnct_inv=_set_lines)
    }

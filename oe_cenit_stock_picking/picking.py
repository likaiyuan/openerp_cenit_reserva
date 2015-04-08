# -*- coding: utf-8 -*-
from openerp import models
from openerp.osv import fields

STATES_OUT = {}

STATES_IN = {}


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = 'stock.picking'

    def _get_product(self, cr, uid, name, context=None):
        product = self.pool.get('product.product')
        product_ids = product.search(cr, uid, [('name', '=', name)])
        return product_ids and product_ids[0] or False

    def _convert(self, cr, uid, vals, context=None):
        new_vals = {}
        new_vals['product_id'] = self._get_product(cr, uid, vals['product_id'])
        new_vals['product_uom_qty'] = vals['quantity']
        return new_vals

    def _set_status(self, cr, uid, oid, name, value, args, context=None):
        if value in STATES_IN:
            self.signal_workflow(cr, uid, [oid], STATES_IN[value], context)
        return True

    def _get_status(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = STATES_OUT.get(obj.state, obj.state)
        return result

    def _set_lines(self, cr, uid, oid, name, value, args, context=None):
        stock_move = self.pool.get('stock.move')
        context = context or {}
        lines = []
        for var in value:
            vals = self._convert(cr, uid, var, context)
            domain = [
                ('picking_id', '=', oid),
                ('product_id.name', '=', var['product_id']),
            ]
            pl_ids = stock_move.search(cr, uid, domain)
            lines.append(pl_ids and (1, pl_ids[0], vals) or (0, 0, vals))
        if lines:
            self.write(cr, uid, oid, {'move_lines': lines}, context)

    def _get_lines(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            lines = []
            for line in obj.move_lines:
                var = {}
                var['product_id'] = line.product_id.name
                var['quantity'] = line.product_uom_qty
                var['received_quantity'] = line.received_quantity
                lines.append(var)
            result[obj.id] = lines
        return result

    _columns = {
        'status': fields.function(_get_status, method=True, type='char',
                                  fnct_inv=_set_status),
        'lines': fields.function(_get_lines, method=True, type='char',
                                 fnct_inv=_set_lines),
    }

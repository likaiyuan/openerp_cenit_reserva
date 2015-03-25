# -*- coding: utf-8 -*-
import openerp
from openerp import models
from openerp.osv import fields

STATES = openerp.addons.sale.sale.sale_order._columns['state'].selection


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    def _get_product(self, cr, uid, name, context=None):
        product = self.pool.get('product.product')
        product_ids = product.search(cr, uid, [('name', '=', name)])
        return product_ids and product_ids[0] or False

    def _convert(self, cr, uid, vals, context=None):
        new_vals = {}
        new_vals['name'] = vals['name']
        new_vals['product_id'] = self._get_product(cr, uid, vals['product_id'])
        new_vals['price_unit'] = vals['price']
        new_vals['product_uom_qty'] = vals['quantity']
        return new_vals

    def _set_company(self, cr, uid, oid, name, value, args, context=None):
        return True
        company = self.pool.get('res.company')
        company_ids = company.search(cr, uid, [('name', '=', value['firstname'])], context=context)
        if not company_ids:
            # This order is not for this company
            raise openerp.exceptions.AccessDenied()
        return True

    def _get_company(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            partner = obj.company_id.partner_id
            var = {}
            var['firstname'] = partner.name
            var['email'] = partner.email
            var['address1'] = partner.street
            var['address2'] = partner.street2
            var['city'] = partner.city
            var['state'] = partner.state_id and partner.state_id.name or False
            var['country'] = partner.country_id and partner.country_id.name or False
            var['phone'] = partner.phone
            var['zipcode'] = partner.zip
            result[obj.id] = var
        return result

    def _set_lines(self, cr, uid, oid, name, value, args, context=None):
        sale_line = self.pool.get('sale.order.line')
        context = context or {}
        lines = []
        for var in value:
            vals = self._convert(cr, uid, var, context)
            domain = [
                ('order_id', '=', oid),
                ('product_id.name', '=', var['product_id']),
            ]
            pl_ids = sale_line.search(cr, uid, domain)
            if pl_ids:
                lines.append((1, pl_ids[0], vals))
            else:
                lines.append((0, 0, vals))
        if lines:
            self.write(cr, uid, oid, {'order_line': lines})

    def _get_lines(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            lines = []
            for line in obj.order_line:
                var = {}
                var['name'] = line.name
                var['product_id'] = line.product_id.name
                var['price'] = line.price_unit
                var['quantity'] = line.product_uom_qty
                lines.append(var)
            result[obj.id] = lines
        return result

    def _set_totals(self, cr, uid, oid, name, value, args, context=None):
        return True

    def _get_totals(self, cr, uid, ids, name, args, context=None):
        return dict.fromkeys(ids, '')

    _columns = {
        'supplier_address': fields.function(_get_company, method=True,
                                            type='char', fnct_inv=_set_company,
                                            priority=1),
        'line_items': fields.function(_get_lines, method=True, type='char',
                                      fnct_inv=_set_lines, priority=2),
        'totals': fields.function(_get_totals, method=True, type='char',
                                  fnct_inv=_set_totals, priority=3),
        'channel': fields.char('Channel', size=64)
    }

    _defaults = {
        'channel': 'origin'
    }

# -*- coding: utf-8 -*-

from openerp import models
from openerp.osv import fields


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'

    _options = []

    def _match_variant(self, cr, uid, value_ids, params, context=None):
        for p in params:
            if p.get('options', False) and (set(value_ids)).issubset(set(p['options'].values())):
                return p['options']
        return False

    def _get_attribute(self, cr, uid, name, context=None):
        pa = self.pool.get('product.attribute')
        attr = pa.search(cr, uid, [('name', '=', name)], context=context)
        if attr:
            attr_id = attr[0]
        else:
            attr_id = pa.create(cr, uid, {'name': name})
        return attr_id

    def _get_attribute_value(self, cr, uid, name, attr_id, context=None):
        pav = self.pool.get('product.attribute.value')
        to_search = [('name', '=', name), ('attribute_id', '=', attr_id)]
        attr_value = pav.search(cr, uid, to_search, context=context)
        if attr_value:
            attr_value_id = attr_value[0]
        else:
            to_create = {x[0]: x[2] for x in to_search}
            attr_value_id = pav.create(cr, uid, to_create)
        return attr_value_id

    def _set_taxons(self, cr, uid, oid, name, value, args, context=None):
        if not value:
            return False
        pc = self.pool.get('product.category')
        current_tx = False
        taxons = isinstance(value[0], list) and value[0] or value
        for tx in taxons:
            categ_id = pc.search(cr, uid, [('name', '=', tx)], context=context)
            if categ_id:
                current_tx = categ_id[0]
            else:
                vals = {'name': tx, 'parent_id': current_tx}
                current_tx = pc.create(cr, uid, vals, context)
        to_write = {'categ_id': current_tx}
        self.write(cr, uid, oid, to_write, context=context)

    def _get_taxons(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            current = obj.categ_id
            taxons = [current.name]
            while (current.parent_id):
                taxons.append(current.parent_id.name)
                current = current.parent_id
            taxons.reverse()
            result[obj.id] = taxons
        return result

    def _set_properties(self, cr, uid, oid, name, value, args, context=None):
        context = context or {}
        attribute_lines = []
        attrs = {x.attribute_id.id: x.id
                 for x in self.browse(cr, uid, oid).attribute_line_ids}
        for a, v in value.items():
            if not v:
                continue
            attr_id = self._get_attribute(cr, uid, a, context)
            attr_value_id = self._get_attribute_value(cr, uid, v, attr_id, context)
            if attr_id in attrs:
                element = (1, attrs[attr_id], {'value_ids': [(6, 0, [attr_value_id])]})
            else:
                element = (0, 0, {'attribute_id': attr_id, 'value_ids': [(6, 0, [attr_value_id])]})
            attribute_lines.append(element)
        if attribute_lines:
            to_write = {'attribute_line_ids': attribute_lines}
            self.write(cr, uid, oid, to_write)

    def _get_properties(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            pp = {}
            for at_line in obj.attribute_line_ids:
                if len(at_line.value_ids) <= 1:
                    at = at_line.attribute_id
                    pp[at.name] = at_line.value_ids.name
            result[obj.id] = pp
        return result

    def _set_options(self, cr, uid, oid, name, value, args, context=None):
        self._options = value

    def _get_options(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            attributes = []
            for at_line in obj.attribute_line_ids:
                if len(at_line.value_ids) > 1:
                    at = at_line.attribute_id
                    attributes.append(at.name)
            result[obj.id] = attributes
        return result

    def _set_variants(self, cr, uid, oid, name, value, args, context=None):
        variant = self.pool.get('product.product')
        package = self.pool.get('market.package')
        context = context or {}
        for var in value:
            vals = {
                'default_code': var['sku'],
                'weight_lb': var['weight_lb'],
                'moq': var['moq'],
                'size_count': var['size_count'],
                'variant_price': var['variant_price'],
            }
            pkg_ids = package.search(cr, uid, [('name', '=', var['package'])])
            if pkg_ids:
                pkg_id = pkg_ids[0]
            else:
                pkg_vals = {'name': var['package'], 'weight_lb': var['weight_lb']}
                pkg_id = package.create(cr, uid, pkg_vals)
            domain = [('product_tmpl_id', '=', oid), ('package', '=', pkg_id)]
            v_ids = variant.search(cr, uid, domain)
            if v_ids:
                variant.write(cr, uid, v_ids, vals)
            else:
                vals.update({
                    'product_tmpl_id': oid,
                    'package': pkg_id
                })
                ctx = dict(context or {}, create_product_variant=True)
                variant.create(cr, uid, vals, ctx)
        return True

    def _get_variants(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            variants = []
            for variant in obj.product_variant_ids:
                var = {}
                var['sku'] = variant.default_code
                var['price'] = variant.lst_price
                var['cost_price'] = variant.price
                var['quantity'] = variant.qty_available
                var['package'] = variant.package.name
                var['weight_lb'] = variant.weight_lb
                var['moq'] = variant.moq
                var['size_count'] = variant.size_count
                var['variant_price'] = variant.variant_price
                variants.append(var)
            result[obj.id] = str(variants)
        return result

    def _set_suppliers(self, cr, uid, oid, name, value, args, context=None):
        partner = self.pool.get('res.partner')
        sellers = []
        for var in value:
            domain = [('name', '=', var['firstname'])]
            pid = partner.search(cr, uid, domain)
            if pid:
                pid = pid[0]
            else:
                domain += [('supplier', '=', True), ('is_company', '=', True)]
                pid = partner.create(cr, uid, {x[0]: x[2] for x in domain})
            sellers.append((0, 0, {'name': pid}))
        self.write(cr, uid, oid, {'seller_ids': sellers})

    def _get_suppliers(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = [{'firstname': si.name.name} for si in obj.seller_ids if si.name]
        return result

    _columns = {
        'taxons': fields.function(_get_taxons, method=True, type='char',
                                  fnct_inv=_set_taxons, priority=1),
        'properties': fields.function(_get_properties, method=True,
                                      type='char', fnct_inv=_set_properties,
                                      priority=2),
        'options': fields.function(_get_options, method=True, type='char',
                                   fnct_inv=_set_options, priority=3),
        'variants': fields.function(_get_variants, method=True, type='char',
                                    fnct_inv=_set_variants, priority=4),
        'suppliers': fields.function(_get_suppliers, method=True, type='char',
                                    fnct_inv=_set_suppliers, priority=4),
    }

# _*_ coding: utf-8 _*_
from odoo import models, api,fields


class SignInvoice(models.Model):
    _name = 'sign.invoice'

    name = fields.Char(string='名稱')
    partner_id = fields.Many2one(comodel_name='res.partner', string='客戶名稱', domain=[('is_month_account', '=', True)])
    partner_sign_price = fields.Float(string='當前剩餘簽口')
    check_invoice_ids = fields.Many2many(comodel_name='account.invoice', string='勾選的發票')
    check_invoice_total = fields.Float(string='發票金額', compute='compute_total_price')
    sign_invoice_line_ids = fields.One2many(comodel_name='sign.invoice.line', inverse_name='sign_id', string='簽口明細')
    sign_invoice_ids_total = fields.Float(string='簽口價值', compute='compute_total_price')
    sign_invoice_pay = fields.Float(string='簽口應付', compute='compute_total_price')
    less_sign_price = fields.Float(string='剩餘簽口金額', compute='compute_total_price')
    created_invoice = fields.Many2one(comodel_name='account.invoice', string='建立的發票', readonly=True)
    state = fields.Selection(selection=[('draft', '草稿'), ('invoiced', '已開發票')], default='draft')
    batch_id = fields.Many2one(comodel_name='sign.batch')

    def write_sign_line(self):
        partner = self.env['sign.main'].search([('partner_id', '=', self.partner_id.id)])
        if len(partner) > 0:
            partner.write({
                'sign_account': [(0, 0, {
                    'sign_from': self.id,
                    'price': self.sign_invoice_ids_total
                })]
            })

    def create_invoice(self):
        invoice_lines = []
        for line in self.sign_invoice_line_ids:
            invoice_lines.append([0, 0, {
                'product_id': line.product_id.id,
                'uom_id': line.product_id.uom_id.id,
                'quantity': 1.0,
                'price_unit': line.price,
                'name': line.product_id.name,
                'account_id': line.product_id.property_account_income_id.id or line.product_id.categ_id.property_account_income_categ_id.id,
            }])
        res = self.env['account.invoice'].create({
            'account_id': self.partner_id.property_account_receivable_id.id,
            'partner_id': self.partner_id.id,
            'invoice_line_ids': invoice_lines,
            'sign_pay': 1,
            'name': '簽口發票' + str(self.id),
            'type': 'out_invoice',
        })
        self.created_invoice = res.id
        self.name = '簽口' + str(self.id)
        self.write_sign_line()

    def open_and_pay_invoice(self):
        # 一次做完打開與登記付款
        self.create_invoice()
        self.created_invoice.action_invoice_open()
        journal = self.env['account.journal'].search([('name', 'like', '簽口')], limit=1)
        self.created_invoice.pay_and_reconcile(journal, self.created_invoice.amount_total)
        self.state = 'invoiced'

    @api.onchange('partner_id')
    def comput_set(self):
        partner = self.env['sign.main'].search([('partner_id', '=', self.partner_id.id)])
        if len(partner) > 0:
            self.partner_sign_price = partner.last_total
            invoice_ids = self.env['account.invoice'].search([('partner_id', '=', self.partner_id.id),('state', '=', 'draft'),('sign_pay', '=', False)])
            data =[]
            for line in invoice_ids:
                data.append([4, line.id])

            self.check_invoice_ids = data
            return {'domain':
                        {'check_invoice_ids':
                             [('partner_id', '=', self.partner_id.id), ('state', '=', 'draft'),('sign_pay', '=', False)]
                         }
                    }
    @api.depends('check_invoice_ids', 'sign_invoice_line_ids')
    def compute_total_price(self):
        for line in self:
            check_sum = 0.0
            sign_sum = 0.0
            pay_sum = 0.0
            for row in line.check_invoice_ids:
                check_sum += row.amount_total
            for sign_row in line.sign_invoice_line_ids:
                sign_sum += sign_row.sign_price
                pay_sum +=sign_row.price

            line.check_invoice_total = check_sum
            line.sign_invoice_ids_total = sign_sum
            line.less_sign_price = line.partner_sign_price - check_sum + sign_sum
            line.sign_invoice_pay = pay_sum


class SignInvoiceLine(models.Model):
    _name = 'sign.invoice.line'

    sign_id = fields.Many2one(comodel_name='sign.invoice')
    product_id = fields.Many2one(comodel_name='product.product', string='簽口產品', domain=[('name', 'like', '簽口')])
    price = fields.Float(string='支付金額')
    sign_price = fields.Float(string='簽口價值', compute='cmpute_sign_price')
    sign_discount = fields.Float(string='簽口優惠', compute='cmpute_sign_price')
    cash_discount = fields.Float(string='現金優惠', compute='cmpute_sign_price')
    is_paid = fields.Boolean(string='已收款')

    def pay_the_paid(self):
        self.is_paid = True

    @api.depends('price')
    def cmpute_sign_price(self):
        for line in self:
            total = line.price
            times1 = 0.0
            times2 = 0.0
            while total >= 30000:
                if total >= 50000:
                    total = total - 50000
                    times1 += 1
                elif total >= 30000:
                    total = total - 30000
                    times2 += 1
            line.sign_price = line.price + 10000*times1 + 3000*times2
            line.sign_discount = 10000*times1 + 3000*times2
            line.cash_discount = line.price * 0.02


class SignBatch(models.Model):
    _name = 'sign.batch'

    date_from = fields.Date(string='開始時間')
    date_to = fields.Date(string='結束時間')
    name = fields.Char(string='名稱')
    sign_main_ids = fields.One2many(comodel_name='sign.batch.line', inverse_name='batch_id')



    @api.onchange('date_to')
    def set_sign_invoice(self):
        if self.date_to is False:
            return
        partner = self.env['res.partner']
        invoice = self.env['account.invoice'].search([('state', '=', 'draft'),('sign_pay', '=', False)])
        for line in invoice:
            exist = False
            for row in partner:
                if row.id == line.partner_id.id:
                    exist = True

            if exist == False and self.date_to != False:
                partner += line.partner_id

        product = self.env['product.product'].search([('name','like', '簽口')], limit=1)

        res =[]
        for line in partner:
            invoice_ids = self.env['account.invoice']
            sum = 0
            for row in invoice.filtered(lambda r:r.partner_id.id == line.id):
                invoice_ids += row
                sum += row.amount_total

            res.append([0,0,{
                'partner_id': line.id,
                'invoice_amount': sum
            }])
        self.sign_main_ids = res


class SignBatchLine(models.Model):
    _name = 'sign.batch.line'

    batch_id = fields.Many2one(comodel_name='sign.batch')
    partner_id = fields.Many2one(comodel_name='res.partner', string='客戶名稱')
    invoice_amount = fields.Float(string='發票總金額')
    sign_amount = fields.Float(string='簽口金額')
    invoice_ids = fields.Char()

    # @api.depends('invoice_ids')
    # def compute_invoice_amount(self):
    #     for line in self:
    #         res = self.env['account.invoice'].search([('id', 'in', line.invoice_ids)])
    #         sum = 0.0
    #         for row in line:
    #             sum += row.amount_total
    #
    #         line.invoice_amount = sum













from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
import json
import logging
import os
import time
import base64
import requests
import sys
import hashlib
from datetime import datetime

from collections import defaultdict
MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'out_receipt': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
    'in_receipt': 'supplier',
}

class PaymentLoant(models.Model):

    _inherit = 'account.payment'
    accountloan_id = fields.Many2one(comodel_name="account.loan", string="Prestamo")

    institucionOrdenante = fields.Char(string="Institucion Ordenante")
    institucionBeneficiaria = fields.Char(string="Institucion Beneficiaria")
    claveRastreo = fields.Char(string="Clave Rastreo")
    nombreOrdenante = fields.Char(string="Ordenante")
    cuentaOrdenante = fields.Char(string="Cuenta Ordenante")
    nombreBeneficiario = fields.Char(string="Beneficiario")
    cuentaBeneficiario = fields.Char(string="Cuenta Beneficiario")
    conceptoPago = fields.Char(string="Concepto Pago")
    referenciaNumerica = fields.Char(string="Folio")
    tipoPago = fields.Char(string="Tipo Pago")
    tsLiquidacion = fields.Char(string="tsLiquidacion")
    folioCodi = fields.Char(string="Folio Codi")

    # clip
    collection_id = fields.Char(string="Id Pago Clip")
    origin = fields.Char(string="Origen")
    source = fields.Char(string="source")
    capital = fields.Float(string="Capital")
    interest = fields.Float(string="Intereses")
    tax = fields.Float(string="IVA")
    overdue_interest = fields.Float(string="% De Interes")
    collection_id_origin = fields.Char(string="Origen de Dispersion")

    def post_collections(self):
        for rec in self:
            conexion = self.env["api.credit.avalor"].search([('api', '=', 'clip')])
            url = ""
            api_key = ""
            for con in conexion:
                url = con.url
                api_key = con.consumer_key

            datas = {
                # "date": fields.Date.context_today(self).strftime('%Y-%m-%d'),
                "proxy_merchant_token": rec.partner_id.merchan,
                "collection": {
                    "provider_loan_id": rec.accountloan_id.name,
                    "provider_collection_id": rec.name,
                    "amount": rec.amount,
                    "capital": rec.capital,
                    "interest": rec.interest,
                    "tax": rec.tax,
                    "overdue_interest": rec.overdue_interest,
                    "collected_at": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
                }
            }
            status_code = "0"
            headers = {"Content-Type": "application/json", "x-api-key": api_key}
            json_text = datas
            url_services = url + "/collections"

            r = requests.post(url=url_services, data=json.dumps(json_text), headers=headers)
            r.encoding = 'utf-8'
            status_code = str(r.status_code)
            result = str(r.text)

            try:
                dat = r.json()
                cal = dat['collection']

                rec.collection_id = cal['collection_id']
                rec.origin = cal['origin']
                rec.source = cal['source']
                rec.collection_id_origin = cal['collection_id_origin']
            except:
                dat = []
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': status_code + " ",
                    # 'message':firma,
                    'message': str(dat),
                    'type': 'success',  # types: success,warning,danger,info
                    'sticky': True,  # True/False will display for few seconds if false
                },
            }
            return notification


    def action_register_payment(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return ''

        return {
            'name': _('Register Payment'),
            'res_model': len(active_ids) == 1 and 'account.payment' or 'account.payment.register',
            'view_mode': 'form',
            'view_id': len(active_ids) != 1 and self.env.ref(
                'account.view_account_payment_form_multi').id or self.env.ref(
                'account.view_account_payment_invoice_form').id,
            'context': self.env.context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    @api.model
    def default_get(self, default_fields):
        rec = super(PaymentLoant, self).default_get(default_fields)
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        active_model = self._context.get('active_model')

        # Check for selected invoices ids
        if not active_ids or active_model != 'account.loan':
            return rec

        invoices = self.env['account.loan'].browse(active_ids)

        # Check all invoices are open
        # if not invoices or any(invoice.state != 'posted' for invoice in invoices):
        #     raise UserError(_("You can only register payments for open invoices"))
        # Check if, in batch payments, there are not negative invoices and positive invoices
        # dtype = invoices[0].type
        # for inv in invoices[1:]:
        #     if inv.type != dtype:
        #         if ((dtype == 'in_refund' and inv.type == 'in_invoice') or
        #                 (dtype == 'in_invoice' and inv.type == 'in_refund')):
        #             raise UserError(
        #                 _("You cannot register payments for vendor bills and supplier refunds at the same time."))
        #         if ((dtype == 'out_refund' and inv.type == 'out_invoice') or
        #                 (dtype == 'out_invoice' and inv.type == 'out_refund')):
        #             raise UserError(
        #                 _("You cannot register payments for customer invoices and credit notes at the same time."))

        # amount = self._compute_payment_amount(invoices, invoices[0].currency_id, invoices[0].journal_id,
        #                                       rec.get('payment_date') or fields.Date.today())
        amount = (invoices.loan_amount * invoices.rate / 100) 
        rec.update({
            'currency_id': invoices[0].currency_id.id,
            'journal_id': 1,

            'amount': amount,
            'payment_type': 'inbound',
            # 'payment_type': 'inbound' if amount > 0 else 'outbound',
            'partner_id': invoices[0].partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE["out_invoice"],
            'communication': invoices.name,
            'accountloan_id': invoices.id,
        })
        return rec


{
  "collection": {
    "collection_id": "cafe3ded-b9a9-4788-84a3-7adee3e6086b",
    "provider_collection_id": "provider-collection-1001",
    "loan_id": "cafe3ded-b9a9-4788-84a3-7adee3e6086b",
    "provider_loan_id": "provider-loan-1001",
    "proxy_merchant_token": "e53af598-be0d-4cdc-bcfc-4b8e26bef6d4",
    "origin": "SETTLEMENT",
    "source": "REGULAR",
    "total_amount": 1000,
    "capital": 0,
    "interest": 0,
    "tax": 0,
    "overdue_interest": 0,
    "collection_date_local": "2021-06-15",
    "collected_at": "2021-01-15T12:00:00Z",
    "collection_id_origin": "60524022-625d-4bfc-a4aa-e9e384f5289c",
    "created_at": "2021-01-15T12:00:00Z",
    "updated_at": "2021-02-15T20:00:00Z"
  },
  "loan": {
    "loan_id": "cafe3ded-b9a9-4788-84a3-7adee3e6086b",
    "proxy_merchant_token": "e53af598-be0d-4cdc-bcfc-4b8e26bef6d4",
    "provider_code": "CLIP",
    "provider_loan_id": "provider-loan-1001",
    "pre_approval_id": "7b63cf89-04cb-444c-b81e-631b1b4e9d7e",
    "status": "ACTIVE",
    "retention_percentage": 25,
    "loan_amount": 10000,
    "interest": 1000,
    "tax": 160,
    "payback": 11160,
    "current_balance": 11160,
    "balance_capital": 10000,
    "balance_interest": 1000,
    "balance_tax": 160,
    "disbursed_at": "2021-01-15T12:00:00Z",
    "ends_at": "2021-12-31T12:00:00Z",
    "contract_signed_at": "2021-01-10T12:00:00Z",
    "start_date_local": "2021-07-31",
    "end_date_local": "2021-12-31",
    "created_at": "2021-01-15T12:00:00Z",
    "updated_at": "2021-02-15T20:00:00Z"
  }
}
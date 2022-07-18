from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
import json
import logging
import os
import time
import base64
import requests

class av_preapproval(models.Model):
    _name = "clip.preapproval"
    _inherit = ['mail.thread']
    _description = 'Ofertas Clip'

    def _default_company(self):
        force_company = self._context.get("force_company")
        if not force_company:
            return self.env.user.company_id.id
        return force_company

    name = fields.Char(string="Nombre", store=True, readonly=True )
    send_ofer = fields.Many2one(comodel_name="clip.sendpreapproval", string="Envio de oferta")
    amount = fields.Float(string="Monto")
    interest = fields.Float(string="Interes", compute="get_interes")
    interestp = fields.Float(string="% Interes")
    tax = fields.Float(string="Tax")
    payback = fields.Float(string="Total a pagar", compute="get_playback")
    term_maximum = fields.Integer(string="Maximo Temermino (meses)")
    retention_percentage_sale = fields.Float(string="Retencion %")
    expiration_at = fields.Datetime(string="Fecha expiracion")
    type = fields.Selection([('REGULAR', 'Regular'), ('OPEN_DATA', 'OPEN DATA')], string="Tipo", default="REGULAR")
    pre_approval_id = fields.Char(string="Pre approval id")
    provider_code = fields.Char(string="Provider Code")

    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=_default_company,

    )

    @api.onchange("amount", "interestp")
    def get_interes(self):
        for rec in self:
            pin = rec.interestp
            mon = rec.amount
            rec.interest = mon * (pin / 100)





    @api.depends("send_ofer", "amount", "interest", "tax","interestp")
    @api.onchange("amount", "interest", "tax")
    def get_playback(self):
        for rec in self:

            rec.payback = rec.amount + rec.interest + rec.tax

class ModelName(models.Model):
    _name = 'clip.sendpreapproval'
    _description = 'Agrupamiento de ofertas'
    _inherit = ['mail.thread']

    def _default_company(self):
        force_company = self._context.get("force_company")
        if not force_company:
            return self.env.user.company_id.id
        return force_company

    name = fields.Char(string="Nombre")
    date = fields.Date(string="Fecha envio")
    date_c = fields.Date(string="Fecha Creacion", compute="rename_oferts")

    merchan = fields.Many2one(comodel_name="res.partner", string="Merchant")
    ofertas = fields.One2many('clip.preapproval','send_ofer',string='Ofertas')

    state = fields.Selection([('espera', 'En espera'), ('send', 'enviado'),('error', 'Error')
                             ], string="Status", default="espera")
    result = fields.Text("Resultado")



    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=_default_company,
        readonly=True,
        states={"espera": [("readonly", False)]},
    )



    @api.depends("merchan","ofertas","date")
    def rename_oferts(self):
        for res in self:
            metch_id = res.merchan.merchan_id
            con = 1

            today = fields.Date.context_today(self)
            name = "BSR-" + res.date.strftime('%y%m')



            for ofer in res.ofertas:

                ofer.name = name + "-" + metch_id + "-" + str(con)
                con = con + 1
            res.date_c = today


    def get_preids(self):
        for rec in self:
            data = json.loads(rec.result)
            dat = ""
            if rec.state == "send":
                for t in data['pre_approvals']:
                    dat = t['pre_approval_id']
                    for ofe in rec.ofertas:
                        if ofe.name == t['provider_pre_approval_id']:
                            ofe.pre_approval_id = dat.replace(" ", "")
                            ofe.provider_code = t['provider_code'].replace(" ", "")
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': "lista",
                    'message': dat,
                    'type': 'success',  # types: success,warning,danger,info
                    'sticky': True,  # True/False will display for few seconds if false
                },
            }
            return notification

    def action_post(self):
        for rec in self:
            conexion = self.env["api.credit.avalor"].search([('api', '=', 'clip')])
            url = ""
            api_key = ""
            for con in conexion:
                url = con.url
                api_key = con.consumer_key
            ofertas = []
            for ofer in rec.ofertas:
                ofertas.append({
                    "provider_pre_approval_id": ofer.name,
                    "amount": ofer.amount,
                    "interest": ofer.interest,
                    "tax": ofer.tax,
                    "payback": ofer.payback,
                    "term_maximum": ofer.term_maximum,
                    "retention_percentage_sale": ofer.retention_percentage_sale,
                    "expiration_at": ofer.expiration_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "type": ofer.type,
                })


            jsonRequest ={
                "proxy_merchant_token":rec.merchan.merchan,
                "pre_approvals": ofertas,
                "signature_redirect_url":""
            }

            headers = {"Content-Type": "application/json", "x-api-key": api_key}
            json_text = jsonRequest
            url_services = url + "/preapproval"

            # headers['x-signature'] = key_handler.get_signature_from_private_key(json_text)
            r = requests.post(url=url_services, data=json.dumps(json_text), headers=headers)
            r.encoding = 'utf-8'

            status_code = str(r.status_code)
            rec.result = str(r.text)
            if(status_code == "201"):
                rec.state = "send"
                rjson = r.text
                rec.get_preids()
            test = str(r.text)
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': status_code,
                    'message': test,
                    'type': 'success',  # types: success,warning,danger,info
                    'sticky': True,  # True/False will display for few seconds if false
                },
            }
            return notification


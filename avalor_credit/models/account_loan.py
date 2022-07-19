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
from odoo.tools import safe_eval
from dateutil.relativedelta import relativedelta
from datetime import datetime
from datetime import timedelta
import OpenSSL
import jks
from OpenSSL import crypto
import base64
from cryptography.hazmat.primitives import serialization, hashes

_logger = logging.getLogger(__name__)
try:
    import numpy_financial
except (ImportError, IOError) as err:
    _logger.debug(err)
_ASN1 = OpenSSL.crypto.FILETYPE_ASN1

class account_loand_estados(models.Model):
    _name = "account.loan.estadostp"
    _inherit = ['mail.thread']
    _description = 'Cambios de Estados'

    id_stp = fields.Integer(string="Clave STP")
    name = fields.Char(string="Name", store=True, compute="get_loand")
    empresa = fields.Char(string="Empresa")
    folioOrigen = fields.Char(string="Folio")
    estado = fields.Char(string="Estado")
    causaDevolucion = fields.Text(string="Causa de Devolucion")
    tsLiquidacion = fields.Text(string="Ts Liquidacion")
    accountloan_id = fields.Many2one(comodel_name="account.loan", string="Prestamo", store=True)

    @api.depends("folioOrigen","estado")
    def get_loand(self):
        for res in self:
            folio = res.folioOrigen
            conexion = res.env["account.loan"].search([('name', '=', folio)])
            id = 0
            for con in conexion:
                id = con.id
            if id > 0:
               res.accountloan_id = id
            res.name = res.estado + "/" + folio
def monthdelta(date, delta):
    m, y = (date.month+delta) % 12, date.year + ((date.month)+delta-1) // 12
    if not m: m = 12
    d = min(date.day, [31,
        29 if y%4==0 and not y%400==0 else 28,31,30,31,30,31,31,30,31,30,31][m-1])
    return date.replace(day=d,month=m, year=y)
class account_loan_integration(models.Model):
    _inherit = 'account.loan'

    # rate = fields.Float(required=True, readonly=True, digits=(8, 6), )
    rate = fields.Float(required=True)
    rate_period = fields.Float(
        compute="_compute_rate_period",
        help="Real rate that will be applied on each period",
    )
    loan_type = fields.Selection(
        [
            ("mca-clip", "MCA Clip"),
            ("kiero", "Kiero"),
            ("simple", "simple"),
            ("fixed-annuity", "Fixed Annuity"),
            ("fixed-annuity-begin", "Fixed Annuity Begin"),
            ("fixed-principal", "Fixed Principal"),
            ("interest", "Only interest"),
        ],
        required=True,
        help="Method of computation of the period annuity",
        readonly=True,
        states={"draft": [("readonly", False)]},
        default="simple",
    )

    estado_loan = fields.One2many(comodel_name="account.loan.estadostp", string="Cambio de Estados", inverse_name="accountloan_id")
    claveRastreo = fields.Char(string="Clave Rastreo")
    loan_id = fields.Char(string="Id Prestamo Clip")
    loan_id_stp = fields.Char(string="Id Prestamo STP", compute="get_idstp")
    ref_numerica = fields.Integer(string="Referencia Numerica")
    conceptoPago = fields.Char(string="Concepto de Pago")
    resut_stp_json = fields.Text(string="STP Resultado")
    resut_clip_json = fields.Text(string="CLIP Resultado")
    fecha_dipersion = fields.Datetime(string="Fecha de Dispersion")
    fecha_contrato = fields.Datetime(string="Fecha de Contrato")
    cuentaOrdenante = fields.Char(string="Cuenta de banco ASIGNADA")
    id_prestamo =fields.Char(string="Id Prestamo", store = True)
    pay_periodo = fields.Monetary(string="Pago por periodo", compute="get_pagos", store = True)

    comision = fields.Monetary(string="Comision")

    pay_back = fields.Monetary(string="Pay Back")
    total_interes = fields.Monetary(string="Total Interes")
    tasa = fields.Float(string="Tasa (anualizada)", compute="get_pagos", store = True)
    comision = fields.Float(string="% Comision")
    tir = fields.Float(string="TIR Estimada")
    tir_actual = fields.Float(string="TIR Actual")
    tir_proyect = fields.Float(string="TIR Proyectada")

    merchan = fields.Char(string="Id Client")
    merchan_id = fields.Char(string="Proxy Merchant Token")
    cuenta_clabe_stp = fields.Char(string="Cuanta Clabe")
    iva = fields.Monetary(string="iva")

    retencion = fields.Float(string="% de retencion")
    clasif_seg = fields.Char(string="Clasificación de Seguimiento")
    coef_seg = fields.Char(string="Coeficiente de Seguimiento")
    plazo_tranc = fields.Float(string="Plazo Transcurrido")
    por_cobranza = fields.Float(string="% de Cobranza")
    count_dias_ult_pago = fields.Integer(string="Días desde el último Pago")
    date_lastpay = fields.Date(string="Fecha último pago")
    days_before_pay = fields.Integer(string="Días para vencimiento")
    tasa_mora = fields.Char(string="Tasa Moratorios")

    total_pay = fields.Monetary(string="Capital Cobrado")
    interes_pay = fields.Monetary(string="Interes Cobrado")
    iva_pay = fields.Monetary(string="Iva Cobrado")


    @api.depends("loan_amount","rate","periods")
    @api.onchange("loan_amount","rate","periods")
    def get_pagos(self):
        for rec in self:
            pay = 0
            tasa = 0
            if rec.periods > 0:
                inte = rec.loan_amount * (rec.rate/100)
                mon = rec.loan_amount + inte
                rec.total_interes = inte
                rec.pay_back = mon
                pay = mon / rec.periods
                tasa = (numpy_financial.rate(rec.periods,pay,rec.loan_amount*(-1),0) * (365/7)) * 100
            rec.tasa = tasa
            rec.pay_periodo = pay

    @api.depends("resut_stp_json")
    def get_idstp(self):
        for rec in self:
            if rec.resut_stp_json:
                data = json.loads(rec.resut_stp_json)
                if data["resultado"]["id"]:
                    rec.loan_id_stp = data["resultado"]["id"]
                else:
                    rec.loan_id_stp = ""
            else:
                rec.loan_id_stp = ""
    @api.depends("partner_id")
    @api.onchange("partner_id")
    def get_infomerchan(self):
        for rec in self:
            if rec.partner_id.ofert_clip:
                rec.rate_type = "real"
                rec.periods = 1
                rec.loan_type = "clip"
                rec.type_periods = "semana"
                monto = rec.partner_id.ofert_clip.amount
                rec.loan_amount = monto
                inter = rec.partner_id.ofert_clip.interest
                rec.merchan = rec.partner_id.merchan
                rec.merchan_id = rec.partner_id.merchan_id
                rec.cuenta_clabe_stp = rec.partner_id.cuenta_clabe_stp
                rec.cuentaOrdenante = rec.company_id.cuentaOrdenante
                rec.rate = rec.partner_id.ofert_clip.interestp

    def open_payments(self):
        payment_ids = []
        for res in self:
            payment_id = self.env['account.payment'].search([('communication', '=', res.id_prestamo)])
            for pay in payment_id:
                payment_ids.append(pay.id)
        # self.ensure_one()
        # invoice_payments_widget = json.loads(self.invoice_payments_widget)
        # payment_ids = []
        # for item in invoice_payments_widget["content"]:
        #     payment_ids.append(item["account_payment_id"])

        # if self.type == "out_invoice":
        #     action_ref = "account.action_account_payments"
        # else:
        #     action_ref = "account.action_account_payments_payable"
        action_ref = "account.action_account_payments"
        [action] = self.env.ref(action_ref).read()
        action["context"] = dict(safe_eval(action.get("context")))
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': ('mejoras'),
                'message': str(action["context"]),
                'type': 'success',  # types: success,warning,danger,info
                'sticky': True,  # True/False will display for few seconds if false
            },
        }
        # return notification
        if len(payment_ids) > 1:
            action["domain"] = [("id", "in", payment_ids)]
        elif payment_ids:
            action["views"] = [(self.env.ref("account.view_account_payment_form").id, "form")]
            action["res_id"] = payment_ids[0]

        return action

    def action_invoice_register_payment(self):
        for rec in self:
            return self.env['account.payment'] \
                .with_context(active_ids=rec.ids, active_model='account.loan', active_id=rec.id) \
                .action_register_payment()

    def encrypt_text(self,input_text, privkeyfile, password, publickey):
        utf8_text = input_text
        # serialized_certificate = privkeyfile.decode("utf-8")
        # serialized_certificate = fp = open(privkeyfile, 'r', encoding='utf-8')
        keystore = jks.KeyStore.loads(privkeyfile,password,True)
        pk_entry = keystore.private_keys["avalor"]
        cety = pk_entry.cert_chain[0][1]
        public_cert = OpenSSL.crypto.load_certificate(_ASN1, pk_entry.cert_chain[0][1])
        # if the key could not be decrypted using the store password, decrypt with a custom password now
        pkey = OpenSSL.crypto.load_privatekey(_ASN1, pk_entry.pkey)
        # pkey = crypto.load_privatekey(crypto.FILETYPE_PEM, serialized_certificate)
        # dataBytes = bytes(utf8_text, encoding='ascii')
        signData = crypto.sign(pkey, utf8_text, "sha256")
        certificate = crypto.load_certificate(crypto.FILETYPE_PEM, publickey)
        res = crypto.verify(public_cert,signData,utf8_text,"sha256")
        # raise UserError(_(res))
        encodedData = base64.b64encode(signData)

        return encodedData

    def prueba_api(self):
        for rec in self:
            datos_stp={
                  "id_stp": 12345678,
                  "empresa": "string",
                  "folioOrigen": "ACL000001",
                  "estado": "string",
                  "causaDevolucion": "string",
                  "tsLiquidacion": "string",

                }
            headers = {"Content-Type": None,"x-api-key":"57b1852e-9e7d-4277-ba12-c574d0526322"}
            json_text = datos_stp
            url_services = "https://avalor.ogum.mx/api/v1/cambiosestado/account.loan.estadostp"

            r = requests.post(url=url_services, data=json_text, headers=headers)
            r.encoding = 'utf-8'

            status_code = str(r.status_code)

            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': status_code + " " + url_services,
                    'message': str(r.text),
                    'type': 'success',  # types: success,warning,danger,info
                    'sticky': True,  # True/False will display for few seconds if false
                },
            }
            return notification

    def loan_CLIP(self):
        for rec in self:

            conexion = self.env["api.credit.avalor"].search([('api', '=', 'clip')])
            url = ""
            api_key = ""
            for con in conexion:
                url = con.url
                api_key = con.consumer_key

            loan = []
            ends_at = monthdelta(rec.fecha_dipersion, rec.partner_id.ofert_clip.term_maximum)
            # ends_at = ends_at + timedelta(months=)

            jsonRequest = {
                  "proxy_merchant_token": rec.partner_id.merchan,
                  "provider_loan_id": rec.name,
                  "pre_approval_id": rec.partner_id.ofert_clip.pre_approval_id,
                  "provider_pre_approval_id": rec.partner_id.ofert_clip.name,
                  "disbursed_at": rec.fecha_dipersion.strftime('%Y-%m-%dT%H:%M:%SZ'),
                  "ends_at": ends_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
                  "contract_signed_at": rec.fecha_contrato.strftime('%Y-%m-%dT%H:%M:%SZ'),
                  "conditions": {
                    "retention_percentage_sale": rec.partner_id.ofert_clip.retention_percentage_sale,
                    "deposited_amount": rec.loan_amount,
                    "interest_amount": rec.partner_id.ofert_clip.interest,
                    "tax_amount": rec.partner_id.ofert_clip.tax,
                    "payback_amount": rec.partner_id.ofert_clip.payback
                  }
            }

            headers = {"Content-Type": "application/json", "x-api-key": api_key}
            json_text = jsonRequest
            url_services = url + "/"
            url_services = url_services.replace(" ", "")

            r = requests.post(url=url_services, data=json.dumps(json_text), headers=headers)
            r.encoding = 'utf-8'

            status_code = str(r.status_code)
            result = str(r.text)
            try:
                data = r.json()
                rec.resut_clip_json =str(result)
                if data["loan_id"]:
                    rec.loan_id = data["loan_id"]
                    rec.loan_id = data["loan_id"]
            except:
                data=[]

            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': status_code + " " + result,
                    # 'message':firma,
                    'message': str(jsonRequest),
                    'type': 'success',  # types: success,warning,danger,info
                    'sticky': True,  # True/False will display for few seconds if false
                },
            }
            return notification
    def regitroSTP(self):
        for rec in self:

            cuentaBeneficiario = ""
            tipoCuentaBeneficiario = ""
            clabe_inti = ""

            rfc_curpBen = rec.partner_id.vat or rec.partner_id.curp or "ND"
            rfc = rec.company_id.vat or "ND"
            # date = str(rec.start_date.strftime('%Y%m%d'))
            date = ""
            for bank in rec.partner_id.bank_ids:
                tipoCuentaBeneficiario = bank.type_cuenta
                cuentaBeneficiario = str(bank.l10n_mx_edi_clabe)
                clabe_inti = str(bank.clabe_inti)
            cadena = "||" + clabe_inti + "|" + rec.company_id.name_stp + "|" + date + "|" + rec.name + "|" + rec.claveRastreo + "|"
            cadena += rec.company_id.clabe_inti + "|" + "{:.2f}".format(rec.loan_amount) + "|1|" + rec.company_id.type_cuenta + "|" + rec.company_id.name + "|" + rec.cuentaOrdenante+ "|" + rfc + "|"
            cadena += tipoCuentaBeneficiario + "|" + rec.partner_id.name + "|" + cuentaBeneficiario + "|" + rfc_curpBen + "||||||" + rec.conceptoPago + "||||||"+ str(rec.ref_numerica) + "||||||||"
            conexion = self.env["api.credit.avalor"].search([('api', '=', 'stpmex')])
            url = ""
            key = ""
            cer = ""
            passw = ""

            for con in conexion:
                url = con.url
                key = base64.b64decode(con.archivo_key)
                cer = base64.b64decode(con.archivo_cer)
                passw = con.consumer_secret
            firma = rec.encrypt_text(cadena,key,passw,cer)
            datos_stp= {
                    "claveRastreo": rec.claveRastreo,
                    "conceptoPago":  rec.conceptoPago,
                    "cuentaBeneficiario": cuentaBeneficiario,
                    "cuentaOrdenante": rec.cuentaOrdenante,
                    "empresa": rec.company_id.name_stp,
                    "folioOrigen": rec.name,
                    "institucionContraparte": clabe_inti,
                    "institucionOperante": rec.company_id.clabe_inti,
                    "monto": "{:.2f}".format(rec.loan_amount),
                    "nombreBeneficiario": rec.partner_id.name,
                    "nombreOrdenante": rec.company_id.name,
                    # "fechaOperacion": date,
                    "referenciaNumerica": str(rec.ref_numerica),
                    "rfcCurpBeneficiario":rfc_curpBen,
                    "rfcCurpOrdenante": rfc,
                    "tipoCuentaBeneficiario": tipoCuentaBeneficiario,
                    "tipoCuentaOrdenante":rec.company_id.type_cuenta,
                    "tipoPago":"1",
                    "firma": firma.decode("utf-8")

            }


            headers = {"Content-Type": "application/json"}
            json_text = json.dumps(datos_stp)
            url_services = url + "/ordenPago/registra"


            r = requests.put(url=url_services, data=json_text, headers=headers)
            r.encoding = 'utf-8'
            #
            status_code = str(r.status_code)
            rec.resut_stp_json = str(r.text)
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': status_code + " ",
                    # 'message':firma,
                    'message':  str(r.text),
                    'type': 'success',  # types: success,warning,danger,info
                    'sticky': True,  # True/False will display for few seconds if false
                },
            }
            return notification
    def get_loan_clip(self):
        for rec in self:
            conexion = self.env["api.credit.avalor"].search([('api', '=', 'clip')])
            url = ""
            api_key = ""
            for con in conexion:
                url = con.url
                api_key = con.consumer_key
            headers = {"Content-Type": "application/json", "x-api-key": api_key}

            url_services = url + "?proxy_merchant_token="+rec.partner_id.merchan

            url_services = url_services.replace(" ", "")

            r = requests.get(url=url_services, headers=headers)
            r.encoding = 'utf-8'

            status_code = str(r.status_code)
            result = str(r.text)

            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': status_code ,
                    # 'message':firma,
                    'message': result,
                    'type': 'success',  # types: success,warning,danger,info
                    'sticky': True,  # True/False will display for few seconds if false
                },
            }
            return notification

    def get_collections(self):
        for res in self:
            conexion = self.env["api.credit.avalor"].search([('api', '=', 'clip')])
            url = ""
            api_key = ""
            for con in conexion:
                url = con.url
                api_key = con.consumer_key

            datas = "?date=2022-05-13"  #fields.Date.context_today(self).strftime('%Y-%m-%d')
            datas = datas + "&proxy_merchant_token=" + res.partner_id.merchan
            datas = datas + "&provider_loan_id=" + res.name



            headers = {"Content-Type": "application/json", "x-api-key": api_key}
            json_text = datas
            url_services = url + "/collections"+ datas
            url_services = url_services.replace(" ", "")
            # headers['x-signature'] = key_handler.get_signature_from_private_key(json_text)
            r = requests.get(url=url_services, headers=headers)
            r.encoding = 'utf-8'
            status_code = str(r.status_code)
            status = str(r.text)
            # data = json.loads(status)
            # data = [
            #       {
            #         "collection_id": "cafe3ded-b9a9-4788-84a3-7adee3e6086b",
            #         "provider_collection_id": "provider-collection-1001",
            #         "loan_id": "cafe3ded-b9a9-4788-84a3-7adee3e6086b",
            #         "provider_loan_id": "provider-loan-1001",
            #         "proxy_merchant_token": "e53af598-be0d-4cdc-bcfc-4b8e26bef6d4",
            #         "origin": "SETTLEMENT",
            #         "source": "REGULAR",
            #         "total_amount": 1000,
            #         "capital": 0,
            #         "interest": 0,
            #         "tax": 0,
            #         "overdue_interest": 0,
            #         "collection_date_local": "2021-06-15",
            #         "collected_at": "2021-01-15T12:00:00Z",
            #         "collection_id_origin": "60524022-625d-4bfc-a4aa-e9e384f5289c",
            #         "created_at": "2021-01-15T12:00:00Z",
            #         "updated_at": "2021-02-15T20:00:00Z"
            #       }
            #     ]
            # pagos = []
            # for pay in data:
            #     loan = self.env["account.loan"].search([('loan_id', '=', pay.loan_id)])
            #     pagos.append([0, 0, {
            #         "accountloan_id" : loan.id,
            #         "collection_id": pay.collection_id,
            #         "origin": pay.origin,
            #         "source": pay.source,
            #         "capital": pay.capital,
            #         "interest": pay.interest,
            #         "tax": pay.tax,
            #         "overdue_interest": pay.overdue_interest,
            #         "collection_id_origin": pay.collection_id_origin,
            #         "amount": pay.total_amount,
            #
            #     }])
            #
            # self.env["account.payment"].write(pagos)

            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title':  status_code,
                    # 'message':firma,
                    'message': str(status),
                    'type': 'success',  # types: success,warning,danger,info
                    'sticky': True,  # True/False will display for few seconds if false
                },
            }
            return notification

    def cosuta_saldoSTP(self):
        for rec in self:
            fecha = str(fields.Date.context_today(self).strftime('%Y%m%d'))

            cadena = rec.cuentaOrdenante
            conexion = self.env["api.credit.avalor"].search([('api', '=', 'stpmex')])
            url = ""
            key = ""
            cer = ""
            passw = ""
            for con in conexion:
                url = con.url
                key = base64.b64decode(con.archivo_key)
                cer = base64.b64decode(con.archivo_cer)
                passw = con.consumer_secret
            firma = rec.encrypt_text(cadena, key, passw, cer)

            url_services = url + "/cuentaModule/" + rec.cuentaOrdenante
            ploads = {"firma": firma.decode("utf-8")}
            headers = {"Content-Type": "application/json"}
            r = requests.get(url=url_services, params=ploads, headers=headers)
            r.encoding = 'utf-8'

            status_code = str(r.status_code)

            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': status_code + " ",
                    'message': str(r.text),
                    'type': 'success',  # types: success,warning,danger,info
                    'sticky': True,  # True/False will display for few seconds if false
                },
            }
            return notification
    def firmado_clip(self):
        for rec in self:
            if rec.partner_id.ofert_clip:
                conexion = self.env["api.credit.avalor"].search([('api', '=', 'clip')])
                url = ""
                api_key = ""
                for con in conexion:
                    url = con.url
                    api_key = con.consumer_key
                data = {
                  "status": "SIGNED",
                  "detail": "",
                  "date":  fields.Date.context_today(self).strftime('%Y-%m-%dT%H:%M:%SZ')
                }
                pre_approval_id = rec.partner_id.ofert_clip.pre_approval_id
                headers = {"Content-Type": "application/json", "x-api-key": api_key}
                json_text = data
                url_services = url + "/preapproval/" + pre_approval_id
                url_services = url_services.replace(" ", "")

                # headers['x-signature'] = key_handler.get_signature_from_private_key(json_text)
                r = requests.patch(url=url_services, data=json.dumps(json_text), headers=headers)
                r.encoding = 'utf-8'


                status_code = str(r.status_code)
                notification = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': status_code + " ",
                        'message': str(r.text),
                        'type': 'success',  # types: success,warning,danger,info
                        'sticky': True,  # True/False will display for few seconds if false
                    },
                }
                return notification
    def apagar_clip(self):
        for rec in self:
            if rec.partner_id.ofert_clip:
                conexion = self.env["api.credit.avalor"].search([('api', '=', 'clip')])
                url = ""
                api_key = ""
                for con in conexion:
                    url = con.url
                    api_key = con.consumer_key
                data = {
                  "status": "SENT_TO_DISBURSEMENT",
                  "detail": "",
                  "date":  fields.Date.context_today(self).strftime('%Y-%m-%dT%H:%M:%SZ')
                }
                pre_approval_id = rec.partner_id.ofert_clip.pre_approval_id
                headers = {"Content-Type": "application/json", "x-api-key": api_key}
                json_text = data
                url_services = url + "/preapproval/" + pre_approval_id
                url_services = url_services.replace(" ", "")
                # headers['x-signature'] = key_handler.get_signature_from_private_key(json_text)
                r = requests.patch(url=url_services, data=json.dumps(json_text), headers=headers)
                r.encoding = 'utf-8'


                status_code = str(r.status_code)
                notification = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': status_code + " ",
                        'message': str(r.text),
                        'type': 'success',  # types: success,warning,danger,info
                        'sticky': True,  # True/False will display for few seconds if false
                    },
                }
                return notification
    def pagado_clip(self):
        for rec in self:
            if rec.partner_id.ofert_clip:
                conexion = self.env["api.credit.avalor"].search([('api', '=', 'clip')])
                url = ""
                api_key = ""
                for con in conexion:
                    url = con.url
                    api_key = con.consumer_key
                data = {
                  "status": "DISBURSED",
                  "detail": "",
                  "date":  fields.Date.context_today(self).strftime('%Y-%m-%dT%H:%M:%SZ')
                }
                pre_approval_id = rec.partner_id.ofert_clip.pre_approval_id
                headers = {"Content-Type": "application/json", "x-api-key": api_key}
                json_text = data
                url_services = url + "/preapproval/" + pre_approval_id
                url_services = url_services.replace(" ", "")
                # headers['x-signature'] = key_handler.get_signature_from_private_key(json_text)
                r = requests.patch(url=url_services, data=json.dumps(json_text), headers=headers)
                r.encoding = 'utf-8'

                # rec.status_send_clip = str(r.text)
                status_code = str(r.status_code)
                notification = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': status_code + " ",
                        'message': str(r.text),
                        'type': 'success',  # types: success,warning,danger,info
                        'sticky': True,  # True/False will display for few seconds if false
                    },
                }
                return notification



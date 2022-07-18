import json
from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError
import base64
import requests

class apiscreditavalor(models.Model):
    _name = 'api.custom.clip.avalor'
    _description = "Envio de Cancelados y No aprovados"

    status = fields.Selection([('NOT_APPROVED', 'No Aprovado'), ('CANCELED', 'Cancelado'),
                                     ], string="Status", required=True)
    detail = fields.Selection([('DOCUMENT_EXPIRED', 'Documento Expirado'), ('DOCUMENT_NOT_READABLE', 'Documento No Legible'), ('DOCUMENT_NOT_VALID', 'Documento No Valido'),
                               ('DOCUMENT_NOT_SENT', 'Documento No Enviado'), ('CREDIT_HISTORY', 'Historial De Credito'),('FRAUD_PREVENTION', 'Prevencion de Fraude'),
                               ('NOT_SIGNED', 'No Firmado'), ('OTHER', 'Otro'),
                               ], string="Detalle", required=True)
    nota = fields.Text(string="Observaciones")

    def cancel_clip(self):
        for rec in self:
            if rec.ofert_clip:
                conexion = self.env["api.credit.avalor"].search([('api', '=', 'clip')])
                url = ""
                api_key = ""
                for con in conexion:
                    url = con.url
                    api_key = con.consumer_key
                # data = {
                #   "status": "NOT_APPROVED",
                #   "detail": "DOCUMENT_NOT_READABLE",
                #   "date":  fields.Date.context_today(self).strftime('%Y-%m-%dT%H:%M:%SZ')
                # }
                data = {
                    "status": "CANCELED",
                    "detail": "DOCUMENT_NOT_SENT",
                    "date": fields.Date.context_today(self).strftime('%Y-%m-%dT%H:%M:%SZ')
                }
                pre_approval_id = rec.ofert_clip.pre_approval_id
                headers = {"Content-Type": "application/json", "x-api-key": api_key}
                json_text = data
                url_services = url + "/preapproval/" + pre_approval_id+"/"
                url_services = url_services.replace(" ", "")
                # headers['x-signature'] = key_handler.get_signature_from_private_key(json_text)
                r = requests.patch(url_services, data=json.dumps(json_text), headers=headers)
                r.encoding = 'utf-8'
                r.text
                # rec.status_send_clip = str(r.text)
                status_code = str(r.status_code)
                if r.status_code == 200:
                    rec.process_sclip = "CANCELED"
                notification = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': status_code + " " + rec.process_sclip,
                        'message': r.text,
                        'type': 'success',  # types: success,warning,danger,info
                        'sticky': True,  # True/False will display for few seconds if false
                    },
                }
                return notification

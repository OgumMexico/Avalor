
import json
import logging
import os
import time
import base64
import requests
from requests.structures import CaseInsensitiveDict
from requests.auth import HTTPBasicAuth
from .key_handler import KeyHandler
#from . import key_handler as keyhean

from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError

class apiscreditavalor(models.Model):
    _name = 'api.credit.avalor'
    _description = "Apis Instances"

    name = fields.Char(string="Nombre de Instancia", required=True)
    color = fields.Integer('Color')
    consumer_key = fields.Char(string="Key o ID")
    consumer_secret = fields.Char(string="Secret o Clave API")
    is_test = fields.Boolean(string="Es Prueba")
    archivo_key = fields.Binary(string=_('Key privavada'))
    archivo_cer = fields.Binary(string=_('Certificado'))
    archivo_keypar = fields.Binary(string=_('Keypair'))
    api = fields.Selection(
        selection=[("Circulo_Credito", "Circulo de Credito"),("stpmex", "STP MEX"),("clip", "CLIP"),("metamap","Metamap")],
        string="Tipo de Api Conexion")

    url = fields.Char(string="Url Conexion", readonly=True, compute="_compute_api",)


    def _compute_api(self):
        for api in self:
            if api.is_test:
                if api.api == "Circulo_Credito":
                    api.url = "https://services.circulodecredito.com.mx/sandbox"
                elif api.api == "WEESIGN2":
                    api.url = "https://api-sandbox.weesign.com.mx"
                elif api.api == "stpmex":
                    api.url = "https://demo.stpmex.com:7024/speiws/rest"
                elif api.api == "clip":
                    api.url = "https://testapi-gw.payclip.com/loans"
                elif api.api == "metamap":
                    api.url = "https://api.getmati.com"
                else:
                    api.url = "Sin URL"

            else:
                if api.api == "Circulo_Credito":
                    api.url = "services.circulodecredito.com.mx"
                elif api.api == "WEESIGN2":
                    api.url = "https://api-gw.weesign.mx/"
                elif api.api == "stpmex":
                    api.url = "https://services.circulodecredito.com.mx/sandbox/"
                elif api.api == "clip":
                    api.url = "https://api-gw.payclip.com/loans"
                elif api.api == "metamap":
                    api.url = "https://api.getmati.com"
                else:
                    api.url = "Sin URL"

    def get_instance(self):
        """
        function is used for returning
        current form view of instance.

        """
        return {
            'name': _('Instance'),
            'view_mode': 'form',
            'res_model': 'api.credit.avalor',
            'res_id': self.id,
            'domain': [],
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'current',

        }

    def get_wizard(self):
        for api in self:
           status_code=""
           url = api. url
           key = api.consumer_key
           clave = api.consumer_secret
           pathkeypa = api.archivo_keypar
           pathKey = api.archivo_key
           pathCer = api.archivo_cer

           if api.api == "Circulo_Credito":
               jsonRequest = {"folio": 123456,
                                  "persona": {
                                      "nombres": "JUAN",
                                      "apellidoPaterno": "PRUEBA",
                                      "apellidoMaterno": "CUATRO",
                                      "fechaNacimiento": "1980-01-04",
                                      "RFC": "PUCJ800104",
                                      "domicilio": {
                                          "direccion": "INSURGENTES SUR 1004",
                                          "coloniaPoblacion": "INSURGENTES",
                                          "ciudad": "BENITO JUAREZ",
                                          "CP": "11230",
                                          "delegacionMunicipio": "BENITO JUAREZ",
                                          "estado": "DF"
                                      }
                                  }
                            }

               file_content = base64.b64decode(pathkeypa)

               # return notification
               # jsonRequest = '{"folio": 123456,  "persona": {"nombres": "JUAN","apellidoPaterno": "PRUEBA","apellidoMaterno": "CUATRO","fechaNacimiento": "1980-01-04","RFC": "PUCJ800104","domicilio": {"direccion": "INSURGENTES SUR 1004","coloniaPoblacion": "INSURGENTES","ciudad": "BENITO JUAREZ","CP": "11230","delegacionMunicipio": "BENITO JUAREZ","estado": "DF" }}}'
               json_text = str(jsonRequest)
               key_handler = KeyHandler(base64.b64decode(pathkeypa), base64.b64decode(pathCer), "avalor2020")
               firma = key_handler.get_signature_from_private_key(json_text)
               headers = {"Content-Type": "application/json", "x-api-key": key, "x-signature": firma}



               # headers['x-signature'] = firma json.dumps(jsonRequest)
               url_services = url + "/v2/ficoextended"

               #headers['x-signature'] = key_handler.get_signature_from_private_key(json_text)
               r = requests.post(url=url_services, data=json.dumps(jsonRequest), headers=headers)
               r.encoding = 'utf-8'

               status_code = str(r.status_code)
               # try:
               #     self.logger.info("RESPONSE ---->" + r.text)
               #     self.logger.info(key_handler.get_verification_from_public_key(r.text, r.headers['x-signature']))
               #     validate = key_handler.get_verification_from_public_key(r.text, r.headers['x-signature'])
               # except Exception as e:
               #     json_resp = ""
               #
               #     raise UserError(_(e))
               #     validate = False

               notification = {
                   'type': 'ir.actions.client',
                   'tag': 'display_notification',
                   'params': {
                       'title': status_code ,
                       'message': str(r.text) ,
                       'type': 'success',  # types: success,warning,danger,info
                       'sticky': True,  # True/False will display for few seconds if false
                   },
               }
               return notification
           if api.api == "clip":
               jsonRequest = {}
               self.logger = logging.getLogger('SingleTest')
               file_content = base64.b64decode(pathkeypa)

               # return notification

               key_handler = KeyHandler(base64.b64decode(pathkeypa), base64.b64decode(pathCer), "avalor2020")
               headers = {"Content-Type": "application/json", "x-api-key": key, "x-signature": None}
               json_text = jsonRequest
               url_services = url + "/components/schemas/Preapproval"

               # headers['x-signature'] = key_handler.get_signature_from_private_key(json_text)
               r = requests.post(url=url_services, data=json.dumps(json_text), headers=headers)
               r.encoding = 'utf-8'

               status_code = str(r.status_code)
               notification = {
                   'type': 'ir.actions.client',
                   'tag': 'display_notification',
                   'params': {
                       'title': status_code,
                       'message': r.text,
                       'type': 'success',  # types: success,warning,danger,info
                       'sticky': True,  # True/False will display for few seconds if false
                   },
               }
               return notification
           if api.api == "metamap":
               payload = "grant_type=client_credentials"
               headers = CaseInsensitiveDict()
               # headers = HTTPBasicAuth(key,clave)
               # userAndPass = base64.b64encode(b"username:password").decode("ascii")
               headers["Accept"] = "application/json"

               headers["Content-Type"] = "application/x-www-form-urlencoded"
               authstr = 'Basic ' +  base64.b64encode(b':'.join((key.encode('latin1'), clave.encode('latin1')))).decode("utf-8").strip()
               headers["Authorization"] = authstr
               r = requests.post(url+"/oauth", data=payload, headers=headers)
               r.encoding = 'utf-8'

               status_code = str(r.status_code)
               datos = r.json()

           notification = {
               'type': 'ir.actions.client',
               'tag': 'display_notification',
               'params': {
                   'title': status_code,
                   'message':datos['access_token'],
                   'type': 'success',  # types: success,warning,danger,info
                   'sticky': True,  # True/False will display for few seconds if false
               },
           }
           return notification






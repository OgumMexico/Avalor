import json
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

import logging
import os
import re
import time
import base64
import requests
import sys
import hashlib
from .key_handler import KeyHandler
# import subprocess
import OpenSSL
import jks
from OpenSSL import crypto

_ASN1 = OpenSSL.crypto.FILETYPE_ASN1

from subprocess import PIPE, run

def out(command):
    result = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True)
    return result.stdout

class av_activ_economics(models.Model):
    _name = "av.actividad.economica"
    _inherit = ['mail.thread']
    id_stp = fields.Integer(string="Id STP", track_visibility='onchange')
    name = fields.Char(string="Nombre", track_visibility='onchange')

class Rescountry_av(models.Model):
    _inherit = "res.country"
    id_stp = fields.Integer(string="Id STP")

class ResPartnerbank(models.Model):
    _inherit = "res.partner.bank"

    clabe_inti = fields.Integer(string="Clave Institución")
    type_cuenta = fields.Selection([('3', 'Tarjeta de Debito'), ('10', 'Teléfono celular'), ('40', 'CLABE')
                                    ], string="Tipo de Cuenta")
    rfc = fields.Char(string="rfc")
    bankname = fields.Char(string="Nombre Banco")
    holder_name = fields.Char(string="Holder name")

class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def _default_company(self):
        company_id = self._context.get('force_company', self._context.get('default_company_id', self.env.company.id))
        return company_id


    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=_default_company,
        readonly=True,

    )



    merchan = fields.Char(string="Merchant token", default="/")
    # merchan_id = fields.Char(string="Id Interno", default="/", readonly=True)
    merchan_id = fields.Char(string="Id Interno", default="/")

    ac_economic = fields.Many2one(comodel_name="av.actividad.economica", string="Actividad Economica")
    ofert_clip = fields.Many2one(comodel_name="clip.preapproval", string="Oferta Elegida")
    curp = fields.Char(string="Curp")
    number_adi = fields.Text(string="Telefonos Adicionales")
    ine_pasas = fields.Binary("Ine o Pasaporte")
    ine = fields.Binary("Ine")
    comp_domi = fields.Binary("Comprobante de Domicilio")
    status_send_clip = fields.Text(string="Status Clip")
    status_send_meta = fields.Text(string="Status Metamap")
    status_meta = fields.Text(string="Status Metamap")
    cuenta_clabe_stp = fields.Char(string="Cuenta Clabe STP", compute="get_cuenta_clabe")

    url_metamap = fields.Char(string="URL Metamap")

    colonia = fields.Char(string="Colonia")
    delegacion = fields.Char(string="Delegacion")

    credito_id = fields.One2many(comodel_name="credito", string="Credito",inverse_name="partner_id")
    score_id = fields.One2many(comodel_name="credito.score", string="Score",inverse_name="partner_id")
    consultas_id = fields.One2many(comodel_name="credito.consultas", string="consultas",inverse_name="partner_id")
    empleos_id = fields.One2many(comodel_name="credito.empleos", string="empleos",inverse_name="partner_id")
    domicilios_id = fields.One2many(comodel_name="credito.domicilios", string="domicilios",inverse_name="partner_id")
    creditos_id = fields.One2many(comodel_name="credito.creditos", string="creditos",inverse_name="partner_id")

    status_sclip = fields.Integer(string="Envio de Status", compute="com_sendstatus")
    process_sclip = fields.Char(string="Proceso Clip", default="/")

    def get_default_name_m(self, vals):
        return self.env["ir.sequence"].next_by_code("partner.merchant") or "/"



    @api.model
    def create(self, vals):
        if vals.get("merchan") != "/" and vals.get("merchan_id","/") == "/":
            vals["merchan_id"] = self.get_default_name_m(vals)
        return super().create(vals)

    def pdf_credit(self):
        for rec in self:
            fecha = '2022-03-04'
            name = 'p002'
            json  = 'json'
            a = "cd /odoo/custom/addons/avalor_credit/models/; java -jar GeneraPDF.jar '"+ fecha +"' '/tmp/" + name +".pdf' "+ json+".txt"
            # os.system("python3 /odoo/custom/addons/avalor_credit/models/genpdf.py '2022-03-04' 'pdf001' 'json'")
            my_output = out("echo hello world")
            # proc = subprocess.Popen(["python3", "/odoo/custom/addons/avalor_credit/models/genpdf.py '2022-03-04' 'pdf001' 'json'"], stdout=subprocess.PIPE, shell=True)
            # mjs = out("python3 /odoo/custom/addons/avalor_credit/models/genpdf.py '2022-03-04' 'pdf001' 'json'")
            mjs = out(a)
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': my_output,
                    'message': mjs,
                    'type': 'success',  # types: success,warning,danger,info
                    'sticky': True,  # True/False will display for few seconds if false
                },
            }
            return notification

    @api.depends("company_id","merchan_id")


    def get_cuenta_clabe(self):
        for rec in self:
            cuenta= []
            ponderacion=[3,	7,	1,	3,	7,	1,	3,	7,	1,	3,	7,	1,	3,	7,	1,	3,	7]
            posicion=[]
            mod10=[]
            ac = 0
            cuenta_clabe = ""
            if rec.company_id and rec.merchan_id != "/":
                stp = rec.company_id.stp
                stp_pais = rec.company_id.stp_pais
                stp_clinte = rec.company_id.stp_clinte
                stp_producto = rec.company_id.stp_producto
                stp_cliente = rec.merchan_id
                stp = str(stp) + str(stp_pais) + str(stp_clinte) + str(stp_producto) + str(stp_cliente)

                for let in str(stp):
                    cuenta.append(int(let))
                    ac = ac + 1
                '''for let in str(stp_pais):
                    cuenta.append(int(let))
                    ac = ac + 1
                for let in str(stp_clinte):
                    cuenta.append(int(let))
                    ac = ac + 1
                for let in str(stp_producto):
                    cuenta.append(int(let))
                    ac = ac + 1
                for let in str(stp_cliente):
                    cuenta.append(int(let))
                    ac = ac + 1 '''
                pn = 0
                if cuenta:
                    for pon in ponderacion:
                        posi = pon * cuenta[pn]
                        rest, mod = divmod(posi,10)
                        posicion.append(int(posi))
                        mod10.append(mod)
                        pn = pn + 1
                    sum_acou= 0
                    for md in mod10:
                        sum_acou = sum_acou + md
                    resd, mod = divmod(sum_acou,10)
                    cuenta.append(int(10 - mod))

                    for cuen in cuenta:
                        cuenta_clabe += str(cuen)

            rec.cuenta_clabe_stp = cuenta_clabe


    @api.onchange("merchan")
    def valid_merchan(self):
        for res in self:
            if res.merchan != "/" and res.merchan_id == "/":
                res.merchan_id = self.get_default_name_m(res)


    def com_sendstatus(self):
        for rec in self:
            rec.valid_merchan()
            if rec.status_sclip == 0 and rec.ofert_clip and rec.process_sclip == "/":
                c = rec.send_notificationofer()
                # raise UserError(c)
                rec.status_sclip = c
            elif rec.process_sclip == "IN_ANALYSIS":
                rec.status_sclip = 1
            elif rec.process_sclip == "APPROVED":
                rec.status_sclip = 2
            elif rec.process_sclip == "FOR_SIGN_OFF":
                rec.status_sclip = 3
            elif rec.process_sclip == "NOT_APPROVED":
                rec.status_sclip = -1
            elif rec.process_sclip == "CANCELED":
                rec.ofert_clip = False
                rec.process_sclip = "/"
                rec.status_sclip = 0

            else:
                rec.status_sclip = 0

    @api.onchange("ofert_clip")
    def cron_sendstatus(self):
        for rec in self:

            if rec.status_sclip == 0 and rec.ofert_clip and rec.process_sclip == "/":
                c = rec.send_notificationofer()
                # raise UserError(c)
                rec.status_sclip = c
            elif rec.process_sclip == "IN_ANALYSIS":
                rec.status_sclip = 1
            elif rec.process_sclip == "APPROVED":
                rec.status_sclip = 2
            elif rec.process_sclip == "FOR_SIGN_OFF":
                rec.status_sclip = 3
            elif rec.process_sclip == "NOT_APPROVED":
                rec.status_sclip = -1
            elif rec.process_sclip == "CANCELED":
                rec.status_sclip = -2
            else:
                rec.status_sclip = 0


    def send_notificationofer(self):
        for rec in self:

                conexion = self.env["api.credit.avalor"].search([('api', '=', 'clip')])
                url = ""
                api_key = ""
                for con in conexion:
                    url = con.url
                    api_key = con.consumer_key
                data = {
                  "status": "IN_ANALYSIS",
                  "detail": "",
                  "date":  fields.Date.context_today(self).strftime('%Y-%m-%dT%H:%M:%SZ')
                }
                pre_approval_id = rec.ofert_clip.pre_approval_id
                headers = {"Content-Type": "application/json", "x-api-key": api_key}
                json_text = data
                url_services = url + "/preapproval/" + pre_approval_id

                # headers['x-signature'] = key_handler.get_signature_from_private_key(json_text)
                r = requests.patch(url=url_services, data=json.dumps(json_text), headers=headers)
                r.encoding = 'utf-8'
                rec.status_send_clip = str(r.text)

                if r.status_code == 200:
                    rec.process_sclip = "IN_ANALYSIS"
                    return 1
                else:
                    return 0

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

    def noaprobado_clip(self):
        for rec in self:
            if rec.ofert_clip:
                conexion = self.env["api.credit.avalor"].search([('api', '=', 'clip')])
                url = ""
                api_key = ""
                for con in conexion:
                    url = con.url
                    api_key = con.consumer_key
                data = {
                  "status": "NOT_APPROVED",
                  "detail": "DOCUMENT_NOT_READABLE",
                  "date":  fields.Date.context_today(self).strftime('%Y-%m-%dT%H:%M:%SZ')
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
                    rec.process_sclip = "NOT_APPROVED"
                notification = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': status_code + " "+ rec.process_sclip,
                        'message': r.text,
                        'type': 'success',  # types: success,warning,danger,info
                        'sticky': True,  # True/False will display for few seconds if false
                    },
                }
                return notification
    def aprobado_clip(self):
        for rec in self:
            if rec.ofert_clip:
                conexion = self.env["api.credit.avalor"].search([('api', '=', 'clip')])
                url = ""
                api_key = ""
                for con in conexion:
                    url = con.url
                    api_key = con.consumer_key
                data = {
                  "status": "APPROVED",
                  "detail": "",
                  "date":  fields.Date.context_today(self).strftime('%Y-%m-%dT%H:%M:%SZ')
                }
                pre_approval_id = rec.ofert_clip.pre_approval_id
                headers = {"Content-Type": "application/json", "x-api-key": api_key}
                json_text = data
                url_services = url + "/preapproval/" + pre_approval_id
                url_services = url_services.replace(" ", "")
                # headers['x-signature'] = key_handler.get_signature_from_private_key(json_text)
                r = requests.patch(url=url_services, data=json.dumps(json_text), headers=headers)
                r.encoding = 'utf-8'

                # rec.status_send_clip = str(r.text)
                status_code = str(r.status_code)
                if r.status_code == 200:
                    rec.process_sclip = "APPROVED"
                notification = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': status_code + " " +str(rec.status_sclip),
                        'message': str(r.text),
                        'type': 'success',  # types: success,warning,danger,info
                        'sticky': True,  # True/False will display for few seconds if false
                    },
                }
                return notification
    def firma_clip(self):
        for rec in self:
            if rec.ofert_clip:
                conexion = self.env["api.credit.avalor"].search([('api', '=', 'clip')])
                url = ""
                api_key = ""
                for con in conexion:
                    url = con.url
                    api_key = con.consumer_key
                data = {
                  "status": "FOR_SIGN_OFF",
                  "detail": "",
                  "date":  fields.Date.context_today(self).strftime('%Y-%m-%dT%H:%M:%SZ')
                }
                pre_approval_id = rec.ofert_clip.pre_approval_id
                headers = {"Content-Type": "application/json", "x-api-key": api_key}
                json_text = data
                url_services = url + "/preapproval/" + pre_approval_id
                url_services = url_services.replace(" ", "")
                # headers['x-signature'] = key_handler.get_signature_from_private_key(json_text)
                r = requests.patch(url=url_services, data=json.dumps(json_text), headers=headers)
                r.encoding = 'utf-8'

                # rec.status_send_clip = str(r.text)
                status_code = str(r.status_code)
                if r.status_code == 200:
                    rec.process_sclip = "FOR_SIGN_OFF"
                notification = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': status_code + " "+ rec.process_sclip,
                        'message': str(r.text),
                        'type': 'success',  # types: success,warning,danger,info
                        'sticky': False,  # True/False will display for few seconds if false
                    },
                }
                return notification

    primerNombre = fields.Char(string="Nombres")
    apellidoPaterno = fields.Char(string="Apellido Paterno")
    apellidoMaterno = fields.Char(string="Apellido Materno")
    fechaNacimiento = fields.Date(string="Fecha Nacimiento")
    nacionalidad = fields.Many2one(comodel_name="res.country", string="Nacionalidad")
    def Get_reportcredit(self):
        for rec in self:

            conexion = self.env["api.credit.avalor"].search([('api', '=', 'Circulo_Credito')])
            url = ""
            key = ""
            pathkeypa = ""
            pathCer = ""
            for con in conexion:
                url = con.url
                key = con.consumer_key
                clave = con.consumer_secret
                pathkeypa = con.archivo_keypar
                pathKey = con.archivo_key
                pathCer = con.archivo_cer
            apellidoPaterno = ""
            if rec.apellidoPaterno:
                apellidoPaterno = rec.apellidoPaterno.upper()
            apellidoMaterno=""
            if rec.apellidoMaterno:
                apellidoMaterno = rec.apellidoMaterno.upper()
            primerNombre = ""
            if rec.primerNombre:
                primerNombre = rec.primerNombre.upper()
            vat = ""

            if rec.vat:
                vat = rec.vat.upper()
            street = ""

            if rec.street:
                street = rec.street.upper()
            colonia = ""
            if rec.colonia:
                colonia = rec.colonia.upper()
            delegacion = ""
            if rec.delegacion:
                delegacion = rec.delegacion.upper()
            city = ""
            if rec.city:
                city = rec.city.upper()


            jsonRequest ={

              "apellidoPaterno": apellidoPaterno,
              "apellidoMaterno": apellidoMaterno,
              "primerNombre": primerNombre,
              "fechaNacimiento": rec.fechaNacimiento.strftime('%Y-%m-%d') or "",
              "RFC": vat,
              "nacionalidad": rec.nacionalidad.code or "",
              "domicilio": {
                "direccion": street,
                "coloniaPoblacion": colonia,
                "delegacionMunicipio": delegacion,
                "ciudad": city,
                "estado": rec.state_id.code or "",
                "CP": rec.zip,
              }
            }

            json_text = str(jsonRequest)
            key_handler = KeyHandler(base64.b64decode(pathkeypa), base64.b64decode(pathCer), "avalor2020")
            firma = key_handler.get_signature_from_private_key(json_text)
            headers = {"Content-Type": "application/json","x-api-key": key, "x-signature": firma, "x-full-report":"true"}
            url_services = url + "/v1/rcc-ficoscore-pld"
            r = requests.post(url=url_services, data=json.dumps(jsonRequest), headers=headers)
            r.encoding = 'utf-8'

            status_code = str(r.status_code)
            data = r.json()
            credito = []
            score = []
            empleos = []
            creditos = []
            direcciones = []
            consultas = []
            if data:
                credito.append([0, 0, {
                    "folioConsulta": str(data["folioConsulta"]),
                    "folioConsultaOtorgante": str(data["folioConsultaOtorgante"]),
                    "claveOtorgante": str(data["claveOtorgante"]),
                    "declaracionesConsumidor": data["declaracionesConsumidor"],
                    "partner_id": rec.id

                }])
                for sc in data["scores"]:
                    score.append([0, 0, {
                        "name": str(sc["nombreScore"]),
                        "valor": str(sc["valor"]),
                        "razones": str(sc["razones"]),
                        "partner_id": rec.id

                    }])
                for con in data["consultas"]:
                    tel = ""
                    try:
                        tel = con["telefonoOtorgante"]
                    except:
                        tel = ""

                    try:
                        con["claveUnidadMonetaria"]
                    except:
                        con["claveUnidadMonetaria"] = ""

                    consultas.append([0, 0, {
                        "fechaConsulta": str(con["fechaConsulta"]),
                        "nombreOtorgante": str(con["nombreOtorgante"]),
                        "telefonoOtorgante": tel,
                        "tipoCredito": con["tipoCredito"],
                        "claveUnidadMonetaria": con["claveUnidadMonetaria"],
                        "importeCredito": con["importeCredito"],
                        "partner_id": rec.id

                    }])
                for con in data["empleos"]:
                    empleos.append([0, 0, {
                        "nombreEmpresa": str(con["nombreEmpresa"]),
                        "direccion": str(con["direccion"]),
                        "coloniaPoblacion": str(con["coloniaPoblacion"]),
                        "delegacionMunicipio": con["delegacionMunicipio"],
                        "ciudad": con["ciudad"],
                        "estado": con["estado"],
                        "CP": con["CP"],
                        "numeroTelefono": con["numeroTelefono"],
                        "extension": con["extension"],
                        "fax": con["fax"],
                        "puesto": con["puesto"],
                        "fechaContratacion": con["fechaContratacion"],
                        "claveMoneda": con["claveMoneda"],
                        "salarioMensual": con["salarioMensual"],
                        "fechaUltimoDiaEmpleo": con["fechaUltimoDiaEmpleo"],
                        "fechaVerificacionEmpleo": con["fechaVerificacionEmpleo"],
                        "partner_id": rec.id

                    }])
                for con in data["domicilios"]:


                    direcciones.append([0, 0, {

                        "direccion": str(con["direccion"]),
                        "coloniaPoblacion": str(con["coloniaPoblacion"]),
                        "delegacionMunicipio": str(con["delegacionMunicipio"]),
                        "ciudad": con["ciudad"],
                        "estado": con["estado"],
                        "CP": con["CP"],
                        "fechaResidencia": con["fechaResidencia"],
                        "fechaRegistroDomicilio": con["fechaRegistroDomicilio"],
                        "partner_id": rec.id

                    }])
                for con in data["creditos"]:
                    try:
                        con["fechaCierreCuenta"]
                    except:
                        con["fechaCierreCuenta"] = ""
                    try:
                        con["garantia"]
                    except:
                        con["garantia"] = ""
                    try:
                        con["clavePrevencion"]
                    except:
                        con["clavePrevencion"] = ""
                    try:
                        con["totalPagosReportados"]
                    except:
                        con["totalPagosReportados"] = "0"
                    try:
                        con["montoUltimoPagoid"]
                    except:
                        con["montoUltimoPagoid"] = "0"
                    try:
                        con["cuentaActual"]
                    except:
                        con["cuentaActual"] = ""

                    try:
                        con["valorActivoValuacion"]
                    except:
                        con["valorActivoValuacion"] = ""
                    try:
                        con["numeroPagos"]
                    except:
                        con["numeroPagos"] = 0
                    try:
                        con["peorAtraso"]
                    except:
                        con["peorAtraso"] = 0
                    try:
                        con["fechaPeorAtraso"]
                    except:
                        con["fechaPeorAtraso"] = ""
                    try:
                        con["saldoVencidoPeorAtraso"]
                    except:
                        con["saldoVencidoPeorAtraso"] = 0
                    try:
                        con["historicoPagos"]
                    except:
                        con["historicoPagos"] = ""

                    creditos.append([0, 0, {
                        "fechaActualizacion": str(con["fechaActualizacion"]),
                        "registroImpugnado": str(con["registroImpugnado"]),

                        "nombreOtorgante": con["nombreOtorgante"],
                        "cuentaActual": con["cuentaActual"],
                        "tipoResponsabilidad": con["tipoResponsabilidad"],
                        "tipoCuenta": con["tipoCuenta"],
                        "tipoCredito": con["tipoCredito"],
                        "claveUnidadMonetaria": con["claveUnidadMonetaria"],
                        "valorActivoValuacion": con["valorActivoValuacion"],
                        "numeroPagos": con["numeroPagos"],
                        "frecuenciaPagos": con["frecuenciaPagos"],
                        "montoPagar": con["montoPagar"],
                        "fechaAperturaCuenta": con["fechaAperturaCuenta"],
                        "fechaUltimoPago": con["fechaUltimoPago"],
                        "fechaUltimaCompra": con["fechaUltimaCompra"],
                        "fechaCierreCuenta": con["fechaCierreCuenta"],
                        "fechaReporte": con["fechaReporte"],
                        "garantia": con["garantia"],
                        "creditoMaximo": con["creditoMaximo"],
                        "saldoActual": con["saldoActual"],
                        "limiteCredito": con["limiteCredito"],
                        "saldoVencido": con["saldoVencido"],
                        "numeroPagosVencidos": con["numeroPagosVencidos"],
                        "pagoActual": con["pagoActual"],
                        "historicoPagos": con["historicoPagos"],

                        "clavePrevencion": con["clavePrevencion"],
                        "totalPagosReportados": con["totalPagosReportados"],
                        "peorAtraso": con["peorAtraso"],
                        "fechaPeorAtraso": con["fechaPeorAtraso"],
                        "saldoVencidoPeorAtraso": con["saldoVencidoPeorAtraso"],
                        "montoUltimoPagoid": con["montoUltimoPagoid"],



                        "partner_id": rec.id

                    }])


                self.write({"credito_id": credito})
                self.write({"score_id": score})
                self.write({"empleos_id": empleos})
                self.write({"creditos_id": creditos})
                self.write({"domicilios_id": direcciones})
                self.write({"consultas_id": consultas})

            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': data["folioConsulta"],
                    'message': credito,
                    'type': 'success',  # types: success,warning,danger,info
                    'sticky': True,  # True/False will display for few seconds if false
                },
            }
            return notification




class res_companystp(models.Model):
    _inherit = "res.company"

    name_stp= fields.Char(string="Nombre Resgistrado")
    type_cuenta = fields.Selection([('3', 'Tarjeta de Debito'), ('10', 'Teléfono celular'), ('40', 'CLABE')
                                ], string="Tipo de Cuenta")
    clabe_inti = fields.Char(string="Clave Institución")
    cuentaOrdenante = fields.Char(string="Cuenta de banco")

    stp = fields.Char(string="Cuenta STP", defaut="646")
    stp_pais = fields.Char(string="Cuenta STP Pais", defaut="180")
    stp_clinte = fields.Char(string="Cuenta STP Clinte", defaut="2988")
    stp_producto = fields.Char(string="Cuenta STP Producto", defaut="0")



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

    def cosuta_saldoSTP(self):
        for rec in self:
            fecha = str(fields.Date.context_today(self).strftime('%Y%m%d'))


            empresa = rec.name
            # cadena = "||"+ empresa + "|" + rec.cuentaOrdenante + fecha + "||"
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
            datos_stp = {
                "cuentaOrdenante": rec.cuentaOrdenante,
                "firma": firma.decode("utf-8")
            }

            headers = {"Content-Type": "application/json"}
            json_text = json.dumps(datos_stp)
            url_services = url + "/ordenPago/consSaldoCuenta"

            r = requests.post(url=url_services, data=json_text, headers=headers)
            r.encoding = 'utf-8'

            status_code = str(r.status_code)

            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': status_code ,
                    'message': str(r.text),
                    'type': 'success',  # types: success,warning,danger,info
                    'sticky': True,  # True/False will display for few seconds if false
                },
            }
            return notification

    def cosuta_saldoHSTP(self):
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



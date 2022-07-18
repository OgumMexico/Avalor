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
import OpenSSL
import jks
from OpenSSL import crypto
import base64
from cryptography.hazmat.primitives import serialization, hashes

_ASN1 = OpenSSL.crypto.FILETYPE_ASN1

class Credito(models.Model):
    _name = 'credito'
    _description = 'Consuta de Buro de Credito'

    partner_id = fields.Many2one(comodel_name="res.partner", string="Cliente")
    folioConsulta = fields.Char(string="Folio Consulta")
    folioConsultaOtorgante = fields.Char(string="Folio Otorgante")
    claveOtorgante = fields.Char(string="Clave")
    declaracionesConsumidor = fields.Char(string="Declaraciones")

class Credito_Score(models.Model):
    _name = 'credito.score'
    _description = 'Score de Calificacion'

    partner_id = fields.Many2one(comodel_name="res.partner", string="Cliente")
    name = fields.Char(string="Nombre")
    valor = fields.Char(string="Valor")
    razones = fields.Char(string="Razones")

class Credito_consultas(models.Model):
    _name = 'credito.consultas'
    _description = 'Consultas de Buro de credito'

    partner_id = fields.Many2one(comodel_name="res.partner", string="Cliente")
    fechaConsulta = fields.Date(string="Fecha")


    nombreOtorgante = fields.Char(string="Nombre")

    telefonoOtorgante = fields.Char(string="Telefono")
    # Tipo de credito crear su modelo
    tipoCredito = fields.Char(string="Tipo de Credito")
    claveUnidadMonetaria = fields.Char(string="Moneda")
    importeCredito = fields.Float(string="Importe")
    # tipo de responsabilidad ?


class Credito_empleos(models.Model):
    _name = 'credito.empleos'
    _description = 'Empleos registrados'

    partner_id = fields.Many2one(comodel_name="res.partner", string="Cliente")
    nombreEmpresa = fields.Char(string="Empresa")
    direccion = fields.Char(string="Direccion")
    coloniaPoblacion = fields.Char(string="Colonia")
    delegacionMunicipio = fields.Char(string="Municipio")
    ciudad = fields.Char(string="Ciudad")
    estado = fields.Char(string="Estado")
    CP = fields.Char(string="CP")
    numeroTelefono = fields.Char(string="Telefono")
    extension = fields.Char(string="Extencion")
    fax = fields.Char(string="Fax")
    puesto = fields.Char(string="Puesto")
    fechaContratacion = fields.Char(string="Fecha de Contratacion")
    claveMoneda = fields.Char(string="Moneda")
    salarioMensual = fields.Float(string="Salario Mensual")
    fechaUltimoDiaEmpleo = fields.Date(string="Ultimo dia de Empleo")
    fechaVerificacionEmpleo = fields.Date(string="Verificacion de empleo")


class Credito_Domicilios(models.Model):
    _name = 'credito.domicilios'
    _description = 'Domicilios Fiscales y Usados'

    partner_id = fields.Many2one(comodel_name="res.partner", string="Cliente")
    direccion = fields.Char(string='Direccion')
    coloniaPoblacion = fields.Char(string='Colonia')
    delegacionMunicipio = fields.Char(string='Municipio')
    ciudad = fields.Char(string='Ciudad')
    estado = fields.Char(string='Estado')
    CP = fields.Char(string='CP')
    fechaResidencia = fields.Date(string='Fecha Residencia')
    fechaRegistroDomicilio = fields.Date(string='Registro Domicilio')


class Credito_creditos(models.Model):
    _name = 'credito.creditos'
    _description = 'Domicilios Fiscales y Usados'

    partner_id = fields.Many2one(comodel_name="res.partner", string="Cliente")
    fechaActualizacion = fields.Date(string='Fecha Actualizacion')
    registroImpugnado = fields.Char(string='Registro Impugnado')
    nombreOtorgante = fields.Char(string='Nombre Otorgante')
    cuentaActual = fields.Char(string='Cuenta Actual')
    # MODELO
    tipoResponsabilidad = fields.Char(string='TipoResponsabilidad')
    # MODELO
    tipoCuenta = fields.Char(string='Tipo Cuenta')
    # MODELO
    tipoCredito = fields.Char(string='Tipo Credito')
    claveUnidadMonetaria = fields.Char(string='Moneda')
    valorActivoValuacion = fields.Char(string='Valor Activo Valuacion')
    numeroPagos = fields.Integer(string='Pagos')
    # modelo
    frecuenciaPagos = fields.Char(string='Frecuencia Pagos')
    montoPagar = fields.Float(string='Monto Pagar')
    fechaAperturaCuenta = fields.Date(string='Apertura Cuenta')
    fechaUltimoPago = fields.Date(string='Ultimo Pago')
    fechaUltimaCompra = fields.Date(string='Ultima Compra')
    fechaCierreCuenta = fields.Char(string='Cierre Cuenta')
    fechaReporte = fields.Date(string='Reporte')

    garantia = fields.Char(string='Garantia')
    creditoMaximo = fields.Float(string='Credito Maximo')
    saldoActual = fields.Float(string='Saldo Actual')
    limiteCredito = fields.Float(string='Limite Credito')
    saldoVencido = fields.Float(string='Saldo Vencido')
    numeroPagosVencidos = fields.Integer(string='Pagos Vencidos')
    pagoActual = fields.Char(string='Pago Actual')
    historicoPagos = fields.Char(string='Historico Pagos')

    clavePrevencion = fields.Char(string='clavePrevencion')
    totalPagosReportados = fields.Integer(string='totalPagosReportados')
    peorAtraso = fields.Integer(string='peorAtraso')
    fechaPeorAtraso = fields.Char(string='fechaPeorAtraso')
    saldoVencidoPeorAtraso = fields.Float(string='saldoVencidoPeorAtraso')
    montoUltimoPagoid = fields.Float(string='montoUltimoPagoid')



    id_can = fields.Char(string='Id Can')
    prelacionOrigen = fields.Char(string='prelacion Origen')
    prelacionActual = fields.Char(string='prelacion Actual')
    fechaAperturaCAN = fields.Char(string='Apertura CAN')
    fechaCancelacionCAN = fields.Char(string='Cancelacion CAN')
    historicoCAN = fields.Char(string='Historico CAN')
    fechaMRCAN = fields.Char(string='MR CAN')
    fechaMACAN = fields.Char(string='MA CAN')
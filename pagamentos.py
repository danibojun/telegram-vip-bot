import os
import logging
import mercadopago
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class Pagamentos:
    def __init__(self):
        self.access_token = os.getenv('MERCADO_PAGO_ACCESS_TOKEN')
        if not self.access_token:
            logger.error("MERCADO_PAGO_ACCESS_TOKEN não encontrado nas variáveis de ambiente")
            raise ValueError("MERCADO_PAGO_ACCESS_TOKEN não configurado")
        self.sdk = mercadopago.SDK(self.access_token)
        logger.info("Cliente Mercado Pago inicializado")

    def criar_pagamento_pix(self, valor, descricao):
        try:
            logger.info(f"Criando pagamento PIX: valor={valor}, descrição={descricao}")
            payment_data = {
                "transaction_amount": float(valor),
                "description": descricao,
                "payment_method_id": "pix",
                "payer": {
                    "email": "pagador@email.com",
                    "first_name": "Cliente",
                    "last_name": "VIP"
                }
            }
            
            logger.debug(f"Dados do pagamento: {payment_data}")
            payment_response = self.sdk.payment().create(payment_data)
            logger.debug(f"Resposta completa do Mercado Pago: {payment_response}")
            
            if payment_response["status"] != 201:
                error_msg = f"Erro ao criar pagamento: {payment_response.get('response', {}).get('message', 'Erro desconhecido')}"
                logger.error(error_msg)
                return {'error': error_msg}
                
            payment = payment_response["response"]
            transaction_data = payment.get("point_of_interaction", {}).get("transaction_data", {})
            qr_code = transaction_data.get("qr_code")
            
            if not qr_code:
                error_msg = "Código PIX não encontrado na resposta do Mercado Pago"
                logger.error(f"{error_msg}. Resposta: {payment}")
                return {'error': error_msg}
                
            logger.info(f"Pagamento PIX criado com sucesso: ID={payment['id']}")
            return {
                'pix_code': qr_code,
                'id': payment["id"],
                'status': payment["status"]
            }
            
        except Exception as e:
            error_msg = f"Erro ao processar pagamento PIX: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {'error': error_msg}

    def verificar_pagamento(self, payment_id):
        try:
            logger.info(f"Verificando pagamento {payment_id}")
            payment_response = self.sdk.payment().get(payment_id)
            logger.debug(f"Resposta da verificação: {payment_response}")
            
            if payment_response["status"] != 200:
                error_msg = f"Erro ao verificar pagamento: {payment_response.get('response', {}).get('message', 'Erro desconhecido')}"
                logger.error(error_msg)
                return {'error': error_msg}
                
            payment = payment_response["response"]
            return {
                'status': payment["status"],
                'amount': payment["transaction_amount"],
                'currency': payment["currency_id"]
            }
        except Exception as e:
            error_msg = f"Erro ao verificar pagamento: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {'error': error_msg} 
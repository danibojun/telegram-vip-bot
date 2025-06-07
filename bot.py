import os
import logging
from datetime import datetime, timedelta, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from dotenv import load_dotenv
from database import Database
from pagamentos import Pagamentos

print('Iniciando bot...')
load_dotenv()
print('Variáveis de ambiente carregadas')
print('TELEGRAM_BOT_TOKEN:', os.getenv('TELEGRAM_BOT_TOKEN')[:8], '...')
print('VIP_GROUP_ID:', os.getenv('VIP_GROUP_ID'))
print('MERCADO_PAGO_ACCESS_TOKEN:', os.getenv('MERCADO_PAGO_ACCESS_TOKEN')[:8], '...')

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'
)
logger = logging.getLogger(__name__)

# Inicializa o banco de dados e pagamentos
db = Database()
pagamentos = Pagamentos()

# Carrega variáveis de ambiente
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
VIP_GROUP_ID = os.getenv('VIP_GROUP_ID')
if not BOT_TOKEN or not VIP_GROUP_ID:
    logger.error('TELEGRAM_BOT_TOKEN ou VIP_GROUP_ID não configurados no .env')
    exit(1)
VIP_GROUP_ID = int(VIP_GROUP_ID)

def start(update: Update, context: CallbackContext):
    logger.info(f"Comando /start de {update.effective_user.id}")
    keyboard = [[InlineKeyboardButton("💎 Assinar VIP R$10,00 mensal", callback_data="assinar_vip")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "🌟 Bem-vindo ao Bot VIP! 🌟\n\n"
        "🎯 Comandos disponíveis:\n"
        "• /assinar - Assine o grupo VIP\n"
        "• /status - Verifique seu status\n\n"
        "💎 Benefícios do grupo VIP:\n"
        "• Acesso exclusivo ao nosso grupo VIP secreto\n"
        "• Encontros exclusivos com os membros do grupo\n"
        "• Sorteios de brindes\n"
        "• Novidades primeiro por aqui\n\n"
        "Para começar, use o botão abaixo! 🚀",
        reply_markup=reply_markup
    )

def status(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    logger.info(f"Comando /status de {user_id}")
    assinatura = db.get_assinatura(user_id)
    if assinatura and assinatura['link_invite'] and assinatura['data_expiracao'] > datetime.now():  # Verifica se tem link e se não expirou
        dias_restantes = (assinatura['data_expiracao'] - datetime.now()).days
        update.message.reply_text(
            f"✅ Você já é um assinante VIP!\n\n"
            f"📅 Sua assinatura expira em {dias_restantes} dias.\n\n"
            f"Para renovar, aguarde a expiração da sua assinatura atual."
        )
    else:
        update.message.reply_text(
            "❌ Você ainda não é um assinante VIP.\n"
            "Use o comando /assinar para se tornar um membro!"
        )

def assinar(update: Update, context: CallbackContext):
    try:
        user_id = update.effective_user.id
        logger.info(f"Comando /assinar de {user_id}")
        
        # Verifica se já é assinante
        assinatura = db.get_assinatura(user_id)
        if assinatura and assinatura['link_invite']:  # Só considera assinante se tiver link de convite
            dias_restantes = (assinatura['data_expiracao'] - datetime.now()).days
            update.message.reply_text(
                f"✅ Você já é um assinante VIP!\n\n"
                f"📅 Sua assinatura expira em {dias_restantes} dias.\n"
                f"🔗 Link do grupo: {assinatura['link_invite']}\n\n"
                f"Para renovar, aguarde a expiração da sua assinatura atual."
            )
            return

        # Cria o pagamento PIX
        logger.info(f"Criando pagamento PIX para usuário {user_id}")
        pagamento = pagamentos.criar_pagamento_pix(10.00, "Assinatura VIP - 30 dias")
        
        if 'error' in pagamento:
            logger.error(f"Erro ao criar pagamento: {pagamento['error']}")
            update.message.reply_text(
                "❌ Desculpe, ocorreu um erro ao gerar o pagamento.\n"
                "Por favor, tente novamente em alguns minutos ou entre em contato com o suporte."
            )
            return

        # Salva apenas o ID do pagamento pendente
        db.salvar_assinatura(user_id, pagamento['id'], datetime.now() + timedelta(days=30))
        
        # Primeiro envia as instruções
        update.message.reply_text(
            "📱 Como pagar com PIX:\n"
            "1. Abra seu aplicativo de banco\n"
            "2. Escolha pagar com PIX\n"
            "3. Cole o código abaixo\n"
            "4. Confirme o pagamento"
        )
        
        # Depois envia o código PIX
        update.message.reply_text(
            f"📋 Código PIX copia e cola:\n"
            f"```\n{pagamento['pix_code']}\n```",
            parse_mode='Markdown'
        )
        
        # Por último, adiciona o botão de verificação
        keyboard = [[InlineKeyboardButton("✅ Verificar Pagamento", callback_data=f"verificar_{pagamento['id']}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            "Clique no botão abaixo após realizar o pagamento:",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Erro ao processar assinatura: {str(e)}", exc_info=True)
        update.message.reply_text(
            "❌ Desculpe, ocorreu um erro inesperado.\n"
            "Por favor, tente novamente em alguns minutos ou entre em contato com o suporte."
        )

def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    if query.data == "assinar_vip":
        try:
            user_id = query.from_user.id
            logger.info(f"Botão de assinatura clicado por {user_id}")
            
            # Verifica se já é assinante
            assinatura = db.get_assinatura(user_id)
            if assinatura and assinatura['link_invite'] and assinatura['data_expiracao'] > datetime.now():  # Verifica se tem link e se não expirou
                dias_restantes = (assinatura['data_expiracao'] - datetime.now()).days
                query.message.reply_text(
                    f"✅ Você já é um assinante VIP!\n\n"
                    f"📅 Sua assinatura expira em {dias_restantes} dias.\n\n"
                    f"Para renovar, aguarde a expiração da sua assinatura atual."
                )
                return

            # Cria o pagamento PIX
            logger.info(f"Criando pagamento PIX para usuário {user_id}")
            pagamento = pagamentos.criar_pagamento_pix(10.00, "Assinatura VIP - 30 dias")
            
            if 'error' in pagamento:
                logger.error(f"Erro ao criar pagamento: {pagamento['error']}")
                query.message.reply_text(
                    "❌ Desculpe, ocorreu um erro ao gerar o pagamento.\n"
                    "Por favor, tente novamente em alguns minutos ou entre em contato com o suporte."
                )
                return

            # Salva apenas o ID do pagamento pendente
            db.salvar_assinatura(user_id, pagamento['id'], datetime.now() + timedelta(days=30))
            
            # Primeiro envia as instruções
            query.message.reply_text(
                "📱 Como pagar com PIX:\n"
                "1. Abra seu aplicativo de banco\n"
                "2. Escolha pagar com PIX\n"
                "3. Cole o código abaixo\n"
                "4. Confirme o pagamento"
            )
            
            # Depois envia o código PIX
            query.message.reply_text(
                f"📋 Código PIX copia e cola:\n"
                f"```\n{pagamento['pix_code']}\n```",
                parse_mode='Markdown'
            )
            
            # Por último, adiciona o botão de verificação
            keyboard = [[InlineKeyboardButton("✅ Verificar Pagamento", callback_data=f"verificar_{pagamento['id']}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.message.reply_text(
                "Clique no botão abaixo após realizar o pagamento:",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Erro ao processar assinatura: {str(e)}", exc_info=True)
            query.message.reply_text(
                "❌ Desculpe, ocorreu um erro inesperado.\n"
                "Por favor, tente novamente em alguns minutos ou entre em contato com o suporte."
            )
            return
            
    if query.data.startswith("verificar_"):
        payment_id = query.data.split("_")[1]
        logger.info(f"Verificando pagamento {payment_id} para usuário {query.from_user.id}")
        
        try:
            # Verifica o status do pagamento
            status = pagamentos.verificar_pagamento(payment_id)
            
            if 'error' in status:
                logger.error(f"Erro ao verificar pagamento: {status['error']}")
                query.message.reply_text(
                    "❌ Erro ao verificar o pagamento.\n"
                    "Por favor, tente novamente em alguns minutos."
                )
                return
                
            if status['status'] == 'approved':
                # Gera link de convite único
                invite_link = context.bot.create_chat_invite_link(
                    chat_id=VIP_GROUP_ID,
                    member_limit=1,
                    expire_date=int((datetime.now() + timedelta(days=1)).timestamp())
                )
                
                # Atualiza a assinatura com o link
                db.salvar_assinatura(
                    query.from_user.id,
                    payment_id,
                    datetime.now() + timedelta(days=30),
                    invite_link.invite_link
                )
                
                query.message.reply_text(
                    "✅ *Pagamento confirmado!*\n\n"
                    "🎉 Parabéns! Você agora é um membro VIP!\n\n"
                    "🔗 Use o link abaixo para acessar o grupo:\n"
                    f"{invite_link.invite_link}\n\n"
                    "⚠️ O link expira em 24 horas.\n"
                    "💎 Sua assinatura é válida por 30 dias.",
                    parse_mode='Markdown'
                )
            else:
                query.message.reply_text(
                    "⏳ Pagamento ainda não foi confirmado.\n"
                    "Por favor, aguarde alguns minutos e tente novamente."
                )
                
        except Exception as e:
            logger.error(f"Erro ao processar verificação de pagamento: {str(e)}", exc_info=True)
            query.message.reply_text(
                "❌ Ocorreu um erro ao verificar o pagamento.\n"
                "Por favor, tente novamente em alguns minutos."
            )

def remover_expirados(context: CallbackContext):
    logger.info("Verificando assinaturas expiradas...")
    expirados = db.get_assinaturas_expiradas()
    for user_id in expirados:
        db.remover_assinatura(user_id)
        logger.info(f"Assinatura removida para usuário {user_id}")

def main():
    logger.info("Iniciando bot...")
    print("Iniciando bot...")
    print("Variáveis de ambiente carregadas")
    print(f"TELEGRAM_BOT_TOKEN: {BOT_TOKEN[:8]}...")
    print(f"VIP_GROUP_ID: {VIP_GROUP_ID}")
    print(f"MERCADO_PAGO_ACCESS_TOKEN: {os.getenv('MERCADO_PAGO_ACCESS_TOKEN')[:8]}...")

    # Cria o updater
    updater = Updater(BOT_TOKEN)

    # Adiciona os handlers
    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("status", status))
    updater.dispatcher.add_handler(CommandHandler("assinar", assinar))
    updater.dispatcher.add_handler(CallbackQueryHandler(button_callback))

    # Agenda a verificação de assinaturas expiradas
    job_queue = updater.job_queue
    job_queue.run_daily(remover_expirados, time=datetime.now().time())

    # Inicia o bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    logger.info("Script principal iniciado.")
    try:
        main()
    except Exception as e:
        logger.error(f"Erro ao iniciar o bot: {e}", exc_info=True)
    finally:
        logger.info("Script principal finalizado.") 
import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('assinaturas.db', check_same_thread=False)
        self.criar_tabela()
        logger.info("Banco de dados inicializado")

    def criar_tabela(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS assinaturas (
                    user_id INTEGER PRIMARY KEY,
                    payment_id TEXT,
                    data_expiracao TIMESTAMP,
                    link_invite TEXT
                )
            ''')
            self.conn.commit()
            logger.info("Tabela de assinaturas criada/verificada")
        except Exception as e:
            logger.error(f"Erro ao criar tabela: {str(e)}", exc_info=True)
            raise

    def salvar_assinatura(self, user_id, payment_id, data_expiracao, link_invite=None):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO assinaturas (user_id, payment_id, data_expiracao, link_invite)
                VALUES (?, ?, ?, ?)
            ''', (user_id, payment_id, data_expiracao, link_invite))
            self.conn.commit()
            logger.info(f"Assinatura salva para usuário {user_id}")
        except Exception as e:
            logger.error(f"Erro ao salvar assinatura: {str(e)}", exc_info=True)
            raise

    def get_assinatura(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM assinaturas WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            
            if result:
                return {
                    'user_id': result[0],
                    'payment_id': result[1],
                    'data_expiracao': datetime.fromisoformat(result[2]),
                    'link_invite': result[3]
                }
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar assinatura: {str(e)}", exc_info=True)
            raise

    def remover_assinatura(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM assinaturas WHERE user_id = ?', (user_id,))
            self.conn.commit()
            logger.info(f"Assinatura removida para usuário {user_id}")
        except Exception as e:
            logger.error(f"Erro ao remover assinatura: {str(e)}", exc_info=True)
            raise

    def get_assinaturas_expiradas(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT user_id FROM assinaturas WHERE data_expiracao < ?', (datetime.now(),))
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Erro ao buscar assinaturas expiradas: {str(e)}", exc_info=True)
            raise 
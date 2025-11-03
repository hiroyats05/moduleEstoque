import logging


def registrar_log(usuario: str, mensagem: str):
    """
    Args:
        usuario: nome do usuário que realizou a ação
        mensagem: descrição da ação realizada
    """
    try:
        logging.info(f'[{usuario}] {mensagem}')
    except Exception:
        print(f'[{usuario}] {mensagem}')

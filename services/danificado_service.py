from typing import Optional
from services.validators import QuantidadeValidator


def atualizar_produto_danificado(produto_danificado_id: int, form_data: dict, usuario_nome: Optional[str] = None):
    """
    Atualiza equipamento danificado e ajusta quantidade do produto pai.
    """

    from models import db, Produto
    from utils.log_utils import registrar_log
    
    # Buscar produto danificado e validações iniciais
    produto_danificado = Produto.query.get_or_404(produto_danificado_id)
    
    if not produto_danificado.danificado or not produto_danificado.origem_id:
        raise ValueError('Este item não é um equipamento danificado válido.')
    
    produto_pai = Produto.query.get(produto_danificado.origem_id)
    if not produto_pai:
        raise ValueError('Produto pai não encontrado.')
    
    # Validar nova quantidade
    nova_qtd_danificada = QuantidadeValidator.validar(form_data.get('quantidade_danificada', 0))
    
    # Regra de negócio: total disponível é constante
    total_disponivel = produto_pai.quantidade + produto_danificado.quantidade
    if nova_qtd_danificada > total_disponivel:
        raise ValueError(
            f"Quantidade danificada ({nova_qtd_danificada}) excede o total disponível ({total_disponivel})."
        )
    
    # Atualizar quantidades
    produto_danificado.quantidade = nova_qtd_danificada
    produto_danificado.nome = f"{produto_pai.nome} (Danificado)"
    produto_danificado.unidade_medida = form_data.get('unidade_medida') or produto_danificado.unidade_medida
    produto_danificado.origem = form_data.get('origem') or produto_danificado.origem
    
    produto_pai.quantidade = total_disponivel - nova_qtd_danificada
    
    # Persistir
    db.session.commit()
    
    # Log
    if usuario_nome:
        registrar_log(usuario_nome, f'Editou equipamento danificado ID {produto_danificado.id}')
    
    return produto_danificado


def excluir_produto_danificado(produto_danificado_id: int, usuario_nome: Optional[str] = None):
    """
    Exclui equipamento danificado e retorna quantidade ao produto pai.
    """
    from models import db, Produto
    from utils.log_utils import registrar_log
    
    # Buscar e validar
    produto_danificado = Produto.query.get_or_404(produto_danificado_id)
    
    if not produto_danificado.danificado or not produto_danificado.origem_id:
        raise ValueError('Este item não é um equipamento danificado válido.')
    
    # Retornar quantidade ao produto pai
    produto_pai = Produto.query.get(produto_danificado.origem_id)
    if produto_pai:
        produto_pai.quantidade += produto_danificado.quantidade
    
    # Excluir
    db.session.delete(produto_danificado)
    db.session.commit()
    
    # Log
    if usuario_nome:
        registrar_log(usuario_nome, f'Excluiu equipamento danificado ID {produto_danificado.id}')

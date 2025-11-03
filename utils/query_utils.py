"""Utilitários para queries de produtos."""
from sqlalchemy import not_


def build_produtos_query(busca: str = '', tipo: str = '', ordem: str = 'asc'):
    """
    Args:
        busca: termo de busca para filtrar por nome
        tipo: tipo de produto para filtrar
        ordem: 'asc' ou 'desc' para ordenação por quantidade
        
    """
    from models import Produto

    query = Produto.query

    if busca:
        query = query.filter(Produto.nome.ilike(f'%{busca}%'))

    if tipo:
        query = query.filter(Produto.tipo == tipo)

    query = query.filter(not_(Produto.nome.ilike('%(Danificado)%')))

    if ordem == 'desc':
        query = query.order_by(Produto.quantidade.desc())
    else:
        query = query.order_by(Produto.quantidade.asc())

    return query.all()

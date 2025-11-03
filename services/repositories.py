from typing import Optional
from abc import ABC, abstractmethod


class ProdutoRepositoryInterface(ABC):
    """Interface para repositório de produtos."""
    
    @abstractmethod
    def get_by_id(self, produto_id: int):
        """Busca produto por ID."""
        pass
    
    @abstractmethod
    def save(self, produto):
        """Salva produto."""
        pass
    
    @abstractmethod
    def commit(self):
        """Confirma transação."""
        pass


class MovimentacaoRepositoryInterface(ABC):
    """Interface para repositório de movimentações."""
    
    @abstractmethod
    def criar_ajuste(self, produto_id: int, usuario_id: str, quantidade: int, observacao: str):
        """Cria movimentação de ajuste."""
        pass
    
    @abstractmethod
    def criar_movimentacao_entrada(self, produto_id: int, usuario_id: str, quantidade: int, observacao: str):
        """Cria movimentação de entrada."""
        pass


# Implementações concretas (SQLAlchemy)

class ProdutoRepository(ProdutoRepositoryInterface):
    """Implementação concreta usando SQLAlchemy."""
    
    def get_by_id(self, produto_id: int):
        """Busca produto por ID."""
        from models import Produto
        return Produto.query.get_or_404(produto_id)
    
    def save(self, produto):
        """Salva produto no contexto."""
        from models import db
        db.session.add(produto)
    
    def commit(self):
        """Confirma transação."""
        from models import db
        db.session.commit()


class MovimentacaoRepository(MovimentacaoRepositoryInterface):
    """Implementação concreta para movimentações."""
    
    def criar_ajuste(self, produto_id: int, usuario_id: str, quantidade: int, observacao: str):
        """Cria e salva movimentação de ajuste."""
        from models import db, MovimentacaoEstoque
        
        movimentacao = MovimentacaoEstoque(
            produto_id=produto_id,
            usuario_id=usuario_id,
            quantidade=quantidade,
            tipo='ajuste',
            observacao=observacao
        )
        db.session.add(movimentacao)
        db.session.commit()
    
    def criar_movimentacao_entrada(self, produto_id: int, usuario_id: str, quantidade: int, observacao: str):
        """Cria e salva movimentação de entrada."""
        from models import db, MovimentacaoEstoque
        
        movimentacao = MovimentacaoEstoque(
            produto_id=produto_id,
            usuario_id=usuario_id,
            quantidade=quantidade,
            tipo='entrada',
            observacao=observacao
        )
        db.session.add(movimentacao)
        db.session.commit()

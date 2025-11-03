from abc import ABC, abstractmethod
from typing import Dict, TYPE_CHECKING
from services.validators import QuantidadeValidator, OrigemValidator, ProdutoValidator

if TYPE_CHECKING:
    from models import Produto


class ProdutoUpdateStrategy(ABC):
    """Interface base para estratégias de atualização de produto."""
    
    @abstractmethod
    def atualizar(self, produto, form_data: Dict, qtd_funcional_anterior: int, qtd_danif_anterior: int):
        pass


class MaterialUpdateStrategy(ProdutoUpdateStrategy):
    """Estratégia para atualização de materiais (sem origem, sem danificados)."""
    
    def atualizar(self, produto, form_data: Dict, qtd_funcional_anterior: int, qtd_danif_anterior: int):
        """Materiais: atualização simples, sem origem e sem danificados."""
        produto.origem = None
        produto.quantidade = QuantidadeValidator.validar(form_data.get('quantidade'))
        
        # Remover danificados se existirem
        self._remover_danificados(produto)
    
    @staticmethod
    def _remover_danificados(produto):
        """Remove produtos danificados vinculados."""
        from models import db
        for pd in produto.produtos_danificados:
            db.session.delete(pd)


class EquipamentoUpdateStrategy(ProdutoUpdateStrategy):
    """Estratégia para atualização de equipamentos (com origem e danificados)."""
    
    def atualizar(self, produto, form_data: Dict, qtd_funcional_anterior: int, qtd_danif_anterior: int):
        """Equipamentos: gerenciar origem e danificados."""
        from models import db, Produto
        
        # Atualizar origem
        produto.origem = OrigemValidator.normalizar(form_data.get('origem'))
        
        # Processar danificados
        qtd_danificada = QuantidadeValidator.validar(form_data.get('quantidade_danificada', 0))
        
        # Validar regra de negócio
        ProdutoValidator.validar_danificados(qtd_danificada, qtd_funcional_anterior, qtd_danif_anterior)
        
        # Calcular nova quantidade funcional
        total_disponivel = qtd_funcional_anterior + qtd_danif_anterior
        produto.quantidade = total_disponivel - qtd_danificada
        
        # Gerenciar produto danificado
        if qtd_danificada > 0:
            self._criar_ou_atualizar_danificado(produto, qtd_danificada)
        else:
            self._remover_danificados(produto)
    
    @staticmethod
    def _criar_ou_atualizar_danificado(produto, qtd_danificada: int):
        """Cria ou atualiza produto danificado vinculado."""
        from models import db, Produto
        
        produto_danificado = produto.produtos_danificados[0] if produto.produtos_danificados else None
        
        if produto_danificado:
            # Atualizar existente
            produto_danificado.nome = f"{produto.nome} (Danificado)"
            produto_danificado.quantidade = qtd_danificada
            produto_danificado.unidade_medida = produto.unidade_medida
            produto_danificado.tipo = produto.tipo
            produto_danificado.origem = produto.origem
            produto_danificado.local_produto = produto.local_produto
        else:
            # Criar novo
            db.session.add(Produto(
                nome=f"{produto.nome} (Danificado)",
                quantidade=qtd_danificada,
                unidade_medida=produto.unidade_medida,
                tipo=produto.tipo,
                origem=produto.origem,
                local_produto=produto.local_produto,
                danificado=True,
                origem_id=produto.id
            ))
    
    @staticmethod
    def _remover_danificados(produto):
        """Remove produtos danificados vinculados."""
        from models import db
        for pd in produto.produtos_danificados:
            db.session.delete(pd)


class ProdutoCreateStrategy(ABC):
    """Interface base para estratégias de criação de produto."""
    
    @abstractmethod
    def criar(self, data: Dict) -> 'Produto':
        """
        Cria produto conforme regras específicas do tipo.
        
        Args:
            data: Dicionário com dados validados do produto
            
        Returns:
            Produto: Instância do produto criado
        """
        pass


class MaterialCreateStrategy(ProdutoCreateStrategy):
    """Estratégia para criação de materiais."""
    
    def criar(self, data: Dict) -> 'Produto':
        """Materiais: criação simples, sem origem e sem danificados."""
        from models import db, Produto
        
        produto = Produto(
            nome=data['nome'],
            quantidade=data['quantidade_funcional'],
            tipo=data['tipo'],
            origem=None,
            unidade_medida=data['unidade_medida'],
            local_produto=data['local_produto']
        )
        
        db.session.add(produto)
        db.session.flush()  # Para obter o ID
        
        return produto


class EquipamentoCreateStrategy(ProdutoCreateStrategy):
    """Estratégia para criação de equipamentos com danificados."""
    
    def criar(self, data: Dict) -> 'Produto':
        """Equipamentos: criar produto principal e danificado se necessário."""
        from models import db, Produto
        
        # Criar produto principal
        produto = Produto(
            nome=data['nome'],
            quantidade=data['quantidade_funcional'],
            tipo=data['tipo'],
            origem=data['origem'],
            unidade_medida=data['unidade_medida'],
            local_produto=data['local_produto']
        )
        
        db.session.add(produto)
        db.session.flush()  # Obter ID para vincular danificado
        
        # Criar produto danificado se houver
        if data['quantidade_danificada_int'] > 0:
            produto_danificado = Produto(
                nome=f"{data['nome']} (Danificado)",
                quantidade=data['quantidade_danificada_int'],
                tipo=data['tipo'],
                origem=data['origem'],
                unidade_medida=data['unidade_medida'],
                local_produto=data['local_produto'],
                danificado=True,
                origem_id=produto.id
            )
            db.session.add(produto_danificado)
        
        return produto


class ProdutoStrategyFactory:
    """Factory para criar estratégias baseadas no tipo de produto."""
    
    _update_strategies = {
        'material': MaterialUpdateStrategy(),
        'equipamento': EquipamentoUpdateStrategy(),
    }
    
    _create_strategies = {
        'material': MaterialCreateStrategy(),
        'equipamento': EquipamentoCreateStrategy(),
    }
    
    @classmethod
    def get_update_strategy(cls, tipo: str) -> ProdutoUpdateStrategy:
        """
        Retorna a estratégia de atualização apropriada.
        
        Args:
            tipo: Tipo do produto ('material' ou 'equipamento')
            
        Returns:
            ProdutoUpdateStrategy: Estratégia de atualização
            
        Raises:
            ValueError: Se tipo for inválido
        """
        tipo_lower = tipo.lower().strip()
        strategy = cls._update_strategies.get(tipo_lower)
        
        if not strategy:
            raise ValueError(f"Tipo de produto desconhecido: {tipo}")
        
        return strategy
    
    @classmethod
    def get_create_strategy(cls, tipo: str) -> ProdutoCreateStrategy:
        """
        Retorna a estratégia de criação apropriada.
        
        Args:
            tipo: Tipo do produto ('material' ou 'equipamento')
            
        Returns:
            ProdutoCreateStrategy: Estratégia de criação
            
        Raises:
            ValueError: Se tipo for inválido
        """
        tipo_lower = tipo.lower().strip()
        strategy = cls._create_strategies.get(tipo_lower)
        
        if not strategy:
            raise ValueError(f"Tipo de produto desconhecido: {tipo}")
        
        return strategy
    
    @classmethod
    def get_strategy(cls, tipo: str) -> ProdutoUpdateStrategy:
        """Compatibilidade com código existente."""
        return cls.get_update_strategy(tipo)
    
    @classmethod
    def registrar_strategy(cls, tipo: str, update_strategy: ProdutoUpdateStrategy = None, 
                          create_strategy: ProdutoCreateStrategy = None):
        """
        Registra novas estratégias (extensibilidade).
        
        Args:
            tipo: Tipo do produto
            update_strategy: Instância da estratégia de atualização
            create_strategy: Instância da estratégia de criação
        """
        tipo_lower = tipo.lower()
        if update_strategy:
            cls._update_strategies[tipo_lower] = update_strategy
        if create_strategy:
            cls._create_strategies[tipo_lower] = create_strategy

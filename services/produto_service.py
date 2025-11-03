from typing import Dict, Optional


class FormValidationError(Exception):
    """Erro simples para sinalizar problemas de validação de formulários."""
    pass


def parse_produto_form(form):
    nome = form.get('nome')
    quantidade = form.get('quantidade')
    tipo = form.get('tipo')
    unidade_medida = form.get('unidade_medida')
    local_produto = form.get('local_produto', 'Estoque Geral')
    quantidade_danificada = form.get('quantidade_danificada', 0)

    if not (nome and quantidade and tipo and unidade_medida):
        raise FormValidationError('Todos os campos são obrigatórios.')

    tipo_clean = tipo.strip().lower()
    origem_raw = form.get('origem', '').strip().lower() if tipo_clean == 'equipamento' else None

    if origem_raw in ['alugada', 'alugado']:
        origem = 'Alugado'
    elif origem_raw == 'comprado':
        origem = 'Comprado'
    else:
        origem = None

    try:
        quantidade_int = int(quantidade)
        quantidade_danificada_int = int(quantidade_danificada)
    except ValueError:
        raise FormValidationError('Quantidade deve ser um número válido.')

    if quantidade_int < 0 or quantidade_danificada_int < 0:
        raise FormValidationError('Quantidade não pode ser negativa.')

    if tipo_clean == 'equipamento' and quantidade_danificada_int > quantidade_int:
        raise FormValidationError('Quantidade danificada não pode ser maior que a quantidade total.')

    quantidade_funcional = quantidade_int
    if tipo_clean == 'equipamento' and quantidade_danificada_int > 0:
        quantidade_funcional = quantidade_int - quantidade_danificada_int

    return {
        'nome': nome,
        'quantidade_int': quantidade_int,
        'tipo': tipo,
        'tipo_clean': tipo_clean,
        'unidade_medida': unidade_medida,
        'local_produto': local_produto,
        'quantidade_danificada_int': quantidade_danificada_int,
        'origem': origem,
        'quantidade_funcional': quantidade_funcional,
    }


def criar_produto(data: Dict, usuario_id: str, usuario_nome: Optional[str] = None):
    """
    Cria novo produto
    Args:
        data: Dicionário com dados validados do produto (de parse_produto_form)
        usuario_id: ID do usuário que está criando o produto
        usuario_nome: Nome do usuário para logging (opcional)
        
    Returns:
        Produto: Instância do produto criado
        
    Raises:
        ValueError: Se tipo de produto for inválido
        
    Example:
        >>> data = parse_produto_form(request.form)
        >>> produto = criar_produto(data, usuario_id='123', usuario_nome='João')
    """
    from services.repositories import ProdutoRepository, MovimentacaoRepository
    from services.produto_strategies import ProdutoStrategyFactory
    from utils.log_utils import registrar_log
    
    # Injeção de dependências
    produto_repo = ProdutoRepository()
    movimentacao_repo = MovimentacaoRepository()
    
    # delegar criação ao tipo apropriado
    strategy = ProdutoStrategyFactory.get_create_strategy(data['tipo_clean'])
    produto = strategy.criar(data)
    
    # Persistir produto principal (e danificado se criado pela strategy)
    produto_repo.commit()
    
    # Registrar movimentação de entrada no estoque
    observacao = f"Produto cadastrado no estoque geral."
    movimentacao_repo.criar_movimentacao_entrada(
        produto_id=produto.id,
        usuario_id=usuario_id,
        quantidade=data['quantidade_int'],
        observacao=observacao
    )
    
    # Registrar operação no log do sistema
    if usuario_nome:
        _log_criacao_produto(usuario_nome, data)
    
    return produto


def _log_criacao_produto(usuario_nome: str, data: Dict):
    """Registra log da criação de produto com detalhes."""
    from utils.log_utils import registrar_log
    
    tipo_clean = data['tipo_clean']
    qtd_danif = data['quantidade_danificada_int'] if tipo_clean == 'equipamento' else 0
    
    mensagem = (
        f"Adicionou produto: {data['nome']} "
        f"({data['quantidade_int']} {data['unidade_medida']}) - "
        f"Local: {data['local_produto']} - "
        f"Tipo: {data['tipo']}, "
        f"Origem: {data['origem']}, "
        f"Danificados: {qtd_danif}"
    )
    
    try:
        registrar_log(usuario_nome, mensagem)
    except Exception:
        pass 


def atualizar_produto(produto_id: int, form_data: Dict, usuario_id: str, usuario_nome: Optional[str] = None):
    from services.repositories import ProdutoRepository, MovimentacaoRepository
    from services.produto_strategies import ProdutoStrategyFactory
    from utils.log_utils import registrar_log
    
    # Injeção de dependências
    produto_repo = ProdutoRepository()
    movimentacao_repo = MovimentacaoRepository()
    
    # Recuperar produto do banco de dados
    produto = produto_repo.get_by_id(produto_id)
    
    # Guardar estado atual para auditoria e cálculo de delta
    qtd_anterior = produto.quantidade
    danif_anterior = produto.quantidade_danificada or 0
    
    # Atualizar atributos básicos 
    produto.nome = form_data.get('nome')
    produto.tipo = form_data.get('tipo')
    produto.unidade_medida = form_data.get('unidade_medida') or produto.unidade_medida or 'unidade'
    produto.local_produto = form_data.get('local_produto') or produto.local_produto or 'Estoque Geral'
    
    # delegar lógica específica ao tipo apropriado
    strategy = ProdutoStrategyFactory.get_strategy(produto.tipo)
    strategy.atualizar(produto, form_data, qtd_anterior, danif_anterior)
    
    # Persistir alterações no banco de dados
    produto_repo.commit()
    
    # Criar movimentação de ajuste se houver alteração nas quantidades
    delta = produto.quantidade - qtd_anterior
    danif_novo = produto.quantidade_danificada or 0
    
    if delta != 0 or danif_novo != danif_anterior:
        observacao = (
            f'Ajuste: funcional {qtd_anterior}→{produto.quantidade}; '
            f'danificados {danif_anterior}→{danif_novo}'
        )
        movimentacao_repo.criar_ajuste(produto.id, usuario_id, delta, observacao)
    
    # Registrar operação no log do sistema
    if usuario_nome:
        registrar_log(usuario_nome, f'Editou produto ID {produto.id}')
    
    return produto

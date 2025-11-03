from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import or_, func, not_
from user_agents import parse
import pytz

from models import db, Produto, MovimentacaoEstoque, MovimentacaoEstoqueObra, Compra, EquipamentoDanificado

app = Flask(__name__)

# Configuração do SQLite3
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///estoque.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
db.init_app(app)

MOCK_USER_ID = 1
MOCK_USERNAME = 'usuario'

from services.produto_service import FormValidationError, parse_produto_form, atualizar_produto
from utils.datetime_utils import fusohorario
from utils.query_utils import build_produtos_query
from utils.log_utils import registrar_log

@app.route('/')
def index():
    """Redireciona para a página de estoque."""
    return redirect(url_for('layout_estoque'))
        
@app.route('/estoque', methods=['GET', 'POST'])
def layout_estoque():
    busca = request.args.get('busca', '')
    ordem = request.args.get('ordem', 'asc')
    tipo = request.args.get('tipo', '')

    produtos_query = build_produtos_query(busca=busca, tipo=tipo, ordem=ordem)
    
    # Verifica se é uma query ou lista
    if hasattr(produtos_query, 'all'):
        produtos = produtos_query.all()
    else:
        produtos = produtos_query
    
    print(f"\n=== DEBUG Estoque ===")
    print(f"Total de produtos: {len(produtos) if produtos else 0}")
    if produtos:
        print(f"Primeiro produto: {produtos[0].nome}")

    equipamentos_danificados = Produto.query.filter(
        Produto.nome.ilike('%(Danificado)%')
    ).all()

    user_agent = parse(request.headers.get('User-Agent'))
    if user_agent.is_mobile:
        return render_template('mobile/estoque_mobile.html', produtos=produtos, busca=busca, ordem=ordem, tipo=tipo, equipamentos_danificados=equipamentos_danificados)
    else:
        return render_template('estoque.html', produtos=produtos, busca=busca, ordem=ordem, tipo=tipo, equipamentos_danificados=equipamentos_danificados)

@app.route('/produtos', methods=['POST'])
def adicionar_produto():
    """Route handler para criação de produtos. Delega ao service layer."""
    print("\n=== DEBUG: Formulário recebido ===")
    print("Form data:", dict(request.form))

    try:
        data = parse_produto_form(request.form)
        print("Data parseada:", data)
    except FormValidationError as e:
        print(f"Erro de validação: {e}")
        flash(str(e), 'warning')
        return redirect(url_for('layout_estoque'))

    from services.produto_service import criar_produto

    try:
        produto = criar_produto(data, MOCK_USER_ID, usuario_nome=MOCK_USERNAME)
        print(f"Produto criado: {produto.nome if produto else 'None'}")
    except Exception as e:
        print(f"ERRO ao criar produto: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Erro ao adicionar produto: {e}', 'danger')
        return redirect(url_for('layout_estoque'))

    print("Produto adicionado com sucesso!")
    flash('Item adicionado com sucesso!', 'success')
    return redirect(url_for('layout_estoque'))

@app.route('/editar/<string:id>', methods=['GET', 'POST'])
def editar(id):
    """Route handler para edição de produtos. Delega ao service layer."""

    # GET: renderizar formulário de edição
    if request.method == 'GET':
        produto = Produto.query.get_or_404(id)
        user_agent = parse(request.headers.get('User-Agent'))
        
        template = 'mobile/editar_mobile.html' if user_agent.is_mobile else 'editar.html'
        return render_template(template, produto=produto)

    # POST: processar atualização
    try:
        atualizar_produto(
            produto_id=id,
            form_data=request.form,
            usuario_id=MOCK_USER_ID,
            usuario_nome=MOCK_USERNAME
        )
        flash('Produto atualizado com sucesso.', 'success')
        return redirect(url_for('layout_estoque'))
        
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(request.url)
    except Exception as e:
        flash(f'Erro ao atualizar produto: {e}', 'danger')
        return redirect(request.url)

@app.route('/excluir/<string:id>')
def excluir(id):
    """Route handler para exclusão de produtos. Operação simples inline."""
    
    # Buscar produto
    produto = Produto.query.get_or_404(id)
    nome_produto = produto.nome
    produto_id = produto.id
    
    # Excluir
    db.session.delete(produto)
    db.session.commit()
    
    # Log e feedback
    registrar_log(MOCK_USERNAME, f'Excluiu produto: {nome_produto} (ID {produto_id})')
    flash(f'Produto "{nome_produto}" excluído com sucesso.', 'success')
    
    return redirect(url_for('layout_estoque'))

@app.route('/equipamentos-danificados')
def listar_danificados():
    danificados = EquipamentoDanificado.query.all()
    return render_template('danificados.html', danificados=danificados)

@app.route('/editar_danificado/<string:id>', methods=['GET', 'POST'])
def editar_danificado(id):
    """Route handler para edição de equipamentos danificados. Delega ao service layer."""
    
    # GET: renderizar formulário
    if request.method == 'GET':
        produto_danificado = Produto.query.get_or_404(id)
        return render_template('editar_danificado.html', produto=produto_danificado)
    
    # POST: processar atualização
    from services.danificado_service import atualizar_produto_danificado
    
    try:
        atualizar_produto_danificado(
            produto_danificado_id=id,
            form_data=request.form,
            usuario_nome=MOCK_USERNAME
        )
        flash('Equipamento danificado atualizado com sucesso.', 'success')
        return redirect(url_for('layout_estoque'))
        
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(request.url)
    except Exception as e:
        flash(f'Erro ao atualizar equipamento: {e}', 'danger')
        return redirect(request.url)

@app.route('/excluir_equipamento_danificado/<string:id>', methods=['POST', 'GET'])
def excluir_danificado(id):
    """Route handler para exclusão de equipamentos danificados. Delega ao service layer."""

    
    from services.danificado_service import excluir_produto_danificado
    
    try:
        excluir_produto_danificado(
            produto_danificado_id=id,
            usuario_nome=MOCK_USERNAME
        )
        flash('Equipamento danificado excluído com sucesso.', 'success')
        return redirect(url_for('layout_estoque'))
        
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('layout_estoque'))
    except Exception as e:
        flash(f'Erro ao excluir equipamento: {e}', 'danger')
        return redirect(url_for('layout_estoque'))

@app.route('/produtos/<string:produto_id>/historico')
def historico_produto(produto_id):
    produto = Produto.query.get_or_404(produto_id)

    movimentacoes_geral = MovimentacaoEstoque.query.filter_by(produto_id=produto.id).all()

    movimentacoes_transferencias = MovimentacaoEstoqueObra.query.filter_by(produto_id=produto.id, obra_id=None).all()

    todas_movimentacoes = sorted(
        list(movimentacoes_geral) + list(movimentacoes_transferencias),
        key=lambda m: m.data,
        reverse=True
    )

    compras = Compra.query.filter_by(produto_id=produto.id).order_by(Compra.data.desc()).all()

    return render_template('historico_produto.html', produto=produto, historico=todas_movimentacoes, compras=compras)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
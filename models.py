from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func
import uuid

db = SQLAlchemy()


class Produto(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    local_produto = db.Column(db.String(100), nullable=False, default='Estoque Geral')
    unidade_medida = db.Column(db.String(50), nullable=True)
    tipo = db.Column(db.String(50), nullable=False)
    origem = db.Column(db.String(50))
    movimentacoes = db.relationship('MovimentacaoEstoque', 
                                    backref ='produto', 
                                    cascade='all, delete-orphan')

    danificado = db.Column(db.Boolean, default=False)
    origem_id = db.Column(db.String(36), db.ForeignKey('produto.id'), nullable=True)
    produto_pai = db.relationship('Produto', remote_side=[id], backref='produtos_danificados')

    @hybrid_property
    def quantidade_danificada(self):
        return sum([p.quantidade for p in self.produtos_danificados])

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'quantidade': self.quantidade,
            'local_produto': self.local_produto,
            'unidade_medida': self.unidade_medida,
            'tipo': self.tipo,
            'origem': self.origem,
            'danificado': bool(self.danificado),
            'origem_id': self.origem_id,
        }


class MovimentacaoEstoque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    produto_id = db.Column(db.String(36), db.ForeignKey('produto.id'))
    usuario_id = db.Column(db.String(36))
    observacao = db.Column(db.Text)
    data = db.Column(db.DateTime, server_default=func.now())


class MovimentacaoEstoqueObra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    produto_id = db.Column(db.String(36), db.ForeignKey('produto.id'))
    usuario_id = db.Column(db.String(36))
    obra_id = db.Column(db.Integer, nullable=True)
    data = db.Column(db.DateTime, server_default=func.now())


class Compra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.String(36), db.ForeignKey('produto.id'))
    quantidade = db.Column(db.Integer, nullable=True)
    fornecedor = db.Column(db.String(200), nullable=True)
    data = db.Column(db.DateTime, server_default=func.now())


class EquipamentoDanificado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.String(36), db.ForeignKey('produto.id'))
    nome = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    data = db.Column(db.DateTime, server_default=func.now())

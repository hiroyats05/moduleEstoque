from typing import Optional


class QuantidadeValidator:
    """Valida quantidades numéricas."""
    
    @staticmethod
    def validar(valor, permitir_zero: bool = True) -> int:
        """
        Valida e converte quantidade.
        
        Args:
            valor: Valor a ser validado
            permitir_zero: Se True, aceita zero como válido
            
        Returns:
            int: Quantidade validada
            
        Raises:
            ValueError: Se quantidade for inválida
        """
        try:
            qtd = int(valor)
        except (ValueError, TypeError):
            raise ValueError("Quantidade deve ser um número válido.")
        
        if qtd < 0:
            raise ValueError("Quantidade não pode ser negativa.")
        
        if not permitir_zero and qtd == 0:
            raise ValueError("Quantidade deve ser maior que zero.")
        
        return qtd


class OrigemValidator:
    """Valida e normaliza origem de equipamentos."""
    
    ORIGENS_VALIDAS = {
        'alugado': 'Alugado',
        'alugada': 'Alugado',
        'comprado': 'Comprado',
        'comprada': 'Comprado'
    }
    
    @staticmethod
    def normalizar(origem: Optional[str]) -> Optional[str]:
        """
        Normaliza valor de origem.
        
        Args:
            origem: Valor bruto da origem
            
        Returns:
            str ou None: Origem normalizada ou None se inválida
        """
        if not origem:
            return None
        
        origem_lower = origem.strip().lower()
        return OrigemValidator.ORIGENS_VALIDAS.get(origem_lower)


class ProdutoValidator:
    """Valida regras de negócio de produtos."""
    
    @staticmethod
    def validar_danificados(qtd_danificada: int, qtd_funcional: int, qtd_danif_anterior: int = 0):
        """
        Valida que quantidade danificada não excede o total disponível.
        
        Args:
            qtd_danificada: Nova quantidade de danificados
            qtd_funcional: Quantidade funcional anterior
            qtd_danif_anterior: Quantidade danificada anterior
            
        Raises:
            ValueError: Se danificados excedem o total
        """
        total_disponivel = qtd_funcional + qtd_danif_anterior
        
        if qtd_danificada > total_disponivel:
            raise ValueError(
                f"Quantidade danificada ({qtd_danificada}) excede o total disponível ({total_disponivel})."
            )

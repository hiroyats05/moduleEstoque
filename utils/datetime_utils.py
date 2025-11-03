"""Utilitários para datas e timezone."""
import pytz

fuso = pytz.timezone('America/Sao_paulo')


def fusohorario(dt_utc):
    """Converte datetime UTC para o fuso horário de São Paulo."""
    if dt_utc is None:
        return None
    if getattr(dt_utc, 'tzinfo', None) is None:
        dt_utc = pytz.utc.localize(dt_utc)
    return dt_utc.astimezone(fuso)

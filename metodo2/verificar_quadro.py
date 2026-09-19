# SPDX-License-Identifier: MIT
from calcular_crc8 import crc8

def verificar_quadro_metodo2(quadro: dict) -> bool:
    """Receptor valida a integridade do quadro do Método 2 usando o CRC-8."""
    tamanho = quadro["tamanho"]
    payload = quadro["payload"]
    crc_recebido = quadro["crc"]
    
    # Recalcula o CRC sobre o tamanho e os dados recebidos
    dados_para_crc = bytes([tamanho]) + payload
    crc_calculado = crc8(dados_para_crc)
    
    # Compara o resultado
    return crc_calculado == crc_recebido
"""
Módulo utilitário para obtenção de timestamp preciso da internet
"""
import ntplib
import time
from datetime import datetime, timezone, timedelta
import socket
from typing import Optional, Tuple

class InternetTimeSync:
    """Classe para sincronização de tempo com servidores NTP"""
    
    # Lista de servidores NTP públicos confiáveis
    NTP_SERVERS = [
        'pool.ntp.org',
        'time.google.com',
        'time.windows.com',
        'time.apple.com',
        'time.cloudflare.com',
        'time.nist.gov'
    ]
    
    def __init__(self, timeout: int = 5):
        """
        Inicializa o cliente NTP
        
        Args:
            timeout: Timeout em segundos para conexão com servidores NTP
        """
        self.ntp_client = ntplib.NTPClient()
        self.timeout = timeout
        self._last_sync_time = None
        self._time_offset = 0
    
    def get_internet_time(self) -> Optional[datetime]:
        """
        Obtém o tempo atual da internet usando servidores NTP
        
        Returns:
            datetime com o tempo atual da internet ou None se falhar
        """
        for server in self.NTP_SERVERS:
            try:
                # Configurar timeout
                socket.setdefaulttimeout(self.timeout)
                
                # Fazer requisição NTP
                response = self.ntp_client.request(server, version=3, timeout=self.timeout)
                
                if response:
                    # Converter timestamp NTP para datetime
                    ntp_time = response.tx_time
                    internet_time = datetime.fromtimestamp(ntp_time, tz=timezone.utc)
                    
                    # Calcular offset entre tempo local e internet
                    local_time = datetime.now(timezone.utc)
                    self._time_offset = (internet_time - local_time).total_seconds()
                    self._last_sync_time = time.time()
                    
                    return internet_time
                    
            except (ntplib.NTPException, socket.timeout, socket.gaierror, OSError) as e:
                print(f"Erro ao conectar com {server}: {str(e)}")
                continue
        
        print("Aviso: Não foi possível obter tempo da internet. Usando tempo local.")
        return None
    
    def get_synced_timestamp(self) -> datetime:
        """
        Obtém timestamp sincronizado com a internet
        
        Returns:
            datetime com timestamp preciso
        """
        # Tentar obter tempo da internet
        internet_time = self.get_internet_time()
        
        if internet_time:
            return internet_time
        
        # Se falhar, usar tempo local com offset calculado anteriormente
        if self._last_sync_time and (time.time() - self._last_sync_time) < 3600:  # 1 hora
            # Aplicar offset se disponível e recente
            local_time = datetime.now(timezone.utc)
            return local_time + timezone.timedelta(seconds=self._time_offset)
        
        # Fallback para tempo local
        return datetime.now(timezone.utc)
    
    def get_formatted_timestamp(self, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        Obtém timestamp formatado da internet
        
        Args:
            format_str: String de formatação do datetime
            
        Returns:
            String com timestamp formatado
        """
        timestamp = self.get_synced_timestamp()
        return timestamp.strftime(format_str)
    
    def get_timestamp_with_timezone(self) -> str:
        """
        Obtém timestamp completo com timezone
        
        Returns:
            String com timestamp completo incluindo timezone
        """
        timestamp = self.get_synced_timestamp()
        return timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")
    
    def get_iso_timestamp(self) -> str:
        """
        Obtém timestamp no formato ISO 8601
        
        Returns:
            String com timestamp no formato ISO
        """
        timestamp = self.get_synced_timestamp()
        return timestamp.isoformat()

# Instância global para uso em toda a aplicação
time_sync = InternetTimeSync()

def get_internet_timestamp() -> datetime:
    """
    Função de conveniência para obter timestamp da internet
    
    Returns:
        datetime com timestamp preciso da internet
    """
    return time_sync.get_synced_timestamp()

def get_formatted_internet_timestamp(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Função de conveniência para obter timestamp formatado da internet
    
    Args:
        format_str: String de formatação
        
    Returns:
        String com timestamp formatado
    """
    return time_sync.get_formatted_timestamp(format_str)

def get_brasilia_timestamp(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Função de conveniência para obter timestamp no horário de Brasília
    
    Args:
        format_str: String de formatação
        
    Returns:
        String com timestamp no horário de Brasília
    """
    try:
        # Tentar obter timestamp UTC da internet
        utc_timestamp = time_sync.get_synced_timestamp()
        
        # Converter para horário de Brasília (UTC-3)
        brasilia_offset = timedelta(hours=3)
        brasilia_time = utc_timestamp - brasilia_offset
        
        return brasilia_time.strftime(format_str)
    except Exception:
        # Se falhar, usar horário local do PC
        local_time = datetime.now()
        return local_time.strftime(format_str)

def get_iso_internet_timestamp() -> str:
    """
    Função de conveniência para obter timestamp ISO da internet
    
    Returns:
        String com timestamp ISO
    """
    return time_sync.get_iso_timestamp()


import time
from dataclasses import dataclass, asdict

@dataclass
class AveSession:
    """Representa una sesión de AveOnline activa"""
    id: int
    document: int
    """ Documento de la empresa en AveOnline """
    user: str
    """ Nombre de usuario en AveOnline """
    name: str
    """ Nombre de la empresa en AveOnline """
    email: str
    """ Email de la empresa en AveOnline """
    razon: str
    """ Razon social de la empresa en AveOnline """
    idEnterprise: int
    """ Id de la empresa en AveOnline """
    accessRedirect: str
    token: str
    """ Token de acceso de AveOnline (se envia en el header Authorization) """
    tokenBody: str
    """ Token de acceso de AveOnline (se envia en el body) """
    logisticAdvisorContactNumber: str
    """ Número de contacto del asesor logística de AveOnline """

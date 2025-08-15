from abc import ABC, abstractmethod

class CitiesServiceInterface(ABC):

    @abstractmethod
    async def search(self, query: str, quantity: int = 5):
        """ Busqueda de ciudades """
        pass
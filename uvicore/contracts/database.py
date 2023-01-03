from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union, Mapping, Optional

try:
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
    from sqlalchemy import MetaData, Table
    from aio_databases import Database
    from sqlalchemy.sql import ClauseElement
    from sqlalchemy.engine.result import Row
except:
    sa = None
    AsyncEngine = None
    AsyncSession = None
    Table = None
    MetaData = None
    ClauseElement = None
    Row = None
    Database = None

from uvicore.contracts import DbQueryBuilder
from .connection import Connection
from .package import Package


class Database(ABC):
    pass

    @property
    @abstractmethod
    def default(self) -> str:
        """The default connection str for the main running app"""
        pass

    @property
    @abstractmethod
    def connections(self) -> Dict[str, Connection]:
        """All connections from all packages, keyed by connection str name"""
        pass

    @property
    @abstractmethod
    def engines(self) -> Dict[str, AsyncEngine]:
        """All engines for all unique (by metakey) connections, keyed by metakey"""
        pass

    @property
    @abstractmethod
    def databases(self) -> Dict[str, Database]:
        """All Encode Databases for all unique (by metakey) connections, keyed by metakey"""
        pass

    @property
    @abstractmethod
    def metadatas(self) -> Dict[str, MetaData]:
        """All SQLAlchemy Metadata for all unique (by metakey) connections, keyed by metakey"""
        pass

    @abstractmethod
    def init(self, default: str, connections: List[Connection]) -> None:
        """Initialize the database system with a default connection str and List of all Connections from all packages"""
        pass

    @abstractmethod
    def packages(self, connection: str = None, metakey: str = None) -> List[Package]:
        """Get all packages with the metakey (direct or derived from connection str)."""
        pass

    @abstractmethod
    def metakey(self, connection: str = None, metakey: str = None) -> str:
        """Get one metekay by connection str or metakey"""
        pass

    @abstractmethod
    def connection(self, connection: str = None) -> Connection:
        """Get one connection by connection name"""
        pass

    @abstractmethod
    def metadata(self, connection: str = None, metakey: str = None) -> MetaData:
        """Get one SQLAlchemy Metadata by connection str or metakey"""
        pass

    @abstractmethod
    def table(self, table: str, connection: str = None) -> Table:
        """Get one SQLAlchemy Table by name (without prefix) and connection str or connection.tablename dot notation"""
        pass

    @abstractmethod
    def tablename(self, table: str, connection: str = None) -> str:
        """Get a SQLAlchemy tablename with prefix by name (without prefix) and connection str or connection.tablename dot notation"""
        pass

    @abstractmethod
    def engine(self, connection: str = None, metakey: str = None) -> Engine:
        """Get one SQLAlchemy Engine by connection str or metakey"""
        pass

    @abstractmethod
    def session(self, connection: str = None, metakey: str = None) -> AsyncSession:
        """Get one SQLAlchemy AsyncSession by connection str or metakey"""
        pass


    @abstractmethod
    async def database(self, connection: str = None, metakey: str = None) -> Database:
        """Get one Encode Database by connection str or metakey"""
        pass

    @abstractmethod
    async def disconnect(self, connection: str = None, metakey: str = None, from_all: bool = False) -> None:
        """Disconnect from a database by connection str or metakey.  Of ALL databases."""
        pass

    @abstractmethod
    async def fetchall(self, query: Union[ClauseElement, str], values: Dict = None, connection: str = None, metakey: str = None) -> List[Row]:
        """Fetch List of records from a SQLAlchemy Core Query based on connection str or metakey"""
        pass

    @abstractmethod
    async def fetchone(self, query: Union[ClauseElement, str], values: Dict = None, connection: str = None, metakey: str = None) -> Optional[Row]:
        """Fetch one record from a SQLAlchemy Core Query based on connection str or metakey"""
        pass

    @abstractmethod
    async def execute(self, query: Union[ClauseElement, str], values: Union[List, Dict] = None, connection: str = None, metakey: str = None) -> Any:
        """Execute a SQLAlchemy Core Query based on connection str or metakey"""
        pass

    @abstractmethod
    def query(self, connection: str = None) -> DbQueryBuilder[DbQueryBuilder, None]:
        """Database query builder passthrough"""

    # @property
    # @abstractmethod
    # def events(self) -> Dict: pass

    # @property
    # @abstractmethod
    # def listeners(self) -> Dict[str, List]: pass

    # @property
    # @abstractmethod
    # def wildcards(self) -> List: pass

    # @abstractmethod
    # def register(self, events: Dict):
    #     pass

    # @abstractmethod
    # def listen(self, events: Union[str, List], listener: Any) -> None:
    #     pass

    # @abstractmethod
    # def dispatch(self, event: Any, payload = {}) -> None:
    #     pass

    # @abstractmethod
    # def get_listeners(self, event: str) -> List:
    #     pass

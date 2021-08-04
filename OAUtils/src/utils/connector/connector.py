'''
Created on 26 Oct 2015

@author: Ruben.Alonso
@Description: Module to create different DB connectors and to have access to
their functionalities

'''
from six import with_metaclass
import utils.config as config
import sys
import contextlib
import urllib3
import elasticsearch2 as ES
import utils.exception.handler as EH
import utils.logger.handler as LH
from abc import abstractmethod, ABCMeta


@contextlib.contextmanager
def nostderr():
    """ Function necessary to remove unwanted log information from stdout and
    stderr
    """
    savestderr = sys.stderr

    class Devnull(object):
        def write(self, _): pass

        def flush(self): pass
    sys.stderr = Devnull()
    try:
        yield
    finally:
        sys.stderr = savestderr


class U_DBConnection(object):
    """ Factory class to select among all the possible DB we can provide"""
    __conn = None
    __type = None

    @classmethod
    def get_connection(cls, typeDB):
        """Factory function which chooses among the possible DB

        :param typeDB: select which DB is gonig to be created by the factory
                       function

        :raises: DBConnectionError

        :return: connector object connected to the DB
        """
        LH.logger.info("Getting DB connection")
        if cls.__conn is None:
            if "elastic_search_v1" == typeDB:
                LH.logger.info("ElasticSearch connection")
                cls.__type = typeDB
                cls.__conn = _U_ElasticSearchV1(cls)
                return cls.__conn
            raise EH.InputError("Incorrect BD name: " + typeDB)
        else:
            if cls.__type == typeDB:
                LH.logger.info("Returning existing connection")
            else:
                LH.logger.warning("Returning existing connection but from a different DB type. Please, close the existing one and create the one you want")
            return cls.__conn

    @classmethod
    def del_connection(cls):
        """Function to close the connection when one exists"""
        if cls.__conn is not None:
            LH.logger.info("Closing the connection")
            cls.__conn = None


class U_AbstractConnector(with_metaclass(ABCMeta)):
    """ Abstract class for the different connectors we might use"""

    @abstractmethod
    def execute_search_query_sort_pag(self, index, docType, body, size, offset, sort):
        """ Abstract method for searching on a DB

        :param index -- table to run the query to
        :param docType -- type of document target of the query
        :param body -- query to execute
        :param size -- number of results
        :param offset -- offset point to start the search
        :param sort -- fields to sort from
        """
        raise NotImplementedError

    @abstractmethod
    def execute_search_query_scroll(self, index, docType, body):
        """ Abstract method for searching on a DB

        :param index -- table to run the query to
        :param docType -- type of document target of the query
        :param body -- query to execute
        """
        raise NotImplementedError

    @abstractmethod
    def execute_create_table(self, index):
        """ Abstract method for creating a new table

        :param index -- table to be created
        """
        raise NotImplementedError

    @abstractmethod
    def execute_create_doc_type(self, index, docType, mapping):
        """ Abstract method for creating a new type of document

        :param index -- table to run the query to
        :param docType -- type of document to be created
        :param mapping -- structure of the document
        """
        raise NotImplementedError

    @abstractmethod
    def execute_insert_query(self, index, docType, body, docID=None):
        """ Abstract method for inserting new data in the DB

        :param index -- table to run the query to
        :param docType -- type of document target of the query
        :param body -- query to execute
        """
        raise NotImplementedError

    @abstractmethod
    def execute_update_query(self, index, docType, docId, body):
        """ Abstract method for updating a register by ID

        :param index -- table to run the query to
        :param docType -- type of document target of the query
        :param docId -- doc to be updated
        :param body -- information to be updated to the specified document
        """
        raise NotImplementedError

    @abstractmethod
    def execute_delete_table(self, index):
        """ Abstract method for deleting the content of a table

        :param index -- table to run the delete command
        """
        raise NotImplementedError

    @abstractmethod
    def execute_delete_doc(self, index, docId):
        """ Abstract method for deleting a register by ID

        :param index -- table to run the delete command
        :param docId -- ID of the document to be deleted
        """
        raise NotImplementedError

    @abstractmethod
    def close(self):
        """ Method to close the connection to the DB"""
        raise NotImplementedError


class _U_ElasticSearchV1(U_AbstractConnector):
    """ Creates a DB connector to the ES database and provides different
        queries to manage the content"""

    def __init__(self, fact):
        """Constructor to initialize the DB connector

        :raises DBConnectionError
        """
        self.fact = fact
        try:
            LH.logger.info("Trying to connect to {db}".format(db=config.configES))
            self.connector = ES.Elasticsearch(config.configES)
        except urllib3.exceptions.LocationValueError as err:
            raise EH.DBConnectionError("Location value error", str(err))
        try:
            with nostderr():
                self.connector.ping()
        except ES.ConnectionTimeout as err:
            raise EH.DBConnectionError(message="Connection timeout error",
                                       error=str(err.info))
        except urllib3.exceptions.NewConnectionError as err:
            raise EH.DBConnectionError(message="New connection error",
                                       error=str(err))
        except ES.ConnectionError as err:
            raise EH.DBConnectionError(message="Generic connection error",
                                       error=str(err.info))
        except Exception as err:
            raise EH.DBConnectionError(message="Other connection error",
                                       error=str(err.info))

    def execute_search_query_sort_pag(self, index, docType=None, body="", size=100, offset=0, sort=""):
        """ Method for executing a search on the DB

        :param index -- table to run the query to
        :param docType -- type of document target of the query
        :param body -- query to execute
        :param size -- number of results
        :param offset -- offset point to start the search
        :param sort -- fields to sort from

        :returns: elastic search response object
        """
        LH.logger.info("Executing search query on index {index}".format(index=index))
        if size + offset > 10000:
            raise EH.InputError(error="The sum of size and offset shouldn't be bigger than 10000")
        try:
            result = self.connector.search(index=index,
                                           doc_type=docType,
                                           body=body,
                                           size=size,
                                           from_=offset,
                                           sort=sort)

            return result['hits']
        except ES.ConnectionTimeout as err:
            raise EH.DBConnectionError(message="Connection timeout error",
                                       error=str(err.info))
        except ES.ConnectionError as err:
            raise EH.DBConnectionError(message="Generic connection error",
                                       error=str(err.info))
        except ES.ElasticsearchException as err:
            raise EH.GenericError(message="Exception while searching",
                                  error=str(err))

    def execute_search_query_scroll(self, index, docType=None, body=""):
        """ Method for executing a search on the DB

        :param index -- table to run the query to
        :param docType -- type of document target of the query
        :param body -- query to execute

        :returns: elastic search response object
        """
        LH.logger.info("Executing search query on index {index}".format(index=index))
        try:
            result = ES.helpers.scan(client=self.connector,
                                  query=body,
                                  raise_on_error=True,
                                  index=index,
                                  doc_type=docType,
                                  scroll='15m')
            response = {}
            response['hits'] = []
            response['total'] = 0
            for item in result:
                response['hits'].append(item)
                response['total'] += 1
            return response
        except ES.ConnectionTimeout as err:
            raise EH.DBConnectionError(message="Connection timeout error",
                                       error=str(err.info))
        except ES.ConnectionError as err:
            raise EH.DBConnectionError(message="Generic connection error",
                                       error=str(err.info))
        except ES.ElasticsearchException as err:
            raise EH.GenericError(message="Exception while searching",
                                  error=str(err))

    def execute_create_table(self, index):
        """ Method for creating a table (index) on ES DB

        :param index -- table to run the query to

        :returns: elastic search response object
        """
        LH.logger.info("Creating a new table {0}".format(index))
        try:
            response = self.connector.indices.create(index)
            return response
        except ES.ConnectionTimeout as err:
            raise EH.DBConnectionError(message="Connection timeout error",
                                       error=str(err.info))
        except ES.ConnectionError as err:
            raise EH.DBConnectionError(message="Generic connection error",
                                       error=str(err.info))
        except ES.RequestError as err:
            if err.error.find('index_already_exists_exception') != -1 or err.error.find('IndexAlreadyExistsException') != -1:
                LH.logger.info("Table already exists {0}".format(index))
                return 1
        except ES.ElasticsearchException as err:
            raise EH.GenericError(message="Exception while creating a new table", error=str(err.info))

    def execute_create_doc_type(self, index, docType, mapping):
        """ Method for creating a document mapping on the ES DB

        :param index -- table to run the query to
        :param docType -- name of document
        :param mapping -- document mapping

        :returns: elastic search response object
        """
        LH.logger.info("Creating new doc type {0}".format(docType))
        try:
            response = self.connector.indices.put_mapping(doc_type=docType,
                                                          index=index,
                                                          body=mapping)
            self.connector.indices.refresh(index=index)
            return response  #do we need to check the response in here or in the function calling??
        except ES.ConnectionTimeout as err:
            raise EH.DBConnectionError(message="Connection timeout error",
                                       error=str(err.info))
        except ES.ConnectionError as err:
            raise EH.DBConnectionError(message="Generic connection error",
                                       error=str(err.info))
        except ES.NotFoundError as err:
            raise EH.InputError(message="Not found error",
                                error=str(err))
        except ES.RequestError as err:
            raise EH.GenericError(message="Transport error",
                                  error=str(err))
        except ES.ElasticsearchException as err:
            raise EH.GenericError(message="Exception while creating a document \
                                  type", error=str(err.info))

    def execute_insert_query(self, index, docType, body, docId=None):
        """ Method for executing a insert on the DB

        :param index -- table to run the query to
        :param docType -- type of document target of the query
        :param body -- document body
        :param docId -- id to save the document

        :returns: elastic search response object
        """
        LH.logger.info("Inserting new {type} document into {index}".format(type=docType, index=index))
        try:
            response = self.connector.index(index=index, doc_type=docType,
                                            body=body, id=docId)
            self.connector.indices.refresh(index=index)
            return response
        except ES.ConnectionTimeout as err:
            raise EH.DBConnectionError(message="Connection timeout error",
                                       error=str(err.info))
        except ES.ConnectionError as err:
            raise EH.DBConnectionError(message="Generic connection error",
                                       error=str(err.info))
        except ES.RequestError as err:
            raise EH.GenericError(message="Incorrect inserting query",
                                  error=str(err.info))
        except ES.ElasticsearchException as err:
            raise EH.GenericError(message="Exception while inserting",
                                  error=str(err.info))

    def execute_bulk_insert_query(self, index, docType, body, docId=None):
        """ Method for executing a insert on the DB

        :param index -- table to run the query to
        :param docType -- type of document target of the query
        :param body -- documents list of content
        :param docId -- id to save the document

        :returns: elastic search response object
        """
        LH.logger.info("Inserting new '{type}' document into {index}".format(type=docType, index=index))
        try:
            actions = []
            for document in body:
                action = {
                    "_index": index,
                    "_type": docType,
                    "_source": document
                    }
                actions.append(action)
            if len(actions) > 0:
                response = ES.helpers.bulk(self.connector, actions)
            self.connector.indices.refresh(index=index)
            return response
        except ES.ConnectionTimeout as err:
            raise EH.DBConnectionError(message="Connection timeout error",
                                       error=str(err.info))
        except ES.ConnectionError as err:
            raise EH.DBConnectionError(message="Generic connection error",
                                       error=str(err.info))
        except ES.RequestError as err:
            raise EH.GenericError(message="Incorrect inserting query",
                                  error=str(err.info))
        except ES.ElasticsearchException as err:
            raise EH.GenericError(message="Exception while inserting",
                                  error=str(err.info))

    def execute_update_query(self, index, docType, docId, body):
        """ Method for executing an update on the DB

        :param index -- table to run the query to
        :param docType -- type of document target of the query
        :param id -- id of the document to update
        :param body -- query to execute

        :returns: elastic search response object
        """
        LH.logger.info("Updating {type} document {id} from {index}".format(type=docType, id=docId, index=index))
        try:
            response = self.connector.update(index=index,
                                             doc_type=docType,
                                             id=docId,
                                             body=body)
            self.connector.indices.refresh(index=index)
            return response
        except ES.ConnectionTimeout as err:
            raise EH.DBConnectionError(message="Connection timeout error",
                                       error=str(err.info))
        except ES.ConnectionError as err:
            raise EH.DBConnectionError(message="Generic connection error",
                                       error=str(err.info))
        except ES.NotFoundError as err:
            raise EH.GenericError(message="Document not found",
                                  error=str(err))
        except ES.ElasticsearchException as err:
            raise EH.GenericError(message="Exception while updating a document",
                                  error=str(err.info))

    def execute_delete_table(self, index):
        """ Method for deleting a table from ES DB

        :param index -- table to delete

        :returns: elastic search response object
        """
        LH.logger.info("Deleting table {0}".format(index))
        try:
            return self.connector.indices.delete(index=index)
        except ES.ConnectionTimeout as err:
            raise EH.DBConnectionError(message="Connection timeout error",
                                       error=str(err.info))
        except ES.ConnectionError as err:
            raise EH.DBConnectionError(message="Generic connection error",
                                       error=str(err.info))
        except ES.NotFoundError as err:
            LH.logger.info("Index doesn't exist {0}".format(index))
            return 1
        except ES.ElasticsearchException as err:
            raise EH.GenericError(message="Exception while deleting a table",
                                  error=str(err.info))

    def execute_delete_doc(self, index, docType, docId):
        """ Method for executing a search on the DB

        :param index -- table to run the query to
        :param docType -- type of document target of the query
        :param docId -- ID of the document to be removed

        :returns: elastic search response object
        """
        LH.logger.info("Deleting document {0}".format(docId))
        try:
            response = self.connector.delete(index, docType, docId)
            self.connector.indices.refresh(index=index)
            return response
        except ES.ConnectionTimeout as err:
            raise EH.DBConnectionError(message="Connection timeout error",
                                       error=str(err.info))
        except ES.ConnectionError as err:
            raise EH.DBConnectionError(message="Generic connection error",
                                       error=str(err.info))
        except ES.NotFoundError as err:
            raise EH.GenericError(message="Document not found",
                                  error=str(err))
        except ES.ElasticsearchException as err:
            raise EH.GenericError(message="Exception while deleting a document",
                                  error=str(err.info))

    def close(self):
        """ Method for closing the connection to the DB
        """
        LH.logger.info("Closing the connection to the DB")
        self.fact.del_connection()


import utils.connector.connector as DB
import utils.config as config
from werkzeug.datastructures import MultiDict
from datetime import datetime
import math

def to_timestamp(dt, epoch=datetime(1970, 1, 1)):
    """Function to convert datetime into timestamp since it doesn't exist in
    python v2

    :param dt: date to be converted
    :param epoch: date to start counting from to create the date stamp

    :return timestamp of the date since epoch
    """
    td = dt - epoch
    return (td.microseconds + (td.seconds + td.days * 86400) * 10**6) / 10**6


class HarvesterModel():
    '''
    Provides a querys for getting data from ES 
    '''
    
    def __init__(self):
        self.__conn = DB.U_DBConnection().get_connection(config.DB_NAME)
        self.__match_all = config.MATCH_ALL
        self.limit = 10
    
    def get_webservices(self, page_num = 0):
        '''
        gets all webservices 
        
        Return:
            list of webbservices
        '''
        
        result = self.__conn.execute_search_query_sort_pag(config.WEBSERVICES_INDEX_NAME,
                                                           config.WEBSERVICES_DOCTYPE_NAME,
                                                           self.__match_all,
                                                           self.limit,
                                                           page_num*self.limit,
                                                           sort='name')
        total = result.get('total',{}).get('value', 0)
        return result['hits'], int(math.ceil(float(total)/float(self.limit)))
    
    def get_history(self, page_num = 0):
        '''
        gets history
        
        Return:
            list of history
        '''
        result = self.__conn.execute_search_query_sort_pag(config.HISTORY_INDEX_NAME,
                                                           config.HISTORY_DOCTYPE_NAME,
                                                           self.__match_all,
                                                           self.limit,
                                                           page_num*self.limit,
                                                           sort='date:desc')
        
        history = result['hits']
        for idx,item in enumerate(history):
            history[idx]['_source']['end_date'] = self.__timestamp_to_date(history[idx]['_source']['end_date'])
            history[idx]['_source']['start_date'] = self.__timestamp_to_date(history[idx]['_source']['start_date'])
            history[idx]['_source']['date'] = self.__timestamp_to_datetime(history[idx]['_source']['date'])
        total = result.get('total',{}).get('value', 0)
        return history, int(math.ceil(float(total)/float(self.limit)))
    
    def __timestamp_to_date(self, timestamp):
        return datetime.fromtimestamp(int(timestamp/1000)).strftime('%Y-%m-%d')
    
    def __timestamp_to_datetime(self, timestamp):
        return datetime.fromtimestamp(int(timestamp/1000)).strftime('%Y-%m-%d %H:%M:%S')
    
    def get_webservice(self, webservice_id):
        '''
        get webservice with all data
        
        Return:
            webservice object
        '''
        query = {
            "query": {
                "match": {
                    '_id' : str(webservice_id)
                              }
            }
        }
        
        result = self.__conn.execute_search_query_scroll(config.WEBSERVICES_INDEX_NAME,
                                                         config.WEBSERVICES_DOCTYPE_NAME,
                                                         query)
        webservice = result['hits']
        for idx,item in enumerate(webservice):
            webservice[idx]['_source']['end_date'] = self.__timestamp_to_date(webservice[idx]['_source']['end_date'])
        
        return webservice
    
    def save_webservice(self, webservice, webservice_id = None):
        '''
        validate and save webservice object
        
        Return:
            webservice object
        '''
        webservices = {}
        webservices['name'] = webservice.name.data
        webservices['url'] = webservice.url.data
        webservices['query'] = webservice.query.data
        webservices['frequency'] = webservice.frequency.data
        webservices['active'] = webservice.active.data
        webservices['email'] = webservice.email.data
        webservices['end_date'] = to_timestamp(datetime.strptime(webservice.end_date.data, "%Y-%m-%d")) * 1000
        webservices['engine'] = webservice.engine.data
        webservices['wait_window'] = webservice.wait_window.data

        if(webservice_id is None):
            result = self.__conn.execute_insert_query(config.WEBSERVICES_INDEX_NAME, config.WEBSERVICES_DOCTYPE_NAME, webservices) 
        else:    
            doc = {}
            doc['doc'] = webservices            
            result = self.__conn.execute_update_query(config.WEBSERVICES_INDEX_NAME, config.WEBSERVICES_DOCTYPE_NAME, webservice_id, doc)
        return result
                                                 
    
    def __valid_webservice(self, webservice):
        ''' 
        valid all information from webservice and save it if everything goes ok
        
        '''
        return True
    
    def delete(self, webservice_id):
        self.__conn.execute_delete_doc(config.WEBSERVICES_INDEX_NAME, config.WEBSERVICES_DOCTYPE_NAME, webservice_id)
    
    def multidict_form_data(self,data):
        '''
        
        '''
        result = MultiDict(
                         [
                          ('url', data[0]['_source']['url']),
                          ('name',data[0]['_source']['name']),
                          ('query',data[0]['_source']['query']),
                          ('end_date',data[0]['_source']['end_date']),
                          ('email',data[0]['_source']['email']),
                          #('end_date',date.fromtimestamp(data[0]['_source']['end_date']/1000)),
                          ('frequency',data[0]['_source']['frequency']),
                          ('engine',data[0]['_source']['engine']),
                          ('wait_window',data[0]['_source']['wait_window'])
                          ]
                         )
        
        if(data[0]['_source']['active']):
            result['active'] = 1
        return result

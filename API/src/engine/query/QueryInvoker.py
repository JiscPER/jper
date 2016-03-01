'''
Created on 06 Nov 2015

Engine invoker

@author: Mateusz.Kasiuba
'''
from engine.query.QueryEngineMultiPage import H_QueryEngineMultiPage
from utils.config import MULTI_PAGE, DB_NAME
from utils.connector.connector import U_DBConnection


class H_QueryInvoker():
    
    @staticmethod
    def get_engine(engine_name, db, url, date_start = 0, date_end = 0):
        if(engine_name == MULTI_PAGE):
            return H_QueryEngineMultiPage(db, url, date_start, date_end)
        
        raise ValueError('Engine %s do not exists!'% engine_name)
    
    @staticmethod
    def is_valid(engine_name, url):
        DB = U_DBConnection().get_connection(DB_NAME)
        if(engine_name == MULTI_PAGE):
            return H_QueryEngineMultiPage(DB,url).valid()
        
        raise ValueError('Engine %s do not exists!'% engine_name)
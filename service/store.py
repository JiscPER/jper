from octopus.core import app
from octopus.lib import plugin

import os, shutil, codecs

class StoreException(Exception):
    pass

class StoreFactory(object):

    @classmethod
    def get(cls):
        si = app.config.get("STORE_IMPL")
        sm = plugin.load_class(si)
        return sm()

class Store(object):

    def store(self, container_id, target_name, source_path=None, source_stream=None):
        pass

    def list(self, container_id):
        pass

    def get(self, container_id, target_name):
        return None

    def delete(self, container_id, target_name=None):
        pass

class StoreLocal(Store):
    """
    Primitive local storage system.  Use this for testing.

    Probably don't use it in production - it doesn't do anything intelligent, and may break
    """
    def __init__(self):
        self.dir = app.config.get("STORE_LOCAL_DIR")
        if self.dir is None:
            raise StoreException("STORE_LOCAL_DIR is not defined in config")

    def store(self, container_id, target_name, source_path=None, source_stream=None):
        cpath = os.path.join(self.dir, container_id)
        if not os.path.exists(cpath):
            os.makedirs(cpath)
        tpath = os.path.join(cpath, target_name)

        if source_path:
            shutil.copyfile(source_path, tpath)
        elif source_stream:
            with codecs.open(tpath, "wb") as f:
                f.write(source_stream.read())

    def list(self, container_id):
        cpath = os.path.join(self.dir, container_id)
        return os.listdir(cpath)

    def get(self, container_id, target_name):
        cpath = os.path.join(self.dir, container_id, target_name)
        if os.path.exists(cpath) and os.path.isfile(cpath):
            f = codecs.open(cpath, "r")
            return f

    def delete(self, container_id, target_name=None):
        cpath = os.path.join(self.dir, container_id)
        if target_name is not None:
            cpath = os.path.join(cpath, target_name)
        if os.path.exists(cpath):
            if os.path.isfile(cpath):
                os.remove(cpath)
            else:
                shutil.rmtree(cpath)


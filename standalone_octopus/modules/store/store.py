from standalone_octopus.core import app
from standalone_octopus.lib import plugin

import os, shutil, requests


class StoreException(Exception):
    pass


class StoreFactory(object):

    @classmethod
    def get(cls):
        """
        Returns an implementation of the base Store class
        """
        si = app.config.get("STORE_IMPL")
        sm = plugin.load_class(si)
        return sm()

    @classmethod
    def tmp(cls):
        """
        Returns an implementation of the base Store class which should be able
        to provide local temp storage to the app.  In addition to the methods supplied
        by Store, it must also provide a "path" function to give the path on-disk to
        the file
        """
        si = app.config.get("STORE_TMP_IMPL")
        sm = plugin.load_class(si)
        return sm()


class Store(object):

    def store(self, container_id, target_name, source_path=None, source_stream=None):
        pass

    def exists(self, container_id):
        return False

    def list(self, container_id):
        pass

    def get(self, container_id, target_name):
        return None

    def delete(self, container_id, target_name=None):
        pass


class StoreLocal(Store):
    """
    Primitive local storage system.  Use this for testing in place of remote store
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
            data = source_stream.read()
            mode = "wb" if isinstance(data, bytes) else "w"
            with open(tpath, mode) as f:
                while data:
                    f.write(data)
                    data = source_stream.read()

    def exists(self, container_id):
        cpath = os.path.join(self.dir, container_id)
        return os.path.exists(cpath) and os.path.isdir(cpath)

    def list(self, container_id):
        cpath = os.path.join(self.dir, container_id)
        return os.listdir(cpath)

    def get(self, container_id, target_name):
        cpath = os.path.join(self.dir, container_id, target_name)
        if os.path.exists(cpath) and os.path.isfile(cpath):
            f = open(cpath, "rb")
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


class StoreJper(Store):
    def __init__(self):
        self.url = app.config.get("STORE_JPER_URL")
        if self.url is None:
            raise StoreException("STORE_JPER_URL is not defined in config")

    def store(self, container_id, target_name, source_path=None, source_stream=None):
        cpath = os.path.join(self.url, container_id)
        r = requests.get(cpath)
        if r.status_code != 200:
            requests.put(cpath)
            try:
                app.logger.info('Store - Container:' + container_id + ' ' + cpath + ' container to be created ' + str(r.status_code))
            except:
                pass
        else:
            try:
                app.logger.info('Store - Container:' + container_id + ' ' + cpath + ' container already exists ' + str(r.status_code))
            except:
                pass

        tpath = os.path.join(cpath, target_name)

        if source_path is not None:
            try:
                app.logger.info('Store - Container:' + container_id + ' attempting to save source path to ' + tpath)
            except:
                pass
            with open(source_path,'rb') as payload:
                #headers = {'content-type': 'application/x-www-form-urlencoded'}
                #r = requests.post(tpath, data=payload, verify=False, headers=headers)
                r = requests.post(tpath, files={'file': payload})
        elif source_stream is not None:
            try:
                app.logger.info('Store - Container:' + container_id + ' attempting to save source stream to ' + tpath)
            except:
                pass
            #headers = {'content-type': 'application/x-www-form-urlencoded'}
            #r = requests.post(tpath, data=source_stream, verify=False, headers=headers)
            r = requests.post(tpath, files={'file': source_stream})
        try:
            app.logger.info('Store - Container:' + container_id + ' ' + tpath + ' request resulted in ' + str(r.status_code))
        except:
            pass

    def exists(self, container_id):
        cpath = os.path.join(self.url, container_id)
        r = requests.get(cpath)
        try:
            app.logger.info('Store - Container:' + container_id + ' checking existence ' + str(r.status_code))
        except:
            pass
        if r.status_code == 200:
            try:
                listing = r.json()
                return isinstance(listing, list)
            except:
                return False
        else:
            return False

    def list(self, container_id):
        cpath = os.path.join(self.url, container_id)
        r = requests.get(cpath)
        try:
            app.logger.info('Store - Container:' + container_id + ' listing requested and returned')
        except:
            pass
        try:
            return r.json()
        except:
            return []

    def get(self, container_id, target_name):
        cpath = os.path.join(self.url, container_id, target_name)
        r = requests.get(cpath, stream=True)
        if r.status_code == 200:
            try:
                app.logger.info('Store - Container:' + container_id + ' ' + cpath + ' retrieved and returning raw')
            except:
                pass
            return r.raw
        else:
            try:
                app.logger.info('Store - Container:' + container_id + ' ' + cpath + ' could not be retrieved')
            except:
                pass
            return False

    def delete(self, container_id, target_name=None):
        cpath = os.path.join(self.url, container_id)
        if target_name is not None:
            cpath = os.path.join(cpath, target_name)
        try:
            app.logger.info('Store - Container:' + container_id + ' ' + cpath + ' is being deleted')
        except:
            pass
        requests.delete(cpath)


class TempStore(StoreLocal):
    def __init__(self):
        self.dir = app.config.get("STORE_TMP_DIR")
        if self.dir is None:
            raise StoreException("STORE_TMP_DIR is not defined in config")

    def path(self, container_id, filename, must_exist=True):
        fpath = os.path.join(self.dir, container_id, filename)
        if not os.path.exists(fpath) and must_exist:
            raise StoreException("Unable to create path for container {x}, file {y}".format(x=container_id, y=filename))
        return fpath

    def list_container_ids(self):
        return [x for x in os.listdir(self.dir) if os.path.isdir(os.path.join(self.dir, x))]

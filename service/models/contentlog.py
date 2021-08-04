
from service import dao
from octopus.lib import dataobj

class ContentLog(dataobj.DataObj, dao.ContentLogDAO):
    '''
    {
        "id" : "<unique persistent account id>",
        "created_date" : "<date account created>",
        "last_updated" : "<date account last modified>",

        "user" : "<user that requested the content>",
        "notification": "<the notification the requested content is from>",
        "filename": ">the requested filename if any",
        "delivered_from" : "<one of store, proxy, notfound>",
    }
    '''

    @property
    def user(self):
        return self._get_single("user", coerce=self._utf8_unicode())

    @user.setter
    def user(self, user):
        self._set_single("user", user, coerce=self._utf8_unicode())

    @property
    def notification(self):
        return self._get_single("notification", coerce=self._utf8_unicode())

    @user.setter
    def notification(self, notification):
        self._set_single("notification", notification, coerce=self._utf8_unicode())

    @property
    def filename(self):
        return self._get_single("filename", coerce=self._utf8_unicode())

    @user.setter
    def filename(self, filename):
        self._set_single("filename", filename, coerce=self._utf8_unicode())

    @property
    def delivered_from(self):
        return self._get_single("delivered_from", coerce=self._utf8_unicode())

    @user.setter
    def delivered_from(self, delivered_from):
        self._set_single("delivered_from", delivered_from, coerce=self._utf8_unicode())

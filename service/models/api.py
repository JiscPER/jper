from octopus.lib import dataobj

class NotificationList(dataobj.DataObj):
    """
    {
        "since" : "<date from which results start in the form YYYY-MM-DDThh:mm:ssZ>",
        "page" : "<page number of results>,
        "pageSize" : "<number of results per page>,
        "timestamp" : "<timestamp of this request in the form YYYY-MM-DDThh:mm:ssZ>",
        "total" : "<total number of results at this time>",
        "notifications" : [
            "<ordered list of Outgoing Data Model JSON objects>"
        ]
    }
    """

    @property
    def since(self):
        return self._get_single("since", coerce=self._date_str())

    @since.setter
    def since(self, val):
        self._set_single("since", val, coerce=self._date_str())

    @property
    def page(self):
        return self._get_single("page", coerce=self._int())

    @page.setter
    def page(self, val):
        self._set_single("page", val, coerce=self._int())

    @property
    def page_size(self):
        return self._get_single("pageSize", coerce=self._int())

    @page_size.setter
    def page_size(self, val):
        self._set_single("pageSize", val, coerce=self._int())

    @property
    def timestamp(self):
        return self._get_single("timestamp", coerce=self._date_str())

    @timestamp.setter
    def timestamp(self, val):
        self._set_single("timestamp", val, coerce=self._date_str())

    @property
    def total(self):
        return self._get_single("total", coerce=self._int())

    @total.setter
    def total(self, val):
        self._set_single("total", val, coerce=self._int())

    @property
    def notifications(self):
        return self._get_list("notifications")

    @notifications.setter
    def notifications(self, val):
        self._set_list("notifications", val)

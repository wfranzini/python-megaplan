#!/usr/bin/env python
# vim: fileencoding=utf-8:

"""Megaplan client module.

Provides a class that implements Megaplan authentication and request signing.
Only supports POST requests.  The complete API documentation is at:

http://wiki.megaplan.ru/API

To use a password:

    import megaplan
    c = megaplan.Client('xyz.megaplan.ru')
    c.authenticate(login, password)

To use tokens:

    import megaplan
    # access_id, secret_key = c.authenticate(login, password)
    c = megaplan.Client('xyz.megaplan.ru', access_id, secret_key)

To list actual tasks:

    res = c.request('BumsTaskApiV01/Task/list.api', { 'Status': 'actual' })
    for task in res['tasks']:
        print task

License: BSD.
"""

__author__ = "Justin Forest"
__email__ = "hex@umonkey.net"
__license__ = "GPL"
__version__ = "1.3"


import base64
import hashlib
import hmac
import json
import netrc
import time
import urllib
import urllib2


def _utf(s):
    if isinstance(s, unicode):
        s = s.encode("utf-8")
    return s


class Request(object):
    def __init__(self, hostname, access_id, secret_key, uri, data=None):
        self.method = 'POST'
        self.proto = 'https'
        self.uri = hostname +'/'+ uri
        self.access_id = access_id
        self.secret_key = secret_key
        self.content_type = 'application/x-www-form-urlencoded'
        self.date = time.strftime('%a, %d %b %Y %H:%M:%S +0000', time.gmtime())
        self.signature = None
        self.data = data

    def sign(self):
        text = '\n'.join([self.method, '', self.content_type, self.date, self.uri])
        self.signature = base64.b64encode(hmac.new(self.secret_key, text, hashlib.sha1).hexdigest())

    def send(self):
        url = self.proto + '://' + self.uri
        data = self.data and urllib.urlencode(self.data)

        req = urllib2.Request(url, data)
        req.add_header('Date', self.date)
        req.add_header('Accept', 'application/json')
        req.add_header('User-Agent', 'python-megaplan')
        if self.signature:
            req.add_header('X-Authorization', self.access_id + ':' + self.signature)

        res = urllib2.urlopen(req)
        data = json.loads(res.read())
        if data['status']['code'] != 'ok':
            m = data["status"]["message"]
            if isinstance(m, list):
                m = m[0]

            if isinstance(m, dict):
                raise Exception(_utf(m["msg"]))

            raise Exception(data['status']['message'])

        if "data" in data:
            return data['data']


class Client(object):
    def __init__(self, hostname, access_id=None, secret_key=None):
        self.hostname = hostname

        if access_id is None and secret_key is None:
            access_id, secret_key = self.get_netrc_auth(hostname)

        self.access_id = access_id
        self.secret_key = secret_key

    def get_netrc_auth(self, hostname):
        n = netrc.netrc()
        auth = n.authenticators(hostname)
        if auth is None:
            return None, None
        return auth[0], auth[2]

    def authenticate(self, login, password):
        """Authenticates the client.

        The access_id and secret_key values are returned.  They can be stored
        and used later to create Client instances that don't need to log in."""
        data = self.request('BumsCommonApiV01/User/authorize.api', { 'Login': login, 'Password': hashlib.md5(password).hexdigest() }, signed=False)
        self.access_id = data['AccessId']
        self.secret_key = data['SecretKey']
        return self.access_id, self.secret_key

    def request(self, uri, args=None, signed=True):
        """Sends a request, returns the data.

        Args should be a dictionary or None; uri must not begin with a slash
        (e.g., "BumsTaskApiV01/Task/list.api").  If an error happens, an
        exception occurs."""
        if uri != "BumsCommonApiV01/User/authorize.api" and (self.access_id is None or self.secret_key is None):
            raise Exception('Authenticate first.')
        req = Request(str(self.hostname), str(self.access_id), str(self.secret_key), uri, args)
        if signed:
            req.sign()
        return req.send()

    def _task_id(self, task_id):
        if task_id < 1000000:
            task_id += 1000000
        return task_id

    # SOME HELPER METHODS

    def add_task(self, name, text, responsible=None, parent_task=None):
        args = {
            "Model[Name]": _utf(name),
            "Model[Statement]": _utf(text),
        }

        if responsible:
            args["Model[Responsible]"] = responsible

        if parent_task:
            args["Model[SuperTask]"] = parent_task

        return self.request("BumsTaskApiV01/Task/create.api", args)

    def get_incoming_tasks(self):
        """Returns all visible tasks"""
        return self.request('BumsTaskApiV01/Task/list.api', {
            'Folder': 'incoming',
            'Detailed': True,
        })["tasks"]

    def get_projects(self, folder="incoming", status="any"):
        return self.request("BumsProjectApiV01/Project/list.api", {
            "Folder": folder,
            "Status": status,
            "Detailed": True,
        })["projects"]

    def get_actual_tasks(self):
        """Returns your active tasks as a list of dictionaries."""
        return self.request('BumsTaskApiV01/Task/list.api', { 'Status': 'actual' })['tasks']

    def get_tasks_by_status(self, status=None):
        """Returns your active tasks as a list of dictionaries."""
        return self.request('BumsTaskApiV01/Task/list.api', { 'Status': status })['tasks']

    def get_task_details(self, task_id):
        """Returns task description or None if there's no such task."""
        try:
            return self.request('BumsTaskApiV01/Task/card.api', { 'Id': self._task_id(task_id) })
        except urllib2.HTTPError, e:
            if e.getcode() == 404:
                return None
            raise e

    def act(self, task_id, action):
        try:
            return self.request("BumsTaskApiV01/Task/action.api", {
                "Id": self._task_id(task_id),
                "Action": action,
            })
        except urllib2.HTTPError, e:
            if e.getcode() == 403:
                return False
            raise e

    def get_all_comments(self, actual=False):
        return self.request('BumsCommonApiV01/Comment/all.api', {
            "OnlyActual": "true" if actual else "false",
        })["comments"]

    def get_task_comments(self, task_id):
        return self.request('BumsCommonApiV01/Comment/list.api', {
            'SubjectType': 'task',
            'SubjectId': task_id,
        })["comments"]

    def get_project_comments(self, project_id):
        return self.request('BumsCommonApiV01/Comment/list.api', {
            'SubjectType': 'project',
            'SubjectId': project_id,
        })["comments"]

    def add_task_comment(self, task_id, text, hours=0, date=None):
        return self._add_comment("task", task_id, text, hours, date)

    def add_project_comment(self, project_id, text, hours=0, date=None):
        return self._add_comment("project", project_id, text, hours, date)

    def _add_comment(self, _type, _id, text, hours, date=None):
        msg = {
            "SubjectType": _type,
            "SubjectId": self._task_id(_id),
            "Model[Text]": text,
            "Model[Work]": hours,
        }
        if date is not None:
            msg["Model[WorkDate]"] = date
        return self.request("BumsCommonApiV01/Comment/create.api", msg)

    def _task_id(self, task_id):
        if task_id < 1000000:
            task_id += 1000000
        return task_id

    def __repr__(self):
        if self.access_id is not None:
            return "<megaplan.Client access_id=%s>" % self.access_id
        return super(Client, self).__repr__()

__all__ = [ 'Client' ]

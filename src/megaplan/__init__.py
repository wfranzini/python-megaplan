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

import base64
import hashlib
import hmac
import json
import time
import urllib
import urllib2


class Request:
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
            raise Exception(data['status']['message'])

        if "data" in data:
            return data['data']


class Client:
    def __init__(self, hostname, access_id=None, secret_key=None):
        self.hostname = hostname
        self.access_id = access_id
        self.secret_key = secret_key

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
        req = Request(self.hostname, self.access_id, self.secret_key, uri, args)
        if signed:
            req.sign()
        return req.send()

    def _task_id(self, task_id):
        if task_id < 1000000:
            task_id += 1000000
        return task_id

    # SOME HELPER METHODS

    def get_incoming_tasks(self):
        """Returns all visible tasks"""
        return self.request('BumsTaskApiV01/Task/list.api', {
            'Folder': 'incoming',
            'Detailed': True,
        })["tasks"]

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

    def get_task_comments(self, task_id):
        return self.request('BumsCommonApiV01/Comment/list.api', { 'SubjectType': 'task', 'SubjectId': task_id })["comments"]

    def add_task_comment(self, task_id, text, hours=0):
        return self._add_comment("task", task_id, text, hours)

    def add_project_comment(self, project_id, text, hours=0):
        return self._add_comment("project", project_id, text, hours)

    def _add_comment(self, _type, _id, text, hours):
        return self.request("BumsCommonApiV01/Comment/create.api", {
            "SubjectType": _type,
            "SubjectId": self._task_id(_id),
            "Model[Text]": text,
            "Model[Work]": hours,
        })

    def _task_id(self, task_id):
        if task_id < 1000000:
            task_id += 1000000
        return task_id

__all__ = [ 'Client' ]

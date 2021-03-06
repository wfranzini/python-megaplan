Python bindings for the megaplan.ru API
=======================================

This module provides a class that implements Megaplan authentication and request
signing and lets you call API methods.

To use a password:

    import megaplan
    c = megaplan.Client('xyz.megaplan.ru')
    c.authenticate(login, password)

To use tokens:

    import megaplan
    # access_id, secret_key = c.authenticate(login, password)
    c = megaplan.Client('xyz.megaplan.ru', access_id, secret_key)

To read the token from ~/.netrc:

    import megaplan
    c = megaplan.Client('xyz.megaplan.ru')

Example ~/.netrc entry:

    machine xyz.megaplan.ru
    login NNNNNNNNNNNNNNNNNNNN
    password NNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN

To list actual tasks:

    res = c.request('BumsTaskApiV01/Task/list.api', { 'Status': 'actual' })
    for task in res['tasks']:
        print task


License
-------

Gnu GPL.


Links
-----

* http://code.umonkey.net/python-megaplan
* http://pypi.python.org/pypi/megaplan

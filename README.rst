
=============
ckanext-klimakonform
=============

.. Put a description of your extension here:
   What does it do? What features does it have?
   Consider including some screenshots or embedding a video!


------------
Requirements
------------

For example, you might want to mention here which versions of CKAN this
extension works with.


------------
Installation
------------

To install ckanext-klimakonform:

1. Activate your CKAN virtual environment, for example::

	. /usr/lib/ckan/default/bin/activate

2. Install the ckanext-klimakonform Python package into your virtual environment::

	cd /usr/lib/ckan/default/src
	git clone https://github.com/GeoinformationSystems/ckanext-klimakonform.git
	cd ckanext-klimakonform
	python setup.py develop
	pip install -r requirements.txt

3. Then create the necessary database tables for spatial search::

	. /usr/lib/ckan/default/bin/activate
	paster --plugin=ckanext-klimakonform klimakonform init -c /etc/ckan/default/ckan.ini

4. Add ``klimakonform`` to the end of ``ckan.plugins`` setting in your CKAN config file (by default the config file is located at ``/etc/ckan/default/ckan.ini``).

5. Restart CKAN. For example if you've deployed CKAN with Supervisor on Ubuntu::

	sudo service supervisor restart


----------------------
Developer installation
----------------------

To install ckanext-klimakonform for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/GeoinformationSystems/ckanext-klimakonform
    cd ckanext-klimakonform
    python setup.py develop
    pip install -r dev-requirements.txt

====================================
Apache-compatible Logging Middleware
====================================

Bark is a piece of WSGI middleware that performs logging, using log
format strings compatible with Apache.

Installing Bark
===============

Bark can be easily installed like many Python packages, using `PIP`_::

    pip install bark

You can install the dependencies required by Bark by issuing the
following command::

    pip install -r .requires

From within your Bark source directory.

If you would like to run the tests, you can install the additional
test dependencies in the same way::

    pip install -r .test-requires

Adding and Configuring Bark
===========================

Bark is intended for use with PasteDeploy-style configuration files.
It is a filter, and should be placed at the head of the WSGI pipeline,
so that the log format can access the information necessary to
generate the logs.

The filter section of the PasteDeploy configuration file will also
need to contain enough information to tell Bark how to generate the
log file(s).  The simplest example of Bark configuration would be::

    [filter:bark]
    use = egg:bark#bark
    log1.file = /var/log/bark.log
    log1.format = %h %l %u %t \"%r\" %>s %b

.. _PIP: http://www.pip-installer.org/en/latest/index.html

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
    log1.filename = /var/log/bark.log
    log1.format = %h %l %u %t "%r" %s %b

The ``use`` configuration option is interpreted by PasteDeploy.  Bark
understands a ``config`` option, which instructs Bark to additionally
read a named INI-style configuration file.  (Configuration options
appearing in the PasteDeploy configuration file will override those
options appearing in this alternate configuration file.)

All other configuration options are given dotted names in the
PasteDeploy configuration file; the first element before the '.'
corresponds to a section in the alternate configuration file, and the
remainder of the name is the full name of the option.  For instance,
expressing the configuration shown above in an alternate configuration
file would result in::

    [log1]
    filename = /var/log/bark.log
    format = %h %l %u %t "%r" %s %b

The corresponding PasteDeploy configuration would look like the
following example, assuming that the alternate configuration was
stored in "/etc/bark/bark.ini"::

    [filter:bark]
    use = egg:bark#bark
    config = /etc/bark/bark.ini

If it was desired to use this configuration file, but to override the
log file name--e.g., for a test instance of the application--all
that's needed is a PasteDeploy configuration as follows::

    [filter:bark]
    use = egg:bark#bark
    config = /etc/bark/bark.ini
    log1.filename = /var/log/bark-test.log

Structure of the Configuration File
-----------------------------------

Each section in Bark's configuration describes a single log stream
(with the exception of the ``[proxies]`` section; see below).  Each
section must have a ``format`` configuration option, which must have
an Apache-compatible format string.  Each section also has a ``type``
option, which expresses the type of the log stream; this defaults to
the "file" log stream type.  Any other options in this section are
passed to a handler factory for the log stream type; most handlers
have other mandatory arguments, such as the ``filename`` option for
the "file" log stream type.

When the Bark middleware processes a request, each of the configured
log streams will be sent a message formatted according to the
configured format string.  (Note that there is no guarantee of
ordering of these log messages; the ordering could, in principle, be
different for each request.)  The Bark middleware should be the first
filter in the processing pipeline, particularly if the "%D" or "%T"
conversions are used in the format string.  (These conversions format
the total time taken for the request to be processed by the
application.)

Available Handlers
------------------

Bark ships with 13 defined log stream types, documented below along
with the configuration options recognized or required by each.  Note
that most of these log stream types actually derive from handlers
defined by the Python standard ``logging`` library.

``null``
~~~~~~~~

The ``null`` log stream type has no recognized configuration options.
Log messages for this log stream type are discarded without being
recorded anywhere.  This could be used to temporarily disable a log
stream.  (As with all log stream types, unrecognized configuration
options only generate a warning, logged via the Python standard
logging library.)

``stdout``
~~~~~~~~~~

The ``stdout`` log stream type has no recognized configuration
options, and log messages are simply emitted to the program's standard
output stream.

``stderr``
~~~~~~~~~~

The ``stderr`` log stream type, similar to the ``stdout`` log stream
type, has no recognized configuration options, and log messages are
simply emitted to the program's standard error stream.

``file``
~~~~~~~~

The ``file`` log stream type is used for logging messages to a
specified file.  It has the following recognized configuration
options:

``filename``
    Required.  The name of the file to which log messages should be
    emitted.

``mode``
    Optional.  A string representing the opening mode for the file
    stream.  Defaults to "a".

``encoding``
    Optional.  The name of the character encoding to use when writing
    messages to the file stream.

``delay``
    Optional.  A boolean value indicating when the file stream should
    be opened.  If "false" (the default), the file stream will be
    opened immediately, whereas if "true", the file stream will not be
    opened until the first log message is emitted.

``watched_file``
~~~~~~~~~~~~~~~~

The ``watched_file`` log stream type is identical to the ``file`` log
stream type, including the recognized configuration options.  It adds
the behavior of closing and reopening the file if the file has changed
since the last log message was written.  This may be used to support
external log file rotation systems, such as logrotate.

``filename``
    Required.  The name of the file to which log messages should be
    emitted.

``mode``
    Optional.  A string representing the opening mode for the file
    stream.  Defaults to "a".

``encoding``
    Optional.  The name of the character encoding to use when writing
    messages to the file stream.

``delay``
    Optional.  A boolean value indicating when the file stream should
    be opened.  If "false" (the default), the file stream will be
    opened immediately, whereas if "true", the file stream will not be
    opened until the first log message is emitted.

``rotating_file``
~~~~~~~~~~~~~~~~~

The ``rotating_file`` log stream type is similar to the ``file`` log
stream type, in that log messages are emitted to a file.  However,
``rotating_file`` log streams watch the size of the file, and rotate
the file (under control of the ``backupCount`` configuration option)
when the file approaches a configured maximum size.

``filename``
    Required.  The name of the file to which log messages should be
    emitted.

``mode``
    Optional.  A string representing the opening mode for the file
    stream.  Defaults to "a".

``maxBytes``
    The maximum size the file should be allowed to grow to.

``backupCount``
    The maximum number of previous versions of the log file to
    maintain in the rotation process.  Log files beyond
    ``backupCount`` are deleted.

``encoding``
    Optional.  The name of the character encoding to use when writing
    messages to the file stream.

``delay``
    Optional.  A boolean value indicating when the file stream should
    be opened.  If "false" (the default), the file stream will be
    opened immediately, whereas if "true", the file stream will not be
    opened until the first log message is emitted.

``timed_rotating_file``
~~~~~~~~~~~~~~~~~~~~~~~

The ``timed_rotating_file`` log stream type is similar to the ``file``
log stream type--in that log messages are emitted to a file--and to
the ``rotating_file`` log stream type--in that log files are rotated.
However, the rotation occurs at a defined time interval, rather than
according to a maximum size for the file.  For a full explanation of
how this log stream type is configured, see the Python documentation
for `TimedRotatingFileHandler`_.

``filename``
    Required.  The name of the file to which log messages should be
    emitted.

``when``
    A string indicating how to interpret the ``interval``
    configuration value.  See the documentation for
    `TimedRotatingFileHandler`_ for a full discussion of the possible
    values of this configuration option.  Defaults to "h".

``interval``
    The length of the interval, as modified by ``when``.  For
    instance, if this value is "3" and ``when`` is set to "h", then
    the file will be rotated every 3 hours.

``backupCount``
    The maximum number of previous versions of the log file to
    maintain in the rotation process.  Log files beyond
    ``backupCount`` are deleted.

``encoding``
    Optional.  The name of the character encoding to use when writing
    messages to the file stream.

``delay``
    Optional.  A boolean value indicating when the file stream should
    be opened.  If "false" (the default), the file stream will be
    opened immediately, whereas if "true", the file stream will not be
    opened until the first log message is emitted.

``utc``
    Optional.  A boolean value indicating whether to use UTC-based
    times for time interval determination.  If "false" (the default),
    the local time will be used, whereas if "true", UTC will be used.

``socket``
~~~~~~~~~~

The ``socket`` log stream type causes a log message to be submitted
via a TCP socket to a server listening on a configured host and port.
The log message will be sent as a pickled dictionary, derived from a
``logging.LogRecord`` instance.  This is compatible with the standard
`SocketHandler`_.

``host``
    Required.  The host to which to submit the log message.

``port``
    Required.  The TCP port number on the host to which to submit the
    log message.

``datagram``
~~~~~~~~~~~~

The ``datagram`` log stream type causes a log message to be submitted
via a UDP datagram to a server listening on a configured host and
port.  The log message will be sent as a pickled dictionary, derived
from a ``logging.LogRecord`` instance.  This is compatible with the
standard `DatagramHandler`_.

``host``
    Required.  The host to which to submit the log message.

``port``
    Required.  The UDP port number on the host to which to submit the
    log message.

``syslog``
~~~~~~~~~~

The ``syslog`` log stream type causes a log message to be submitted to
a SysLog server, listening on a specified address.

``address``
    Optional.  The address of the SysLog server.  For local servers
    listening on a UNIX datagram socket, this may be a path name for
    that socket.  For servers listening on a UDP port, this must be
    the host name and port number of the server, separated by a colon.
    If not given, defaults to "localhost:514".

``facility``
    Optional.  The name of a SysLog facility, such as "user",
    "local0", etc.  Defaults to "user".

``nt_event_log``
~~~~~~~~~~~~~~~~

The ``nt_event_log`` log stream type causes a log message to be
submitted to the NT event log.  See the documentation for the
`NTEventLogHandler`_ for more information.

``appname``
    Required.  The application name to log under.

``dllname``
    Optional.  Should give the fully qualified pathname of a .dll or
    .exe which contains message definitions to hold in the log.
    Defaults to ``win32service.pyd``.

``logtype``
    Optional.  One of "Application", "System", or "Security".
    Defaults to "Application".

``smtp``
~~~~~~~~

The ``smtp`` log stream type causes a log message to be emitted via an
email to a specified destination address or list of addresses.
Compatible with `SMTPHandler`_.

``mailhost``
    Required.  The hostname for the mail server.  If a non-standard
    SMTP port is used, separate it from the hostname with a colon.

``fromaddr``
    Required.  The email address the email should appear to come from.

``toaddrs``
    Required.  A comma-separated list of email addresses to which the
    mail should be sent.

``subject``
    Required.  The text to include in the "Subject" header of the
    email message.

``credentials``
    Optional.  A username and password (separated by a colon) to use
    to authenticate with the SMTP server.  If not provided, no
    authentication exchange is performed.

``http``
~~~~~~~~

The ``http`` log stream type causes a log message to be emitted via a
GET or POST request to web server.  Compatible with `HTTPHandler`_.

``host``
    Required.  The hostname of the web server.  If a non-standard port
    number must be specified, separate it from the hostname with a
    colon.

``url``
    Required.  The URL to which to submit the log message.

``method``
    Optional.  The HTTP method to use to submit the log message.  May
    be either "GET" or "POST".  Defaults to "GET".

.. _PIP: http://www.pip-installer.org/en/latest/index.html
.. _TimedRotatingFileHandler: http://docs.python.org/2/library/logging.handlers.html#timedrotatingfilehandler
.. _SocketHandler: http://docs.python.org/2/library/logging.handlers.html#sockethandler
.. _DatagramHandler: http://docs.python.org/2/library/logging.handlers.html#datagramhandler
.. _NTEventLogHandler: http://docs.python.org/2/library/logging.handlers.html#nteventloghandler
.. _SMTPHandler: http://docs.python.org/2/library/logging.handlers.html#smtphandler
.. _HTTPHandler: http://docs.python.org/2/library/logging.handlers.html#httphandler

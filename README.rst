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

Proxy Configuration
-------------------

The "%a" format string conversion specification allows for Bark to log
the IP address of a client connection.  However, what happens if the
connection is redirected through a proxy?  Proxies usually embed
information about the original client connection in a request header,
such as the "X-Forwarded-For" header, so the information is available.
However, to prevent a user from spoofing the originating IP address,
this header must be validated.

Bark includes a proxy validation system, which can be configured
through the special ``[proxies]`` section of the configuration.  This
section contains one required configuration setting, namely,
``header``; this configuration tells Bark which header to use (e.g.,
"X-Forwarded-For").

If ``header`` is the only configuration value set, then that header
will be trusted for all connections, which is obviously a security
problem.  To combat this, the list of trusted proxy IP addresses may
be specified through the ``proxies`` configuration value, which must
be a comma-separated list of IP addresses (note: not hostnames!).

Each proxy may be further restricted as to the IP addresses of the
clients it may introduce.  To do this, use the IP address of the proxy
as a configuration key; the value must be a comma-separated list of IP
addresses or CIDR expressions which that proxy is permitted to
introduce clients from.

For more advanced users, there are some advanced ways of expressing
proxies and permitted client addresses.  By default, no proxy may
introduce a client from an internal address (e.g., 10.0.5.23), but is
allowed to introduce a client from any public address; this may be
modified by using the "internal()" modifier, which allows internal
addresses, or the "restrict()" modifier, which requires that an IP
address be specifically permitted to a proxy to allow it to introduce
a client from that address.  For instance, consider the following
configuration::

    [proxies]
    header = x-forwarded-for
    proxies = 10.5.21.1

In this configuration, the proxy 10.5.21.1 may introduce a client
from, say, 207.97.209.147; however, a client from 10.3.15.127 may not
be introduced.  If we wish to allow this proxy to introduce
10.3.15.127, we would need the following configuration::

    [proxies]
    header = x-forwarded-for
    proxies = internal(10.5.21.1)

If, on the other hand, the proxy 10.5.21.1 should only be able to
introduce clients from 10.3.15.0/24, and not be permitted to introduce
a client from 207.97.209.147, this is the configuration we would
need::

    [proxies]
    header = x-forwarded-for
    proxies = restrict(10.5.21.1)
    10.5.21.1 = 10.3.15.0/24

Note that one cannot simply add an internal IP range to a
non-restricted proxy entry.  That is, this configuration would **not**
allow clients from 10.3.15.0/24 to be introduced via 10.5.21.1::

    [proxies]
    header = x-forwarded-for
    proxies = 10.5.21.1
    10.5.21.1 = 10.3.15.0/24

There is one more important point in the configuration of proxies.  It
is possible to prohibit proxies from introducing certain IP addresses,
by using the "restrict()" modifier on the CIDR list.  (The converse,
"accept()", exists, but is no different from listing a bare address.)
For instance, we can use "internal(10.5.21.1)" to allow the
introduction of clients from local addresses, but prohibit clients
from being introduced from some of those ranges.  For instance, let's
allow 10.5.21.1 to introduce internal clients, but prohibit
introduction of clients from the ranges 10.5.0.0/16 and 10.3.15.0/24::

    [proxies]
    header = x-forwarded-for
    proxies = internal(10.5.21.1)
    10.5.21.1 = restrict(10.5.0.0/16), restrict(10.3.15.0/24)

Modifications to the request environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If Bark's proxy system is enabled, and a client is introduced from a
proxy, the ``REMOTE_ADDR`` key in the WSGI environment is *not*
altered; rather, the verified client's IP address will be present in
the WSGI environment key ``bark.useragent_ip``.  Additionally, a
comma-separated list of the verified proxies will be present in a
dictionary stored in the WSGI environment key ``bark.notes``; the
dictionary key containing this list of proxy IP addresses is
``remoteip-proxy-ip-list``.  (The ``bark.notes`` dictionary is
provided for the "%n" format string conversion, and is provided for
compatibility with Apache's method of presenting this information.  To
include this data in a log message, one would use
"%{remoteip-proxy-ip-list}n" in the format string.)  The proxy
verification system *does* alter the proxy header, however; the header
may be removed if all IP addresses listed are valid proxies, otherwise
it will contain a comma-separated list of those IP addresses which
could not be validated as proxies.

Log Format Strings
==================

All log streams must have a ``format`` configuration value, as
described above.  This format string is compatible with the `Apache
log module`_, with some minor differences.  For instance, the "%l",
"%L", "%R", and "%X" conversions always format as a "-", since those
values are generally not available in WSGI; additionally, the "%k"
conversion always formats as a "0", since again keep-alive information
is generally not available in WSGI.  Bark also adds the "%w"
conversion, which allows formatting of any WSGI environment variable.
As an example, the conversion "%{wsgi.version}w" would format as "(1,
0)".  Finally, note that all the modifiers permitted for Apache
conversions are recognized by Bark; however, the modifiers "<" and ">"
have no meaning.

Extending Bark
==============

Bark uses the ``pkg_resources`` package (part of setuptools) to look
up conversions and log stream types.  This allows for easily extending
Bark to allow for new conversions or log stream types.

Adding New Conversions
----------------------

To add a new conversion, subclass the ``bark.conversions.Conversion``
abstract class.  The subclass must define a ``convert()`` method,
taking as arguments a ``webob.Request`` object, a ``webob.Response``
object, and arbitrary data (more on this argument in a moment).  The
return value of the ``convert()`` method must be the string to
substitute for the conversion.

Some conversions need to initialize data before the request is
processed; examples are "%D" and "%T", which time the processing of a
request, and "%t", which formats the start time of a request.  For
extension conversions that require such preparation, override the
``prepare()`` method.  This method takes a single argument--a
``webob.Request`` object--and return a dictionary containing arbitrary
data.  This return value will be presented to the ``convert()`` method
as its third argument.  (The default implementation of ``prepare()``
simply returns an empty dictionary.)

The conversion must then be listed as a member of the
``bark.conversion`` entry point group.  Of course, single characters
may be used, as for the standard conversions; however, it is
encouraged to use descriptive names for extension conversions.  An
extension to Bark's parsing of format strings allows for
multicharacter conversion names to be specified by enclosing them in
parentheses.  As an example, consider defining an entry point for
Bark's existing ``TimeConversion`` class, under the multicharacter
name "time"; the entry point would be defined as follows::

    'bark.conversion': [
        'time = bark.conversions:TimeConversion',
    ]

To specify that this time conversion be used with an ISO-8601
compliant time format, the format conversion would be:
"%{%Y-%m-%dT%H:%M:%SZ}(time)".

Adding New Log Stream Types
---------------------------

To add a new log stream type, create a factory for configuring the log
stream type.  This factory could be a function which returns a
callable of one argument, or it could be a class with ``__init__()``
conforming to the factory function interface and ``__call__()`` taking
a single argument; in either case, what matters is that the return
value of calling the factory must be a callable of one argument.  This
callable will be passed a string--the formatted message--and must emit
the string to the appropriate log message handler.

All of these log stream type factories are passed a minimum of two
arguments: the name of the log stream type (e.g., "null", "file",
etc.) and the name of the configuration file section in which it is
used.  (All the predefined log stream types ignore this argument, but
extension stream types are welcome to make use of it.)  All remaining
arguments will be drawn from the configuration, and arguments which
have no defined default will be required configuration options.

When a log stream type factory is called, all the arguments will be
passed as simple string values, straight from the configuration.
However, it is possible to designate certain arguments as being
certain types, in which case those arguments will be converted before
calling the factory.  For instance, consider the socket factory, which
is defined as follows::

    @arg_types(port=int)
    def socket_handler(name, logname, host, port):
        return wrap_log_handler(logging.handlers.SocketHandler(host, port))

The decorator ``@bark.handlers.arg_types()`` takes keyword arguments,
mapping argument names to callables which can convert a string into
the expected value.  If this callable raises a ``ValueError``, as the
``int`` callable may, that error will be logged and that log stream
will be skipped.  This can also be used to validate argument values,
such as with the special ``bark.handlers.choice()`` class, which
demands that the string be one of the ones specified; if it does not
match, ``choice()`` raises a ``ValueError``.

Finally, note the ``bark.handlers.wrap_log_handler()`` function; this
function takes an instance of a ``logging.Handler`` class and returns
a callable which uses that class to emit a log message via that
handler.  All of the standard log stream types, with the exception of
the ``null`` log stream type, use standard ``logging.Handler``
instances to perform the actual logging.

Once a log stream type factory has been created, it then must be
listed as a member of the ``bark.handler`` entry point group.  The
name will then be recognized as a valid log stream type.

.. _PIP: http://www.pip-installer.org/en/latest/index.html
.. _TimedRotatingFileHandler: http://docs.python.org/2/library/logging.handlers.html#timedrotatingfilehandler
.. _SocketHandler: http://docs.python.org/2/library/logging.handlers.html#sockethandler
.. _DatagramHandler: http://docs.python.org/2/library/logging.handlers.html#datagramhandler
.. _NTEventLogHandler: http://docs.python.org/2/library/logging.handlers.html#nteventloghandler
.. _SMTPHandler: http://docs.python.org/2/library/logging.handlers.html#smtphandler
.. _HTTPHandler: http://docs.python.org/2/library/logging.handlers.html#httphandler
.. _Apache log module: http://httpd.apache.org/docs/2.4/mod/mod_log_config.html#formats

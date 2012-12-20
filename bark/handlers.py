# Copyright 2012 Rackspace
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import functools
import inspect
import logging
import logging.handlers
import sys

import pkg_resources

from bark import middleware


LOG = logging.getLogger('bark')


class SimpleFormatter(logging.Formatter):
    def format(self, record):
        """
        Return the log message, unchanged, since it has already been
        formatted.
        """

        return record.msg


def wrap_log_handler(handler):
    """
    Helper function which takes a Python logging handler and wraps it.
    Returns a callable taking a single argument, which will be wrapped
    in a log record and passed to the handler's emit() method.

    :param handler: A logging.Handler instance.

    :returns: A callable of one argument, which will emit that
              argument to the appropriate logging destination.
    """

    # Set the formatter on the handler to be the SimpleFormatter
    handler.setFormatter(SimpleFormatter())

    # Get file name, line number, and function name for
    # middleware.BarkMiddleware.__call__
    obj = middleware.BarkMiddleware.__call__
    filename = inspect.getsourcefile(obj)
    lineno = inspect.getsourcelines(obj)[1]
    funcname = '__call__'

    @functools.wraps(handler.emit)
    def wrapper(msg):
        # First, generate a LogRecord
        record = logging.LogRecord('bark', logging.INFO, filename, lineno,
                                   msg, (), None, funcname)

        # Now, pass it to the handler's emit method
        handler.emit(record)

    return wrapper


def arg_types(**kwargs):
    """
    Mark the expected types of certain arguments.  Arguments for which
    no types are provided default to strings.  To specify an argument
    type, give this decorator a keyword argument, where the argument
    name is the name of the function argument and the value is a
    callable taking one argument, which will convert a string to a
    value of that type.

    Note that the 'bool' type is treated specially.
    """

    def decorator(func):
        if not hasattr(func, '_bark_types'):
            func._bark_types = {}
        func._bark_types.update(kwargs)
        return func

    return decorator


def null_handler(name, logname):
    """
    A Bark logging handler that discards log messages.

    Similar to logging.NullHandler.
    """

    def null(msg):
        pass

    return null


def stdout_handler(name, logname):
    """
    A Bark logging handler logging output to sys.stdout.

    Similar to logging.StreamHandler with a stream of sys.stdout.
    """

    return wrap_log_handler(logging.StreamHandler(sys.stdout))


def stderr_handler(name, logname):
    """
    A Bark logging handler logging output to sys.stderr.

    Similar to logging.StreamHandler with a stream of sys.stderr.
    """

    return wrap_log_handler(logging.StreamHandler(sys.stderr))


@arg_types(delay=bool)
def file_handler(name, logname, filename, mode='a', encoding=None,
                 delay=False):
    """
    A Bark logging handler logging output to a named file.

    Similar to logging.FileHandler.
    """

    return wrap_log_handler(logging.FileHandler(
        filename, mode=mode, encoding=encoding, delay=delay))


@arg_types(delay=bool)
def watched_file_handler(name, logname, filename, mode='a', encoding=None,
                         delay=False):
    """
    A Bark logging handler logging output to a named file.  If the
    file has changed since the last log message was written, it will
    be closed and reopened.

    Similar to logging.handlers.WatchedFileHandler.
    """

    return wrap_log_handler(logging.handlers.WatchedFileHandler(
        filename, mode=mode, encoding=encoding, delay=delay))


@arg_types(maxBytes=int, backupCount=int, delay=bool)
def rotating_file_handler(name, logname, filename, mode='a', maxBytes=0,
                          backupCount=0, encoding=None, delay=False):
    """
    A Bark logging handler logging output to a named file.  When the
    file grows close to 'maxBytes', it will be rotated, under control
    of 'backupCount'.

    Similar to logging.handlers.RotatingFileHandler.
    """

    return wrap_log_handler(logging.handlers.RotatingFileHandler(
        filename, mode=mode, maxBytes=maxBytes, backupCount=backupCount,
        encoding=encoding, delay=delay))


@arg_types(interval=int, backupCount=int, delay=bool, utc=bool)
def timed_rotating_file_handler(name, logname, filename, when='h',
                                interval=1, backupCount=0,
                                encoding=None, delay=False, utc=False):
    """
    A Bark logging handler logging output to a named file.  At
    intervals specified by the 'when', the file will be rotated, under
    control of 'backupCount'.

    Similar to logging.handlers.TimedRotatingFileHandler.
    """

    return wrap_log_handler(logging.handlers.TimedRotatingFileHandler(
        filename, when=when, interval=interval, backupCount=backupCount,
        encoding=encoding, delay=delay, utc=utc))


@arg_types(port=int)
def socket_handler(name, logname, host, port):
    """
    A Bark logging handler logging output to a stream (TCP) socket.
    The server listening at the given 'host' and 'port' will be sent a
    pickled dictionary.

    Similar to logging.handlers.SocketHandler.
    """

    return wrap_log_handler(logging.handlers.SocketHandler(host, port))


@arg_types(port=int)
def datagram_handler(name, logname, host, port):
    """
    A Bark logging handler logging output to a datagram (UDP) socket.
    The server listening at the given 'host' and 'port' will be sent a
    pickled dictionary.

    Similar to logging.handlers.DatagramHandler.
    """

    return wrap_log_handler(logging.handlers.DatagramHandler(host, port))


def syslog_handler(name, logname, address='localhost:514',
                   facility='user'):
    """
    A Bark logging handler logging output to syslog.  By default,
    sends log messages to localhost on port 514; if this logger
    doesn't seem to work, confirm that the address is correct.
    Addresses containing a colon (':') are treated as a hostname and
    port, while others are interpreted as UNIX domain sockets.

    Similar to logging.handlers.SysLogHandler.
    """

    # Translate the address, if needed
    if ':' in address:
        # Using rpartition here means we should be able to support
        # IPv6, but only with a strict syntax
        addr, _sep, port = address.rpartition(':')

        # Convert the port to a number
        try:
            port = int(port)
        except ValueError:
            # Translate for proper logging
            raise ValueError("Invalid port number %r" % port)

        address = (addr, port)

    # Now, let's translate the facility
    if facility not in logging.handlers.SysLogHandler.facility_names:
        raise ValueError("Unrecognized syslog facility %r" % facility)
    facility = logging.handlers.SysLogHandler.facility_names[facility]

    return wrap_log_handler(logging.handlers.SysLogHandler(
        address=address, facility=facility))


def nt_event_log_handler(name, logname, appname, dllname=None,
                         logtype="Application"):
    """
    A Bark logging handler logging output to the NT Event Log.

    Similar to logging.handlers.NTEventLogHandler.
    """

    # Sanity-check logtype
    if logtype not in ('Application', 'System', 'Security'):
        raise ValueError("Unrecognized logtype value %r" % logtype)

    return wrap_log_handler(logging.handlers.NTEventLogHandler(
        appname, dllname=dllname, logtype=logtype))


def smtp_handler(name, logname, mailhost, fromaddr, toaddrs, subject,
                 credentials=None):
    """
    A Bark logging handler logging output via SMTP.  To specify a
    non-standard SMTP port, use the "host:port" format.  To specify
    multiple "To" addresses, separate them with commas.  To specify
    authentication credentials, supply a "username:password".

    Similar to logging.handlers.SMTPHandler.
    """

    # Set up the mailhost
    if ':' in mailhost:
        # Using rpartition here means we should be able to support
        # IPv6, but only with a strict syntax
        addr, _sep, port = mailhost.rpartition(':')

        # Convert the port to a number
        try:
            port = int(port)
        except ValueError:
            # Translate for proper logging
            raise ValueError("Invalid port number %r" % port)

        mailhost = (addr, port)

    # Set up toaddrs as a list
    toaddrs = [addr.strip() for addr in toaddrs.split(',')]

    # Split up credentials
    if credentials:
        username, _sep, password = credentials.partition(':')
        credentials = (username, password)

    return wrap_log_handler(logging.handlers.SMTPHandler(
        mailhost, fromaddr, toaddrs, subject, credentials=credentials))


def http_handler(name, logname, host, url, method="GET"):
    """
    A Bark logging handler logging output to an HTTP server, using
    either GET or POST semantics.

    Similar to logging.handlers.HTTPHandler.
    """

    return wrap_log_handler(logging.handlers.HTTPHandler(
        host, url, method=method))


def get_handler(name, logname, args):
    """
    Retrieve a logger given its name and initialize it by passing it
    appropriate arguments from the configuration.  (Unnecessary
    arguments will be logged, and missing required arguments will
    cause a TypeError to be thrown.)  The result should be a callable.

    :param name: The name of the handler to look up.
    :param logname: The name of the log section.
    :param args: A dictionary of arguments for the handler.

    :returns: A callable taking a single argument: the message to be
              logged.
    """

    # Look up and load the handler factory
    for ep in pkg_resources.iter_entry_points('bark.handler', name):
        try:
            # Load the handler factory
            factory = ep.load()
            break
        except (ImportError, pkg_resources.UnknownExtra):
            # Couldn't load it...
            continue
    else:
        raise ImportError("Unknown log file handler %r" % name)

    # What arguments are we passing to the handler?
    available = set(args.keys())

    # Now, let's introspect the factory to pass it the right arguments
    if inspect.isclass(factory):
        argspec = inspect.getargspec(factory.__init__)
        ismethod = True
    else:
        argspec = inspect.getargspec(factory)
        ismethod = inspect.ismethod(factory)

    # Now, let's select the arguments we'll be passing in from the
    # args dictionary
    argnames = argspec.args[2 + ismethod:]
    recognized = set(argnames)

    # Now, which ones are required?
    required = set(argnames[:len(argnames) - len(argspec.defaults)])
    missing = required - available
    if missing:
        raise TypeError("Missing required parameters: %s" %
                        ', '.join(repr(arg) for arg in sorted(missing)))

    # OK, let's determine the argument types
    type_map = getattr(factory, '_bark_types', {})

    # Now go convert the arguments
    kwargs = {}
    additional = set()
    for arg, value in args.items():
        # Should we ignore it?
        if not argspec.keywords and arg not in recognized:
            additional.add(arg)
            continue

        # Translate the value, first
        target_type = type_map.get(arg, lambda x: x)
        if target_type is bool:
            test = value.lower()
            if test.isdigit():
                value = bool(int(test))
            elif test in ('t', 'true', 'on', 'yes'):
                value = True
            elif test in ('f', 'false', 'off', 'no'):
                value = False
            else:
                raise ValueError("Argument %r: invalid Boolean value %r" %
                                 (arg, value))
        else:
            try:
                value = target_type(value)
            except ValueError as exc:
                raise ValueError("Argument %r: invalid %s value %r" %
                                 (arg, target_type.__name__, value))

        # OK, save it
        kwargs[arg] = value

    # Log any unused arguments
    if additional:
        LOG.warn("Unused arguments for handler of type %r for log %r: %s" %
                 (name, logname, ', '.join(repr(arg)
                                           for arg in sorted(additional))))

    # OK, we have now constructed the arguments to feed to the handler
    # factory; call it and return the result
    return factory(name, logname, **kwargs)

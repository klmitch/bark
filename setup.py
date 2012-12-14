#!/usr/bin/env python

import os

from setuptools import setup


def readreq(filename):
    result = []
    with open(filename) as f:
        for req in f:
            req = req.partition('#')[0].strip()
            if not req:
                continue
            result.append(req)
    return result


def readfile(fname):
    with open(filename) as f:
        return f.read()


setup(
    name='bark',
    version='0.1.0',
    author='Kevin L. Mitchell',
    author_email='kevin.mitchell@rackspace.com',
    url='https://github.com/klmitch/bark',
    description="WSGI logging middleware",
    long_description=readfile('README.rst'),
    license='Apache License (2.0)',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Environment :: Web Environment',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Framework :: Paste',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
    ],
    packages=['bark'],
    install_requires=readreq('.requires'),
    tests_require=readreq('.test-requires'),
    entry_points={
        'paste.filter_factory': [
            'bark = bark.middleware:bark_filter',
        ],
        'bark.conversion': [
            'a = bark.conversions:AddressConversion',
            'A = bark.conversions:LocalAddressConversion',
            'b = bark.conversions:ResponseSizeConversion',
            'B = bark.conversions:ResponseSizeConversion',
            'C = bark.conversions:CookieConversion',
            'D = bark.conversions:ServeTimeConversion',
            'e = bark.conversions:EnvironmentConversion',
            'f = bark.conversions:FilenameConversion',
            'h = bark.conversions:HostnameConversion',
            'H = bark.conversions:ProtocolConversion',
            'i = bark.conversions:RequestHeaderConversion',
            'k = bark.conversions:KeepAliveConversion',
            'l = bark.conversions:UnavailableConversion',
            'L = bark.conversions:UnavailableConversion',
            'm = bark.conversions:RequestMethodConversion',
            'n = bark.conversions:UnavailableConversion',
            'o = bark.conversions:ResponseHeaderConversion',
            'p = bark.conversions:ServerPortConversion',
            'P = bark.conversions:ProcessIDConversion',
            'q = bark.conversions:QueryStringConversion',
            'r = bark.conversions:FirstLineConversion',
            'R = bark.conversions:UnavailableConversion',
            's = bark.conversions:StatusConversion',
            't = bark.conversions:TimeConversion',
            'T = bark.conversions:ServeTimeConversion',
            'u = bark.conversions:RemoteUserConversion',
            'U = bark.conversions:URLConversion',
            'v = bark.conversions:ServerNameConversion',
            'V = bark.conversions:ServerNameConversion',
            'X = bark.conversions:UnavailableConversion',
            'w = bark.conversions:WSGIEnvironmentConversion',
        ],
    },
)

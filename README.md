# Swift Informant - [![Build Status](https://secure.travis-ci.org/pandemicsyn/swift-informant.png?branch=master)](http://travis-ci.org/pandemicsyn/swift-informant)

Swift Proxy Middleware to send events to a [statsd](http://github.com/etsy/statsd/ "statsd") instance.

**After** the request has been serviced (using a event posthook) it will fire a statsd counter incrementing the request method's status code.  It breaks these up by whether the request was an operation on an Account, Container, or an Object. In addition to the counter a timer event is fired for the request duration of the event, as well as counter for bytes transferred.

Counter Sample:

    obj.GET.200:1|c

Timer Sample:

    duration.acct.GET.200:140|ms

Bytes Transferred Sample:

    tfer.obj.PUT.201 2423.9

To enable, load informant as the first pipeline entry (even before catcherrors):

    pipeline = informant catch_errors healthcheck cache ratelimit proxy-server

And add the following filter config:

    [filter:informant]
    use = egg:informant#informant
    # statsd_host = 127.0.0.1
    # statsd_port = 8125
    # standard statsd sample rate 0.0 <= 1
    # statsd_sample_rate = 0.5
    # list of allowed methods, all others will generate a "BAD_METHOD" event
    # valid_http_methods = GET,HEAD,POST,PUT,DELETE,COPY
    # send multiple statsd events per packet as supported by statsdpy
    # combined_events = no
    # prepends name to metric collection output for easier recognition, e.g. company.swift.
    # metric_name_prepend = 

The commented out values are the defaults. This module does not require any additional statsd client modules. 
**To utilize combined_events you'll need to run a statsd server that supports mulitple events per packet such as [statsdpy](https://github.com/pandemicsyn/statsdpyd)**

# Building packages

Clone the version you want and build the package with [stdeb](https://github.com/astraw/stdeb "stdeb"):
    
    git clone git@github.com:pandemicsyn/swift-informant.git informant-0.0.5
    cd informant-0.0.5
    git checkout 0.0.5
    python setup.py --command-packages=stdeb.command bdist_deb
    dpkg -i deb_dist/python-informant_0.0.5-1_all.deb

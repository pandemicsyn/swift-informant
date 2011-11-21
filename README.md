# swift-informant

Swift Proxy Middleware to send events to a [statsd](http://github.com/etsy/statsd/ "statsd") instance.

After the request has been serviced it will fire a statsd counter incrementing the request method and the status code.  It breaks these up by whether the request was an operation on an Account, Container, or an Object.

Sample:

    obj.GET:1|c
    obj.200:1|c
    cont.DELETE:1|c
    cont.204:1|c
    acct.DELETE:1|c
    acct.DELETE:1|c

To enable load informant as the first pipeline entry (even before catcherrors):

    pipeline = informant catch_errors healthcheck cache ratelimit proxy-server

And add the following filter config:

    [filter:informant]
    use = egg:swift-informant#informant
    # statsd_host = 127.0.0.1
    # statsd_port = 8125
    # standard statsd sample rate 0.0 <= 1
    # statsd_sample_rate = 0.5

The commented out values are the defaults.

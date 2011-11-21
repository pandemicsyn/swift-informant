# simple test
from eventlet.green import socket

counter = 0

def main():
    global counter
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    addr = ('127.0.0.1', 8125)
    sock.bind(addr)
    buf = 512
    print "Listening on %s:%d" % addr
    while 1:
        data, addr = sock.recvfrom(buf)
        if not data:
            break
        else:
            print "recv: %s" % data
            counter += 1

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print "\nReceived %d events" % counter
        print '\n'

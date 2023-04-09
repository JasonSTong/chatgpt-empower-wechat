import socket


def is_port_open(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(1)
        result = s.connect_ex((ip, port))
        s.close()
        if result == 0:
            return True
        return False
    except Exception as e:
        print(e)
        return False
    finally:
        s.close()

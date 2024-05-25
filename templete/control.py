import os


def temp01():
    cmd = "dracal-usb-get -i 0 -s E23182"
    p = os.popen(cmd)
    c = p.read().strip()
    p.close()
    try:
        return True, float(c)
    except:
        return False, 0


def temp02():
    cmd = "dracal-usb-get -i 0 -s E23182"
    p = os.popen(cmd)
    c = p.read().strip()
    p.close()
    try:
        return True, float(c)
    except:
        return False, 0


from bluepy.btle import Scanner, DefaultDelegate, BTLEManagementError
from collector.lib import redis_helper
import hashlib
import json

LOCK_NAME = 'btle-lock'
r = redis_helper.redis_connection(decode=True)


def set_lock(timeout):
    if r.get(LOCK_NAME):
        return False
    else:
        r.set(LOCK_NAME, 1)
        r.expire(LOCK_NAME, timeout)
        return True


def delete_lock():
    r.delete(LOCK_NAME)


def log_btle_error():
    btle_error_key = 'btle-error'
    btle_error_key_ttl = 3600

    if r.get(btle_error_key):
        r.incr(btle_error_key)
        r.expire(btle_error_key, btle_error_key_ttl)
    else:
        r.set(btle_error_key, 1)
        r.expire(btle_error_key, btle_error_key_ttl)


def lookup_bluetooth_manufacturer(manufacturer):
    """
    We need to do a fair bit of juggling here, but the goal is to
    return the manufacturer based on the data we captured.

    We need to swap around the result [1] and then convert it to
    decimal in order to look it up from the Nordic database.

    [1] https://stackoverflow.com/questions/23626871/list-of-company-ids-for-manufacturer-specific-data-in-ble-advertising-packets#comment36359241_23626871
    """

    shuffled_manufacturer = '0x{}{}'.format(manufacturer[2:4], manufacturer[0:2])
    manufacturer_in_decimal = int(shuffled_manufacturer, 16)
    redis_key = 'manufacturer-{}'.format(manufacturer_in_decimal)
    lookup_result = 'Unknown'
    redis_lookup = r.get(redis_key)

    if not redis_lookup:
        with open('company_ids.json', 'r') as company_ids:
            company_database = json.loads(company_ids.read())

        for company in company_database:
            r.set('manufacturer-{}'.format(company['code']), company['name'])
            if company['code'] == manufacturer_in_decimal:
                lookup_result = company['name']
        return lookup_result
    else:
        return redis_lookup


def build_device_fingerprint(device):
    """
    Because BLE devices (type: random), re-generates the MAC address,
    we won't be able to track returning visitors. We need to attempt
    to build a footprint instead based on metadata from the GAP payload [1].

    Some additional insperation can also be found here [2].


    [1] https://www.bluetooth.com/specifications/assigned-numbers/generic-access-profile/
    [2] https://hal.inria.fr/hal-02359914/document
    """

    fingerprint = ''

    # Start by the first two octets of the manufacturer
    if device.getValue(255):
        fingerprint += device.getValueText(255)[0:4]

    # If the device type is public, we know it should be static,
    # so no need to go on. If however it is 'random', we need to
    # feed other random metadata to try to establish a fingerprint.
    if device.addrType == 'public':
        fingerprint += device.addr
    else:
        # Flags
        if device.getValue(1):
            fingerprint += device.getValueText(1)

        # TX Power
        if device.getValue(10):
            fingerprint += device.getValueText(10)

        # Incomplete 16b Services
        if device.getValue(2):
            fingerprint += device.getValueText(2)

        # Incomplete 128b Services
        if device.getValue(6):
            fingerprint += device.getValueText(6)

        # Complete Local Name
        if device.getValue(9):
            fingerprint += device.getValueText(9)

        # Short Local Name
        if device.getValue(8):
            fingerprint += device.getValueText(8)

    return hashlib.sha256(fingerprint.encode()).hexdigest()

def scan_for_btle_devices(timeout=30):
    class ScanDelegate(DefaultDelegate):
        def __init__(self):
            DefaultDelegate.__init__(self)

    try:
        if set_lock(timeout+5):
            scanner = Scanner().withDelegate(ScanDelegate())
            scan_result = scanner.scan(float(timeout), passive=True)
            delete_lock()
            return(scan_result)
        else:
            print('Failed to acquire lock.')
            return
    except BTLEManagementError:
        log_btle_error()
        print('Got BTLEManagementError. Failure counter at {}.'.format(r.get('btle-error')))
        return

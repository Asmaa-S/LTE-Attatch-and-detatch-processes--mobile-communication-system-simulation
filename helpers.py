import os
from random import randint
from socket import gethostname, gethostbyname
from functools import reduce
from ast import literal_eval as eval


# returns total as checksum
# input - string

def get_my_local_host_ip():
    return gethostbyname(gethostname())


def checksum(st):
    return reduce(lambda x, y: x + y, map(ord, st))


def format_ip_packet(msg, source_ip='localhost', destination_ip='localhost'):
    # normally an ip packet would be formatted as a buffer where each field is identified by its byte position and
    # offset. However, here, for the sake of simplicity as well as clarity were just formatting it as a dictionary
    # where each key value pair represent a field in the ip header
    if destination_ip == 'localhost':
        destination_ip = get_my_local_host_ip()

    if source_ip == 'localhost':
        source_ip = get_my_local_host_ip()

    ip_version = 4
    header_length = 20  # bytes
    TOS = 0b00000000  # type of service, a byte summarizing the quality of service restraints
    total_length = 20 + len(msg.encode('utf-8'))  # equals 20 bytes for header + datasize in bytes
    identification = 0x69ed
    flags = 0x02  # don't fragment
    offset = 0
    TTL = 128  # time to live
    protocol = 17  # 17 is'udp': protocol of the upper layer

    header = {'ip_version': ip_version,
              'header_length': header_length,
              'TOS': TOS,
              'total_length': total_length,
              'identification': identification,
              'flags': flags,
              'offset': offset,
              'TTL': TTL,
              'protocol': protocol,
              'source_ip': source_ip,
              'destination_ip': destination_ip
              }
    payload = {'payload': msg}
    packet = dict(header, **payload)

    header_checksum = checksum(str(header))
    total_checksum = checksum(str(packet))
    checksums = {'header_checksum': header_checksum, 'total_checksum': total_checksum}

    packet = dict(packet, **checksums)

    return packet


def format_udp_packet(msg, source_port, destination_port):
    length = 8 + len(msg.encode('utf-8'))  # length of entire packet = header size + msg size- udp header is 8 bytes
    packet = {'source_port': source_port,
              'destination_port': destination_port,
              'length': length,
              'payload': msg
              }
    Checksum = {'checksum': checksum(str(packet))}  # checksum over entire packet

    packet = packet = dict(packet, **Checksum)
    return packet


def GTP_c_encapsulate(msg, imsi, mei):
    if msg.split()[:3] == ['CREATE', 'SESSION', 'REQUEST']:
        gtp_packet = {'flags': 0x48,
                      'message_type': 32,  # create session request
                      'message_length': len(msg.encode('utf-8')),
                      'teid': generate_tunnel_id(imsi),
                      'sequence_number': 167430,
                      'spare': 0,
                      'IMSI': imsi,
                      'APN': 'jionet.mnc854.mcc405.gprs',  # access point name
                      'MEI': mei,  # mobile equipment
                      'MSISDN': 65638974563,
                      'RAT_type': 6,  # EUTRAN
                      'serving_network': 'MCC 602- Egypt (Republic of) MNC 02',
                      # 'ULI': '',
                      'PDN_type': 'IPv4',
                      'APN_restriction': 'value 0',
                      'recovery_reset_counter': 170,
                      'bearer_context': '[grouped IE]',
                      'payload': msg
                      }

    elif msg.split()[:3] == ['CREATE', 'SESSION', 'RESPONSE']:
        gtp_packet = {'flags': 0x48,
                      'message_type': 33,  # create session response
                      'message_length': len(msg.encode('utf-8')),
                      'teid': generate_tunnel_id(imsi),
                      'sequence_number': 1129199,
                      'spare': 0,
                      'cause': 16,  # request accepted
                      'APN_restriction': 'value 0',
                      'recovery_reset_counter': 8,
                      'bearer_context': '[grouped IE]',
                      'payload': msg

                      }

    udp_packet = format_udp_packet(str(gtp_packet), 2123, 2123)
    ip_packet = format_ip_packet(str(udp_packet))
    return ip_packet


def GTP_c_decapsulate(ip_packet):
    if type(ip_packet) == str:
        ip_packet = eval(ip_packet)

    udp_packet = eval(ip_packet['payload'])
    gtp_packet = eval(udp_packet['payload'])
    msg = gtp_packet['payload']
    return msg


def generate_random_ip():
    return ".".join(map(str, (randint(0, 255)
                              for _ in range(4))))


def generate_tunnel_id(imsi):
    return imsi % 50

def Authentication_token(imsi):
    return imsi % 100
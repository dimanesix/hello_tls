import re

from chardet import UniversalDetector

from scan import scan_server, ScanError, DEFAULT_TIMEOUT, DEFAULT_MAX_WORKERS, parse_target, ConnectionSettings, \
    to_json_obj
from protocol import ClientHello
from names_and_numbers import Protocol
# from urllib.parse import quote

import os
import sys
import json
import logging
import argparse
import idna
from typing import Optional
import chardet

error_file_name = 'error.txt'

log_file_name = 'log.txt'

parser = argparse.ArgumentParser(prog="python -m hello_tls", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("target",
                    help="server to scan, in the form of 'example.com', 'example.com:443', or even a full URL")
parser.add_argument("--timeout", "-t", dest="timeout", type=float, default=DEFAULT_TIMEOUT,
                    help="socket connection timeout in seconds")
parser.add_argument("--max-workers", "-w", type=int, default=DEFAULT_MAX_WORKERS,
                    help="maximum number of threads/concurrent connections to use for scanning")
parser.add_argument("--server-name-indication", "-s", default=None,
                    help="value to be used in the SNI extension, defaults to the target host, pass empty string to not send SNI")
parser.add_argument("--test-sni", default=False, action=argparse.BooleanOptionalAction,
                    help="also attempt handshakes with missing and wrong SNI")
parser.add_argument("--certs", "-c", default=True, action=argparse.BooleanOptionalAction,
                    help="fetch the certificate chain using pyOpenSSL")
parser.add_argument("--enumerate-cipher-suites", "-C", default=True, action=argparse.BooleanOptionalAction,
                    help="enumerate supported cipher suites")
parser.add_argument("--enumerate-groups", "-G", default=True, action=argparse.BooleanOptionalAction,
                    help="enumerate supported groups")
parser.add_argument("--protocols", "-p", dest='protocols_str', default=','.join(p.name for p in Protocol),
                    help="comma separated list of TLS/SSL protocols to test")
parser.add_argument("--proxy", default=None,
                    help="HTTP proxy to use for the connection, defaults to the env variable 'http_proxy' else no proxy")
parser.add_argument("--verbose", "-v", action="count", default=0,
                    help="increase output verbosity (logging in log.txt file)")
parser.add_argument("--progress", default=False, action=argparse.BooleanOptionalAction,
                    help="write lines with progress percentages to stderr")
parser.add_argument("-l", default=False, action=argparse.BooleanOptionalAction,
                    help="scan the sites in the file -l <path_to_file>")
args = parser.parse_args()

if os.path.exists(error_file_name):
    os.remove(error_file_name)
error_file = open(error_file_name, 'a')

if os.path.exists(log_file_name):
    os.remove(log_file_name)


def scan(url: str):
    logging.basicConfig(
        datefmt='%Y-%m-%d %H:%M:%S',
        format='{asctime}.{msecs:0<3.0f} {module} {threadName} {levelname}: {message}',
        style='{',
        level=[logging.WARNING, logging.INFO, logging.DEBUG][min(2, args.verbose)],
        filename='log.txt',
        filemode='w'
    )
    # error_file = open('error.txt', 'a')
    if not args.protocols_str:
        parser.error("no protocols to test")
    try:
        protocols = [Protocol[p] for p in args.protocols_str.split(',')]
    except KeyError as e:
        parser.error(f'invalid protocol name "{e.args[0]}", must be one of {", ".join(p.name for p in Protocol)}')

    host, port = parse_target(url)  # args.target

    if args.certs and protocols == [Protocol.SSLv3]:
        parser.error("SSLv3 is not supported by pyOpenSSL, so `--protocols SSLv3` must be used with `--no-certs`")

    proxy = os.environ.get('https_proxy') or os.environ.get('HTTPS_PROXY') if args.proxy is None else args.proxy

    if args.progress:
        progress = lambda current, total: print(f'{current / total:.0%}', flush=True, file=sys.stderr)
        print('0%', flush=True, file=sys.stderr)
    else:
        progress = lambda current, total: None

    server_name: Optional[str]
    if args.server_name_indication is None:
        # Argument unset, default to host.
        server_name = host
    elif args.server_name_indication == '':
        # Argument explicitly set to empty string, interpret as "no SNI".
        server_name = None
    else:
        server_name = args.server_name_indication

    try:
        results = scan_server(
            ConnectionSettings(
                host=host,
                port=port,
                proxy=proxy,
                timeout_in_seconds=args.timeout
            ),
            ClientHello(
                protocols=protocols,
                server_name=server_name
            ),
            do_enumerate_cipher_suites=args.enumerate_cipher_suites,
            do_enumerate_groups=args.enumerate_groups,
            do_test_sni=args.test_sni,
            fetch_cert_chain=args.certs,
            max_workers=args.max_workers,
            progress=progress,
        )
        return results
    except ScanError as e:
        print(f'Scan error: {e.args[0]}', end=' ', file=error_file)  # sys.stderr
        if args.verbose > 0:
            raise
        else:
            exit(1)


def read_urls_file(path_to_file: str) -> list:
    sites_list = []
    try:
        encoding = detect_file_encoding(path_to_file)
        with open(path_to_file, 'r', encoding=encoding) as file:
            for line in file:
                sites_list.append(line.strip())
    except FileNotFoundError:
        print(f"File was not found: {path_to_file}")
        raise
    except Exception as e:
        print(f"Error in open urls file: {e}")
        raise
    return sites_list


def detect_file_encoding(file_path) -> str:
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        return encoding


def print_status(index: int, sites: list, placeholder_size: int) -> int:
    percentage = (index + 1) / len(sites) * 100
    if index % (len(sites) // 15) == 0:
        print(f'{placeholder_size * "."}{int(percentage)}%')
        return placeholder_size + 1
    else:
        return placeholder_size


if args.l:
    sites = read_urls_file(args.target)
    string_number = 0
    placeholder_size = 0
    report_file_name = 'report.txt'
    pattern_cyrillic = r'[а-яА-ЯёЁ]'
    if os.path.exists(report_file_name):
        os.remove(report_file_name)
    with open(report_file_name, 'a') as report_file:
        print(f'\nTotal number of entries: {len(sites)}. Start scanning...')
        for index, site in enumerate(sites):
            try:
                string_number = string_number + 1
                if len(sites) > 15:
                    #print_status(index, sites, placeholder_size)
                    #placeholder_size = placeholder_size + 1 #
                    placeholder_size = print_status(index, sites, placeholder_size)
                if re.search(pattern_cyrillic, site):
                    site_cyr = idna.encode(site.lower())
                    results = str(scan(site_cyr.decode()))
                else:
                    results = str(scan(site.lower()))
                match = re.search('GOST', results)
                if match:
                    print(f'site_order: {string_number} url: {site} "it looks like this site supports GOST"',
                          file=report_file)
                else:
                    continue
            except Exception as e:
                print(f'(order: {string_number} url: {site})', file=error_file)
                continue
    print(f'\nThe scan is complete! Verify {string_number} websites. See "report.txt" file.')
    print(f'See problems in "log.txt" file and errors in "errors.txt" file.')

else:
    results = scan(args.target)
    json.dump(to_json_obj(results), sys.stdout, indent=2)

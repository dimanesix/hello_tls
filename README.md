# Hello (GOST) TLS!

This program is a reworking of the Boppreh (https://github.com/boppreh/hello_tls) program to test the possibility of servers building TLS connections on GOST cipher suites. The program is a single PE file created using pyinstaller.

A file of sites for verification is submitted to the program input, and a report file ("report.txt") is created at the output, which contains sites that are more likely to support GOST cipher suites

Errors are output to a file "errors.txt" and logs are outputs to file "log.txt"

## Installation

Run hello_gost.exe
   <p><b>hello_gost.exe --timeout 5 --no-certs --no-enumerate-groups --no-test-sni -l sites.txt</b><p>
   <ul><li>timeout - waiting for a response from the server</li>
   <li>no-certs - without certificate chain check</li>
   <li>no-enumerate-groups - without groups check</li>
   <li>no-test-sni - without SNI check</li>
   <li>-l [list_of_sites_file] - test websites from the file</li></ul>

list_of_sites_file ("sites.txt") format:
   <br>www.yandex.ru
   <br>www.sberbank.ru
   <br>сбер.рф
   <br>...

## Requirements

Microsoft Windows 10

# Hello (GOST) TLS!

This program is a reworking of the Boppreh program to test the possibility of TLS servers building connections on GOST cipher suites. The program is a single PE file created using pyinstaller.

A file of sites for verification is submitted to the program input, and a report file ("report.txt") is created at the output, which contains sites that are more likely to support GOST cipher suites

Errors are output to a file "errors.txt" and logs are outputs to file "log.txt"

## Installation

Run hello_gost.exe
   hello_tls.exe --timeout 5 --no-certs --no-enumerate-groups --no-test-sni -l sites.txt
   timeout - waiting for a response from the server
   no-certs - without certificate chain check
   no-enumerate-groups - without groups check
   no-test-sni - without SNI check
   -l <sites_list_file> - test websites from list 

## Requirements

Microsoft Windows 10

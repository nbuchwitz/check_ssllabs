# check_ssllabs
Icinga check command for SSLLabs score

## Requirements

This check command depends on the following python modules:
 * enum
 * requests
 * argparse
 * signal
 * time

**Installation on Debian / Ubuntu**
```
apt install python-enum34 python-requests
```

**Installation on Redhat 6 / CentOS 6**
```
yum install python-argparse python-enum34 python34-requests
```

**Installation on Redhat 7 / CentOS 7**
```
yum install python-enum34 python-requests
```

## Usage

The ``icinga2`` folder contains the command defintion and service examples for use with Icinga2.

```shell
usage: check_ssllabs.py [-h] -d DOMAINNAME [-i IP_ADDRESS] [-p] [--no-cache]
                        [--cache-hours MAX_AGE] [--timeout TIMEOUT]
                        [-w TRESHOLD_WARNING] [-c TRESHOLD_CRITICAL]

Check command SSLLabs score monitoring

optional arguments:
  -h, --help            show this help message and exit
  -d DOMAINNAME         Domainname to test
  -i IP_ADDRESS         IP to test when the host has more than one endpoint
  -p                    Publish the results
  --no-cache            Do not accept cached results
  --cache-hours MAX_AGE
                        Max age of cached results (hours)
  --timeout TIMEOUT     Timeout for test results in seconds
  -w TRESHOLD_WARNING   Warning treshold for check value
  -c TRESHOLD_CRITICAL  Critical treshold for check value

```

## Examples

```shell
./check_ssllabs.py -d example.com
OK - SSLLabs score for domain 'example.com' is A
```

If the domain is served by multiple server, you could also specify an IP address for the test:
```
./check_ssllabs.py -d example.com -i 127.0.0.1
CRITICAL - IP address '127.0.0.1' not found in test results of domain 'example.com'
```

```
./check_ssllabs.py -d example.com -i ::1
OK - SSLLabs score for domain 'example.com' is A
```

Raise a warning if the score is greater than or equal B is:
```
./check_ssllabs.py -d example.com -w B
WARNING - SSLLabs score for domain 'example.com' is B
```

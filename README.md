# jippy!

Jippy is a small command line tool to **J**uggle **ip**s in **py**thon.

## Usage 

```
$ ./jippy.py -h                                                                  
usage: jippy.py [-h] [--output OUTPUT] [--exclude EXCLUDE [EXCLUDE ...]] {atomize,minify,count} ips [ips ...]

Convert IP notations and collect additional informations.

positional arguments:
  {atomize,minify,count}
                        Mode of operation
                                atomize: Returns a list of single IPs that are contained in the input
                                minify: Calculates the smalles number of CIDR ranges containing all IPs from the input 
                                count: Returns the number of unique IPs contained in the input
  ips                   Input IPs as space separated list or an input file with newline separated entries. Supported formats are:
                                Standard IP notation (123.123.123.123)
                                CIDR ranges (123.123.123.0/24)
                                Range notation (123.123.123.0-123)

options:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        Write the output to the specified file.
  --exclude EXCLUDE [EXCLUDE ...], -e EXCLUDE [EXCLUDE ...]
                        Remove the IPs from the input
```


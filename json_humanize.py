#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json, os, sys, getopt

def convert(inputfile, outputfile=None):
    f = open(inputfile, 'r')
    string = f.read()
    f.close()

    obj = json.loads(string.decode('utf-8'))

    dump = json.dumps(obj, ensure_ascii=False, indent=4)
    
    if not outputfile:
        dirname  = os.path.dirname(inputfile)
        basename = os.path.basename(inputfile)
        new = basename.split('.')
        new.insert(-1, 'decode')
        new = '.'.join(new)
        outputfile = os.path.join(dirname, new)
    f = open(outputfile, 'w')
    f.write(dump.encode('utf-8'))
    f.close()
    return outputfile

def main(argv):
    inputfile = None
    outputfile = None
    try:
        opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
    except getopt.GetoptError:
        print 'json_humanize.py -i <inputfile> -o <outputfile>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'json_humanize.py -i <inputfile> -o <outputfile>'
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
    outputfile = convert(inputfile, outputfile)
    print 'Input file is "', inputfile
    print 'Output file is "', outputfile

if __name__ == "__main__":
    main(sys.argv[1:])

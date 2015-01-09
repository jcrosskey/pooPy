#!/usr/bin/python

#============================
# gen_qual.py fasta_file qual_file
#============================
import sys
import os

# get base_out filename and extension
input_filename = sys.argv[1]
output_filename = sys.argv[2]
out = open(output_filename, 'wb')
quality='F'

# open and read input file
with open(input_filename, 'r') as f:
    for line in f:
        line = line.strip()
        if (line.startswith(">")):
            out.write(line+"\n")
        else:
            line_len = len(line)
            for x in range(0, line_len):
                out.write(quality)
            out.write("\n")

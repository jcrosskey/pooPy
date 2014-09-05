#!/usr/bin/python

import argparse
import sys
import os
import re 
## =================================================================
def pbcorrection_check_status(lengthFile, mapFile, alignDir, outFasta, outputFile):
    if not os.path.exists(lengthFile):
        sys.stderr.write("lengthFile {} does not exist!\n".format(lengthFile))
        return -1
        
    if not os.path.exists(mapFile):
        sys.stderr.write("mapFile {} does not exist!\n".format(mapFile))
        return -1
        
    if not os.path.exists(alignDir):
        sys.stderr.write("alignment directory {} does not exist!\n".format(alignDir))
        return -1
    if alignDir[-1] != '/':
        alignDir += '/'
        
    length_dict = dict()
    map_dict = dict()

    with open(lengthFile,'r') as length:
        for line in length:
            seqID = line.strip().split('\t')[0]
            seqLen = int(line.strip().split('\t')[1:])
            if seqLen >= 1000:
                length_dict[seqID] = seqLen
    with open(mapFile,'r') as map:
        for line in map:
            fields = line.strip().split('/')
            seqID = fields[2]
            seqID = re.sub("__","/",seqID)
            seq_dir = '/'.join(fields[1], fields[2])
            map_dict[seqID] = seq_dir

    myfasta = open(outFasta,'w')
    myout = open(outputFile, 'w')
    myout.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format("seqID", "length", "covered_bps","covered_percent", "coverage_depth", "good_region_len", "correction_time"))
    #myout.write("{}\t{}\t{}\t{}\t{}\t{}\n".format("ZMW_name","passes","min_len","max_len","map","correction"))
    for seqID in length_dict:
        if seqID in map_dict:
            seq_dir = alignDir + map_dict[seqID] + '/' # directory of this sequence, with alignment, and correction output
            correctOutFile = seq_dir + "pbcorrect.out"
            correctFastaFile = seq_dir + "corrected_PacBio.fata"
            if os.path.exists(correctFastaFile):
                correctFasta = open(correctFastaFile, 'r')
                myfasta.write(correctFasta.read())
                correctFasta.close()
            if os.path.exists(correctOutFile):
                region_len_tot = 0
                with open(correctOutFile,'r') as correctOut:
                    for line in correctOut:
                        if "covered bps:" in line:
                            covered_bps = int(re.findall('\d+',line)[0])
                            covered_percent = float(covered_bps)/length_dict[seqID]
                        elif "average coverage depth:" in line:
                            cv = re.findall('\d+.\d+', line)[0]
                        elif "total time" in line:
                            correction_time = re.findall('\d+.\d+', line)[0]
                        elif line[0] == "(":
                            region_lens = []
                            good_regions = line.strip("\n").split("\t")
                            for good_region in good_regions:
                                region_lens.append(good_region.split(": ")[-1])
                            region_len_tot = sum(map(int,region_lens))
                myout.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(seqID, length_dict[seqID], covered_bps,covered_percent, coverage_depth, good_region_len, correction_time))
            else:
                myout.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(seqID, length_dict[seqID], '-','-', '-', '-', '-'))
        else:
            myout.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(seqID, length_dict[seqID], 'NA','NA', 'NA', 'NA', 'NA'))


    myout.close()
    myfasta.close()
## =================================================================
## argument parser
## =================================================================
parser = argparse.ArgumentParser(description="summarize pacbio correction results",
                                 prog = 'pbcorrection_check_status', #program name
                                 prefix_chars='-', # prefix for options
                                 fromfile_prefix_chars='@', # if options are read from file, '@args.txt'
                                 conflict_handler='resolve', # for handling conflict options
                                 add_help=True, # include help in the options
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter # print default values for options in help message
                                 )

## input files and directories
parser.add_argument("--length",help="input length file",dest='lengthFile',required=True)
parser.add_argument("--map",help="input map file",dest='mapFile',required=True)
parser.add_argument("--alignDir",help="alignment directory",dest='alignDir',default="/chongle/shared/work/pacbio_test/02_test_mock_community/01_PacBio_correction/")

## output directory
parser.add_argument("-o","--out",help="output file",dest='outputFile',required=True)
parser.add_argument("-of","--outfasta",help="output fasta file",dest='outputFasta',required=True)

## =================================================================
## main function
## =================================================================
def main(argv=None):
    
    if argv is None:
        args = parser.parse_args()

    pbcorrection_check_status(args.lengthFile, args.mapFile, args.alignDir, args.outputFasta, args.outputFile)
##==============================================================
## call from command line (instead of interactively)
##==============================================================

if __name__ == '__main__':
    sys.exit(main())

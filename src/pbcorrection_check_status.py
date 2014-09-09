#!/usr/bin/python

import argparse
import sys
import os
import re 
import glob 
## =================================================================
def pbcorrection_check_status(alignDir, outFasta, outputBase):
    ''' same as above, instead of starting from some summary file, just go through directories for all PacBio reads.
    '''
    # check input directory information
    if not os.path.exists(alignDir):
        sys.exit("alignment directory {} does not exist!\n".format(alignDir))
    alignDir = os.path.abspath(alignDir)
    if alignDir[-1] != '/':
        alignDir += '/'
        
    # make sure the output file directory exists
    outFile_dir = os.path.dirname(os.path.abspath(outFasta)) 
    if not os.path.exists(outFile_dir):
        sys.stdout.write("{} specified by outputfile does not exist, create it now.\n".format(outFile_dir))
        os.makedirs(outFile_dir)

    # output file names
    outputGoodFile = outputBase + '.good' # output tabulated file for the reads that got corrected
    outputBadFile = outputBase + '.bad' # output tabulated file for the rads that haven't been corrected or had something wrong during the correction process

    pacbio_dirs = os.listdir(alignDir) # find all directories in the alignment directory
    sys.stdout.write("Total number of directories for PacBio sequences: {}\n".format(len(pacbio_dirs)))

    # open output files
    myfasta = open(outFasta,'w')
    myout = open(outputGoodFile, 'w')
    myoutbad = open(outputBadFile, 'w')
    # header line for the tabulated summary file, also print number of good regions now
    myout.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format("seqID", "length", "num_good_regions", "covered_bps","covered_percent", "coverage_depth", "good_region_len", "correction_time"))
    myoutbad.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format("seqID", "length", "num_good_regions", "covered_bps","covered_percent", "coverage_depth", "good_region_len", "correction_time"))
    for pdir in pacbio_dirs:
        #print pdir
        #seqName = pdir.split('/')[-1] # sequence ID
        seqName = re.sub('__', '/', pdir) # convert seqName from __ to /
        pdir = alignDir + pdir + '/'
        #print pdir, seqName
        OutFile = pdir + "pbcorrect.out"
        ErrFile = pdir + "pbcorrect.err"
        FastaFile = pdir + "corrected_PacBio.fasta"
        if not os.path.exists(ErrFile): # haven't corrected the sequence yet
            myoutbad.write('{}\tnot corrected\n'.format(seqName))
        elif os.stat(ErrFile)[6] != 0 : # if error output if not empty
            with open(ErrFile, 'r') as Err:
                Err_string = Err.read()
            if "walltime" in Err_string:
                myoutbad.write('{}\twall time exceeded\n'.format(seqName)) # walltime limit exceeded
            elif "PacBio read does not have any good region covered by the Illumina reads" in Err_string:
                myoutbad.write('{}\tno good regions\n'.format(seqName)) # walltime limit exceeded
            else:
                myoutbad.write('{}\tcheck \n'.format(seqName)) # do not know what went wrong :!
        else: # get the corrected sequence and the information of the corrected PacBio sequence
            with open(FastaFile, 'r') as correctFasta: 
                myfasta.write(correctFasta.read())
            if os.path.exists(OutFile) and os.stat(OutFile)[6] != 0:
                #sys.stdout.write("\t logged")
                region_len_tot = -1
                covered_bps = -1
                cv = -1
                correction_time = -1
                with open(OutFile,'r') as correctOut:
                    #print "\n",correctOut.read(), "\n"
                    for line in correctOut:
                        if "length:" in line:
                            seq_length = int(re.findall('\d+',line)[0])
                        if "covered bps:" in line:
                            covered_bps = int(re.findall('\d+',line)[0])
                            #print covered_bps
                        if "average coverage depth:" in line:
                            if '.' in line:
                                cv = re.findall('\d+.\d+', line)[0]
                            else:
                                cv = re.findall('\d+', line)[0]
                            #print cv
                        if "total time" in line:
                            correction_time = re.findall('\d+.\d+', line)[0]
                            #print correction_time
                        if line[0] == "(":
                            region_lens = []
                            good_regions = line.strip("\n").split("\t")[:-1]
                            num_good_regions = len(good_regions)
                            for good_region in good_regions:
                                #print good_region
                                region_lens.append(int(good_region.split(":")[-1]))
                            region_len_tot = sum(region_lens)
                if covered_bps == -1:
                    covered_percent = -1
                else:
                    covered_percent = float(covered_bps)/seq_length
                #if region_len_tot == -1:
                #    myoutbad.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(seqName, seq_length,num_good_regions, covered_bps,covered_percent, cv, region_len_tot, correction_time))
                myout.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(seqName, seq_length, num_good_regions, covered_bps,covered_percent, cv, region_len_tot, correction_time))
            else:
                myoutbad.write('{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(seqName, seq_length, 'NA','NA', 'NA', 'NA', 'NA'))
        #sys.stdout.write("\n")


    myout.close()
    myoutbad.close()
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
#parser.add_argument("--length",help="input length file",dest='lengthFile',required=True)
#parser.add_argument("--map",help="input map file",dest='mapFile',required=True)
parser.add_argument("--alignDir",help="alignment directory",dest='alignDir',default="/chongle/shared/work/pacbio_test/02_test_mock_community/01_PacBio_correction/")

## output directory
parser.add_argument("-o","--out",help="output file",dest='outputBase',required=True)
parser.add_argument("-of","--outfasta",help="output fasta file",dest='outputFasta',required=True)

## =================================================================
## main function
## =================================================================
def main(argv=None):
    
    if argv is None:
        args = parser.parse_args()

    pbcorrection_check_status(args.alignDir, args.outputFasta, args.outputBase)
##==============================================================
## call from command line (instead of interactively)
##==============================================================

if __name__ == '__main__':
    sys.exit(main())

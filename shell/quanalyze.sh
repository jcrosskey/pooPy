#!/bin/bash

#================= parse command line arguments ===============##
NO_ARGS=0
E_OPTERROR=85
SCRIPT=`basename $0`

#format of the output
BOLD="\x1b[1m"
NORMAL="\x1b[00m"
RED='\033[01;31m'
GREEN='\033[01;32m'
YELLOW='\033[01;33m'
PURPLE='\033[01;35m'
CYAN='\033[01;36m'
WHITE='\033[01;37m'
UNDERLINE='\033[4m'

usage() { 
	echo -e "${BOLD}${RED}${SCRIPT} ${NORMAL}parses quast output files and generate files for misassembled contigs IDs and their mapped coordinates\n"
	echo -e "${BOLD}Usage: ${NORMAL}${SCRIPT} -p <prefix> <quast_output_dir>" >&2
	echo -e "${BOLD}-p${NORMAL}    --Prefix for the quast output files, required"
	echo -e "${BOLD}-h${NORMAL}    --Print this help message"
}


#check the number of arguments, if none is passed, print help and exit.
if [ $# -eq "$NO_ARGS" ] 
then
	usage
	exit $E_OPTERROR
fi

while getopts ":hp:" opt 
do
	case $opt in
		h)
			usage
			exit 0
			;;
		p)
			prefix=$OPTARG
			echo "prefix for the output files is $OPTARG" >&2
			;;
#		i)
#			input=$OPTARG
#			echo "input file is $OPTARG" >&2
#			;;
#		o)
#			out_dir=$OPTARG
#			echo "output directory is $OPTARG" >&2
#			;;
		:)
			echo "Option -$OPTARG requires an argument" >&2
			exit 1
			;;
		\?)
			echo "Invalid option: -$OPTARG" >&2
			echo -e "Use ${SCRIPT} -h to see help information\n"
			exit 1
			;;
	esac
done
shift $((OPTIND-1))

quast_dir=$1/contigs_reports
mis_contig_fa=${quast_dir}/${prefix}.mis_contigs.fa
contigs_report=${quast_dir}/contigs_report_${prefix}.stdout
filtered_coords=${quast_dir}/nucmer_output/${prefix}.coords.filtered

echo '>>>Extract extensively misassembled contigs from' ${mis_contig_fa}
grep '^>' ${mis_contig_fa} | sed 's/>//g' > ext_mis.id

echo '>>>Extract locally misassembled contigs from' ${contigs_report}
grep -A 1 'local misassembly' ${contigs_report} | grep -v 'local misassembly' | grep -v '^--' | awk '{print $(NF)}' > local_mis.id

cat ext_mis.id local_mis.id | sort -u -nk 1 > mis.id
rm ext_mis.id local_mis.id

echo '>>>Find the mapping coordinates for the misassemble contigs'
awk 'NR==FNR{ids[$0];next} $NF in ids' mis.id $filtered_coords > mis.coords

exit #?

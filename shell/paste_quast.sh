#!/bin/bash

if [ -e ref.txt ]
then
	rm ref.txt
fi
touch ref.txt
cols=("Assembly" "# contigs (>= 0 bp)" "# contigs (>= 1000 bp)" "Total length (>= 0 bp)" "Total length (>= 1000 bp)" "# contigs  " "Largest contig" \
	"Total length  " "Largest contig"  "Reference length" "GC (%)" "Reference GC (%)" "N50" "NG50" "N75" "L50" "LG50" "L75" \
	"# misassemblies" "# misassembled contigs" "Misassembled contigs length" "# local misassemblies" "# unaligned contigs" "Genome fraction" \
	"Duplication ratio" "# mismatches per 100 kbp" "# indels per 100 kbp" "Largest alignment" "NA25" "NGA25" "NA50" "NGA50" "NA75" "LA25" "LGA25" "LA50" "LGA50" "LA75")
#IFS=$'\n' read -d '' -r -a refNames < refNames.txt
#echo refName >> ref.txt

for i in "${cols[@]}"
do
	echo $i >> ref.txt
done

for f in `find $1 -type f -name 'report.txt'`
do 
	echo $f

	for i in "${cols[@]}"
	do
		if [ -e $f ]
		then
			if grep -q "^$i" $f
			then
				#echo Found $i
				#echo `grep "^$i" $f | cut -c 30-`
				grep "^$i" $f | cut -c 28- | tr -d '[[:blank:]]' >> temp
			else
				#echo didn\'t find $i
				echo - >> temp
			fi
		else
			echo - >> temp
		fi
	done
	paste ref.txt temp > tmp
	rm -f temp
	mv tmp ref.txt
done

## transpose ref.txt
awk -F "\t" '
{ 
	for (i=1; i<=NF; i++)  {
		a[NR,i] = $i
	}
}
NF>p { p = NF }
END {    
for(j=1; j<=p; j++) {
	str=a[1,j]
	for(i=2; i<=NR; i++){
		str=str"\t"a[i,j];
	}
	print str
}
										    }' ref.txt > transpose.ref.txt

awk 'BEGIN {RS=">";FS="\n";ORS="\n"} {if(FNR>1) print ">"NR"\n"$2; else NR--}'

#!/bin/bash                                                                                                           
                                                                                                                      
if [ $# -eq 1 ]; then                                                                                                 
    pyProgName="$1"                                                                                                   
    dirName="./"                                                                                                      
elif [ $# -eq 2 ]; then                                                                                               
    pyProgName="$2"                                                                                                   
    dirName="/home/jj/git/$1"                                                                                         
else                                                                                                                  
    echo bad number of arguments                                                                                      
    exit 1                                                                                                            
fi                                                                                                                    
                                                                                                                      
pyProgName="${pyProgName%\.py}"                                                                                       
pyFileName="$pyProgName.py"                                                                                           
                                                                                                                      
pyFilePath=$(find $dirName -name $pyFileName)                                                                         
if [ -z $pyFilePath ]                                                                                                 
then                                                                                                                  
    echo "cannot find python file named $pyFileName"                                                                  
    exit 2                                                                                                            
fi                                                                                                                    
                                                                                                                      
                                                                                                                      
cmd="PYTHONPATH=$PYTHONPATH pylint $pyFilePath --rcfile=proj_config/pylintrc --msg-template={path}:{line}:\\ [{msg_id}
\\({symbol}\\),\\ {obj}]\\ {msg}";                                                                                    
                                                                                                                      
echo -e "will execute $cmd\n";                                                                                        
                                                                                                                      
eval $cmd                                                                                                             

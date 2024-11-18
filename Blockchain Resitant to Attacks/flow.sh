# Help me parse through ./observations/BlockChains/ to find *.dot and convert into .png files 
# using dot -Tpng <file>.dot -o <file>.png

# Find all .dot files in ./observations/BlockChains/

for file in ./observations/BlockChains/*.dot
do
    # Convert .dot to .png
    dot -Tpng $file -o ${file%.dot}_format.png
    

done
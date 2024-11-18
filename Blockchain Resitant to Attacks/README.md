# CS 765 Assignment 2 Selfish Mining

Command to Run

```
python main.py -n 15 -h0 0.2 -h1 0.3 -I 1000 -ttx 100 -stop 1 --save False
```

```
 n : number of peers in the network
h0 : hash power of selfish miner 1
h1 : hash power of selfish miner 2
stop : stop condition after Blocks
ttx : mean inter-arrival time between transactions
I : average time taken to mine a block
save : save the events in the file
```

Change values to test further.. 

---

Packages to install 

```
pip install networkx
pip install numpy
pip install pygraphviz
pip install pydot
```

Directory Structure 

```
.
 |-Design Document.pdf
 |-flow.sh
 |-main.py
 |-observations
 | |-BlockChains
 | |-Results
 | |-Events
 | |-Transactions
 |-Report.pdf
 |-Results.txt
 |-utils
 | |-definitions.py
 | |-generators.py
 | |-utils.py
```

For more visualization, you can use the dot files present in ./observations/BlockChains with flow.sh
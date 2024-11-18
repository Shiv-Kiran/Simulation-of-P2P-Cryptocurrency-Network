# CS 765 Assignment 1

Command to Run

```
python main.py -n 20 -z0 50 -z1 50 -I 1000 -ttx 100 --save False
```

```
n : number of peers in the network
z0 : percentage of slow peers
z1 : percentage of peers having low CPU power
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
```

Directory Structure 

```
.
 |-Design Document.pdf
 |-main.py
 |-observations
 | |-BlockChains
 | |-Results
 | |-Events
 | |-Transactions
 |-Report.pdf
 |-utils
 | |-definitions.py
 | |-generators.py
 | |-utils.py
```

For more visualization, you can use the dot files present in ./observations/BlockChains
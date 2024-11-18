from numpy.random import default_rng
import networkx as nx
import matplotlib.pyplot as plt
from utils.definitions import Peer, Transaction, Event, BlockChain, Block
from queue import PriorityQueue 
from utils.generators import ExponentialDist

random_gen = default_rng(0)
Initbalance = 114 # Lets assume initial balance of all peers as 114.(75+20+19).




def getPercent(zo, n):
    '''
    Function to get the percentage of slow and low CPU peers.
    '''
    arr = [True for i in range(int((zo * n) /100))] + [False for i in range(n - int((zo * n) /100))]
    random_gen.shuffle(arr)
    return arr


def get_Peers(num_of_peers, percent_slow, percent_low_CPU):
    '''
    Function to initialize the Peers in the network.
    '''
    Peers = []
    slowNodes = getPercent(percent_slow, num_of_peers)
    lowCPUNodes = getPercent(percent_low_CPU, num_of_peers)
    gensis = Block(0, 0, None, Transaction(peer1=None, amount=0, timestamp=0, is_coinbase=True), True,gen=True,  balances = [Initbalance]*num_of_peers)
    for i in range(num_of_peers):
        Peers.append(Peer(i,slow=slowNodes[i],low_CPU=lowCPUNodes[i],balance=Initbalance, neighbors=[], gensis = gensis)) # Creating peers here.
    
    return Peers



def generate_network(n, zo, z1): #p2p network connection
    '''
    Function to generate the network of peers and Graph of the network.
    '''
    Graph = nx.Graph()
    Graph.add_nodes_from(range(n))
    Peers = [None] *n
    Peers = get_Peers(n, zo, z1)

    while not nx.is_connected(Graph):
        Graph = nx.Graph()
        Graph.add_nodes_from(range(n))
        # reset nodes
        for peer in Peers:
            peer.neighbors = set()
        # generate random connections
        for nodeX in range(n):
            l = random_gen.integers(3, 7) #random number of peers
            # check for number of neighbors for nodeX in the graph
            while Graph.degree[nodeX] < l:
                nodeY = random_gen.choice([j for j in range(n) if j != nodeX and j not in Graph.neighbors(nodeX)])  
                
                if Graph.degree[nodeY] < 6:
                    connection(nodeX, nodeY, Peers, Graph)

    return Peers, Graph

    #adding edges of the peer graph
def connection(nodeX, nodeY, Peers, Graph):
    '''
    Connect the Peers in the Network if not already connected 
    '''

    if(nodeX not in Graph.neighbors( nodeY)):
        Graph.add_edge(nodeX, nodeY)
        Graph.add_edge(nodeY, nodeX)
        Peers[nodeX].neighbors.add(Peers[nodeY])
        Peers[nodeY].neighbors.add(Peers[nodeX])

def print_graph(Graph):
    '''
    Visualize the Network Graph
    '''
    plt.figure()
    nx.draw(Graph, with_labels=True)
    plt.savefig('./BlockChain_Network_Connections.png')
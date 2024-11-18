import argparse
from utils.utils import generate_network, print_graph
from utils.generators import ExponentialDist, getHashDist
from utils.definitions import Event, Block, EventList
import networkx as nx
import matplotlib.pyplot as plt
from utils.definitions import blockId, total_blocks
import os 
from networkx.drawing.nx_agraph import write_dot, graphviz_layout
import warnings
warnings.filterwarnings("ignore", message="More than 20 figures have been opened*")


'''
Simulator class to simulate the cryptocurrency network
Contains the following functions:
Peers: list of peers in the network
Graph: Graph of the network
TtxDist: Transaction inter-arrival time distribution
slowHash: Distribution for slow peers
fastHash: Distribution for fast peers
sim_Time: Simulation time
'''


class Simulator:
    def __init__(self, n, z0, z1, ttx, I, sim_Time = 5000, block_limit = 20, save_Events = False):
        self.n = n
        self.Peers, self.Graph = generate_network(n, z0, z1)
        self.TtxDist = ExponentialDist(ttx)
        self.slowHash, self.fastHash = getHashDist(self.Peers, I)
        self.sim_Time = sim_Time
        self.Block_Limit = block_limit
        self.save_Events = save_Events
    

    def outputEvent(self, event):
        '''
        output the event to the respective file
        '''

        if event.event_type == "Transaction_Gen":
            # output print to sender.txt 
            with open(f'./observations/Events/peer_{event.sender.unique_id}.txt', 'a') as f:
                f.write(f"{event.timestamp} {event.event_type} sender = {event.sender.unique_id}  \n")
        elif event.event_type == "Transaction_Rec":
            with open(f'./observations/Events/peer_{event.receiver.unique_id}.txt', 'a') as f:
                f.write(f"{event.timestamp} {event.event_type} {event.receiver.unique_id} {event.txn.txid} {event.txn.amount} Transaction from {event.txn.peer1.unique_id} to {event.txn.peer2.unique_id} \n")
        elif event.event_type == "Block_Gen":
            with open(f'./observations/Events/peer_{event.generator.unique_id}.txt', 'a') as f:
                f.write(f"{event.timestamp} {event.event_type} {event.generator.unique_id} \n")
        elif event.event_type == "Block_Rec":
            with open(f'./observations/Events/peer_{event.receiver.unique_id}.txt', 'a') as f:
                f.write(f"{event.timestamp} {event.event_type} {event.receiver.unique_id} {event.block.id} \n")
        
            

    def simulate(self):
        '''
        Simulate the cryptocurrency network
        
        '''

        # Add 1st transaction for each peer 
        for i in range(self.n):
            timeStamp = self.TtxDist()
            EventList.put((timeStamp,Event(timeStamp, "Transaction_Gen", sender=self.Peers[i])))
        
        # first block 
        for i in range(self.n):
            if self.Peers[i].low_CPU:
                timeStamp = self.slowHash()
                EventList.put((timeStamp,Event(timeStamp, "Block_Gen", generator=self.Peers[i])))
            else:
                timeStamp = self.fastHash()
                EventList.put((timeStamp,Event(timeStamp, "Block_Gen", generator=self.Peers[i])))
        

        # Until the event list is empty or BlockChain size is less than 20
        while not EventList.empty():
            time, event = EventList.get()
            # self.outputEvent(event)
            # if time > self.sim_Time:
                # break

            # check for the type event.event_type using case 
            if self.save_Events:
                self.outputEvent(event)
            if event.event_type == "Transaction_Gen":
                delta_t = self.TtxDist()
                event.sender.createTransaction(event, delta_t)
            elif event.event_type == "Transaction_Rec":
                event.receiver.receiveTransaction(event)
            elif event.event_type == "Block_Gen":
                if event.generator.blockchain.bcTree.size() >=  self.Block_Limit:
                    break
                if event.generator.low_CPU:
                    delta_t = self.slowHash()
                else :
                    delta_t = self.fastHash()
                event.generator.createBlock(event, delta_t)
            elif event.event_type == "Block_Rec":
                event.receiver.receiveBlock(event)
            

    def drawBlockChains(self, save=False):
        '''
        Draw the blockchains of all the peers
        '''
        for i in range(self.n):
            plt.figure()
            nx.draw(self.Peers[i].blockchain.bcTree, pos=nx.planar_layout(self.Peers[i].blockchain.bcTree), node_size=200, node_color='blue', with_labels=True)
            if save:
                plt.savefig(f'./observations/BlockChains/bc_{i}.png')
            else:
                plt.show()

            plt.close() 
            plt.figure()
            nx.draw(self.Peers[i].blockchain.bcTree, pos=nx.kamada_kawai_layout(self.Peers[i].blockchain.bcTree), node_size=200, node_color='blue', with_labels=True)
            if save:
                plt.savefig(f'./observations/BlockChains/bc_kkl_{i}.png')
            plt.close() 


    def drawChain(self, unique_id, save=False):
        '''
        Draw the blockChain of single Peer 
        '''
        i = unique_id
        plt.figure()
        pos = graphviz_layout(self.Peers[i].blockchain.bcTree, prog="dot")
        # for each label add its creator id 
        labels = {}
        for node in self.Peers[i].blockchain.bcTree.nodes():
            if node == 0:
                labels[node] = "Genesis"
            else:
                labels[node] = f"Peer_{self.Peers[i].blockchain.id2blk[node].creator.unique_id}, {node}"

        # pos = nx.nx_agraph.graphviz_layout(self.Peers[i].blockchain.bcTree, prog="dot")
        # Create new graph with lables as nodes and nodes present in the blockchain as edges
        tempGraph = nx.DiGraph()
        for edge in self.Peers[i].blockchain.bcTree.edges():
            tempGraph.add_edge(labels[edge[0]], labels[edge[1]])
        write_dot(tempGraph, f'./observations/BlockChains/bc_{i}.dot')

        

        
        nx.draw(self.Peers[i].blockchain.bcTree, pos, with_labels=True, labels=labels)
        if save:
            plt.savefig(f'./observations/BlockChains/bc_{i}.png')
        else:
            plt.show()

        plt.figure()
        nx.draw(self.Peers[i].blockchain.bcTree, pos=nx.kamada_kawai_layout(self.Peers[i].blockchain.bcTree), node_size=200, node_color='blue', with_labels=True)
        # if save:
            # plt.savefig(f'./observations/BlockChains/bc_kkl_{i}.png')

    def printDetails(self):
        '''
        Saving the details of the peers in the network 
        '''


        ratios = {}
        print_graph(self.Graph)

        for i in range(self.n):
            unique_id = i
            peer = self.Peers[unique_id]
            self.drawChain(unique_id, save=True)
            genesis = 0

            node_type_successful = {}
            node_type_blocks_mined = {}
            for type in ['slow_low', 'slow_high', 'fast_low', 'fast_high']:
                node_type_successful[type] = 0
                node_type_blocks_mined[type] = 0
            mined_in_longest_chain = {}

            block = peer.blockchain.long_Block
            ordering = []
            while block.id != genesis:
                ordering.append(block.id)
                temp_peer = block.creator
                block = temp_peer.blockchain.id2blk[block.pblkid]
            ordering.append(0)

            self.drawChain(unique_id, save=True)
            count = 0
            for i in ordering: 
                if i in peer.blocksCreated:
                    count += 1
            if len(peer.blocksCreated) == 0:
                ratios[unique_id] = None
            else:
                ratios[unique_id] = count/len(peer.blocksCreated)
                # round off the ratio to 3 decimal places
                ratios[unique_id] = round(ratios[unique_id], 3)

            cpu = 'low' if peer.low_CPU else 'high'
            speed = 'slow' if peer.slow else 'fast'
            type_peer = cpu + '_' + speed


            with open(f'./observations/Results/peer_{unique_id}.txt', 'a') as f:
                f.write("Peer_" + str(unique_id) + " is of type " + type_peer + " \n")
                f.write("Peer Block Details:" + str(peer.blocksCreated) + str(peer.blockchain.id2blk.keys()) + str(peer.blockchain.id2blk_orphan.keys()) + str(peer.blockchain.arrival_time.keys()) + "\n")
                f.write("Length of longest chain (including genesis block):" + str(peer.blockchain.long_Block.length) + "\n")
                f.write("Longest chain:" + str(ordering) + "\n")
                f.write("Total number of blocks at Peer_" +str(unique_id) +" : "  + str(total_blocks() - 1) + "\n")
                f.write("Fraction of longChain to Total Blocks " + str(len(ordering)/(total_blocks())) + "\n")
                f.write("Ratio of blocks mined by Peer_" +str(unique_id) + " that made it to the longest chain: " + str(ratios[unique_id]) + "\n")
                f.write("\n")
            
            # Store Arrival times of Blocks 
            with open(f'./observations/Results/arrival_times_peer_{unique_id}.csv', 'a') as f:
                f.write("Block_id, Arrival_Time \n")
                for key in peer.blockchain.arrival_time:
                    f.write(str(key) + ", " + str(peer.blockchain.arrival_time[key]) + "\n")
                
        # print("Ratios of blocks mined by each node that made it to the longest chain:", ratios)
        types = ['low_slow', 'high_slow', 'low_fast', 'high_fast']
        average_type_ratios = {}
        # iterate through the ratios and check for the type of the peer
        for type in types:
            sum = 0
            count = 0
            for key in ratios:
                peer = self.Peers[key]
                cpu = 'low' if peer.low_CPU else 'high'
                speed = 'slow' if peer.slow else 'fast'

                type_peer = cpu + '_' + speed
                if type == type_peer:
                    if ratios[key] == None:
                        continue
                    sum += ratios[key]
                    count += 1
            if count == 0:
                average_type_ratios[type] = None
            else  :
                average_type_ratios[type] = sum/count
                average_type_ratios[type] = round(average_type_ratios[type], 3)

        # append values to csv file 
        with open(f'./observations/Results/average_type_ratios.csv', 'a') as f:
            # f.write("Type, Average_Ratio \n")
            for key in average_type_ratios:
                f.write(key + ", " + str(average_type_ratios[key]) + "\n")

        # print ratios in formatted way
        for key in ratios:
            peer = self.Peers[key]
            cpu = 'low' if peer.low_CPU else 'high'
            speed = 'slow' if peer.slow else 'fast'
            type_peer = cpu + '_' + speed
            print(f"Ratio of blocks mined by Peer_{key} of type "+ type_peer + f" that made it to the longest chain: {ratios[key]}")

        # print("Average Type Ratios: ", average_type_ratios)
        for type in types:
            print(f"Average ratio of blocks in longest chain mined by {type} node:", average_type_ratios[type])
        
        

                
    def checkFolder(self):
        '''
        Function to check the folder and create if not present
        '''

        # check for observations folder 
        if not os.path.exists('./observations'):
            os.makedirs('./observations')
            os.makedirs('./observations/Results')
            os.makedirs('./observations/BlockChains')
            os.makedirs('./observations/Events')
            os.makedirs('./observations/Transactions')
        else:
            if not os.path.exists('./observations/Results'):
                os.makedirs('./observations/Results')
            if not os.path.exists('./observations/BlockChains'):
                os.makedirs('./observations/BlockChains')
            if not os.path.exists('./observations/Events'):
                os.makedirs('./observations/Events')
            if not os.path.exists('./observations/Transactions'):
                os.makedirs('./observations/Transactions')
        # clean the folders 
        for file in os.listdir('./observations/Results'):
            os.remove(f'./observations/Results/{file}')
        for file in os.listdir('./observations/BlockChains'):
            os.remove(f'./observations/BlockChains/{file}')
        for file in os.listdir('./observations/Events'):
            os.remove(f'./observations/Events/{file}')
        for file in os.listdir('./observations/Transactions'):
            os.remove(f'./observations/Transactions/{file}')






if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Cryptocurrency Simulator')
    parser.add_argument('-n', '--num_nodes', default=10, type=int, help='Num Nodes')
    parser.add_argument('-z0', '--percent_slow', default=50, type=float, help=" %  of slow nodes")
    parser.add_argument('-z1', '--percent_lowCPU', default=50, type=float, help='percentage of nodes having low CPU power')
    parser.add_argument('-ttx', '--mean_inter_arrival', default=10, type=float, help='mean inter-arrival time between transactions')
    parser.add_argument('-I', '--average_block_mining_time', default=100, type=float, help='average time taken to mine a block')
    parser.add_argument('-s', '--save_events', default=False, type=bool, help='save the Events')
    args = parser.parse_args()

    n = args.num_nodes
    z0 = args.percent_slow
    z1 = args.percent_lowCPU
    ttx = args.mean_inter_arrival # 10 
    I = args.average_block_mining_time  # 10 minutes
    save = args.save_events

    '''
    n : number of peers in the network
    z0 : percentage of slow peers
    z1 : percentage of peers having low CPU power
    ttx : mean inter-arrival time between transactions
    I : average time taken to mine a block
    save : save the events in the file
    '''
    print (f"n={n}, z0={z0}, z1={z1}, ttx={ttx}, I={I}, save_Events={save}")
    sim = Simulator(n, z0, z1, ttx, I, save_Events=save)
    sim.checkFolder()
    sim.simulate()
    # sim.drawBlockChains( save=True)
    sim.printDetails()
    # sim.printRes()
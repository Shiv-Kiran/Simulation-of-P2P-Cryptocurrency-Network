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
honestHash: Hash power distribution of honest peers
att_hash_1: Hash power distribution of selfish miner 1
att_hash_2: Hash power distribution of selfish miner 2
sim_Time: Simulation time
stop_condition: Emptying the EventList after the 2*n blocks are mined
'''


class Simulator:
    def __init__(self, n, z0,  ttx, I, hash_selfish, sim_Time = 5000, save_Events = False, stop_condition = False):
        '''
        zo = 50 % of honest are slow 
        z1 = same for all honest peers 
        '''

        self.n = n
        self.Peers, self.Graph = generate_network(n, z0, 100)
        self.TtxDist = ExponentialDist(ttx)
        self.honestHash = getHashDist(self.Peers, I, hash_selfish)


        self.att_hash_1 = ExponentialDist(I/hash_selfish[0])
        self.att_hash_2 = ExponentialDist(I/hash_selfish[1])
        self.sim_Time = sim_Time
        self.Block_Limit = 2 * n 
        self.save_Events = save_Events
        self.stop_condition = stop_condition

        # Last 2 peers are selfish miners
    

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
        Simulate the cryptocurrency network with 2 selfish Miners 
        
        '''

        # Add 1st transaction for each peer 
        for i in range(self.n):
            timeStamp = self.TtxDist()
            EventList.put((timeStamp,Event(timeStamp, "Transaction_Gen", sender=self.Peers[i])))
        
        # first block 
        for i in range(self.n):
            # check if self.Peers[i] has prefix of selfish 
            if self.Peers[i].peer_type == "selfish1":
                timeStamp = self.att_hash_1()
                EventList.put((timeStamp,Event(timeStamp, "Block_Gen", generator=self.Peers[i])))
            elif self.Peers[i].peer_type == "selfish2":
                timeStamp = self.att_hash_2()
                EventList.put((timeStamp,Event(timeStamp, "Block_Gen", generator=self.Peers[i])))
            # elif self.Peers[i].low_CPU:
            #     timeStamp = self.lowHash()
            #     EventList.put((timeStamp,Event(timeStamp, "Block_Gen", generator=self.Peers[i])))
            else:
                timeStamp = self.honestHash()
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
                if event.generator.peer_type == "selfish1":
                    delta_t = self.att_hash_1()
                elif event.generator.peer_type == "selfish2":
                    delta_t = self.att_hash_2()
                # elif event.generator.low_CPU:
                #     delta_t = self.lowHash()
                else :
                    delta_t = self.honestHash()
                event.generator.createBlock(event, delta_t)
            elif event.event_type == "Block_Rec":
                event.receiver.receiveBlock(event)
        

        # Empty the EventList after the 2*n blocks are mined
        while not EventList.empty() and self.stop_condition: 
            time, event = EventList.get()

            if self.save_Events:
                self.outputEvent(event)
            if event.event_type == "Transaction_Gen":
                continue
            elif event.event_type == "Transaction_Rec":
                continue
            elif event.event_type == "Block_Gen":
                if event.generator.peer_type == "selfish1":
                    delta_t = self.att_hash_1()
                elif event.generator.peer_type == "selfish2":
                    delta_t = self.att_hash_2()
                # elif event.generator.low_CPU:
                #     delta_t = self.lowHash()
                else :
                    delta_t = self.honestHash()
                    continue
                event.generator.createBlock(event, delta_t, stop =True)
            elif event.event_type == "Block_Rec":
                event.receiver.receiveBlock(event, stop=True)


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

        pos = nx.nx_agraph.graphviz_layout(self.Peers[i].blockchain.bcTree, prog="dot")
        # Create new graph with lables as nodes and nodes present in the blockchain as edges
        tempGraph = nx.DiGraph()
        # for edge in self.Peers[i].blockchain.bcTree.edges():
        #     tempGraph.add_edge(labels[edge[0]], labels[edge[1]])
        # write_dot(tempGraph, f'./observations/BlockChains/bc_{i}.dot')
        # Define colors for nodes with specific prefixes
        prefix_colors = {
            "Peer_0,": "blue",
            "Peer_1,": "red"
        }

        for edge in self.Peers[i].blockchain.bcTree.edges():
            source_label = labels[edge[0]]
            target_label = labels[edge[1]]
            
            # Check if the source node label starts with specified prefixes
            for prefix, color in prefix_colors.items():
                if source_label.startswith(prefix):
                    tempGraph.add_node(source_label, color=color)
                    break
                    
            # Check if the target node label starts with specified prefixes
            for prefix, color in prefix_colors.items():
                if target_label.startswith(prefix):
                    tempGraph.add_node(target_label, color=color)
                    break
            
            tempGraph.add_edge(source_label, target_label)

        write_dot(tempGraph, f'./observations/BlockChains/bc_{i}.dot')
        

        

        
        nx.draw(self.Peers[i].blockchain.bcTree, pos, with_labels=True, labels=labels)
        nx.draw(self.Peers[i].blockchain.bcTree, with_labels=True, labels=labels)
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

            cpu = 'honest' if peer.peer_type == 'honest' else 'selfish'
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
        '''
                
        # print("Ratios of blocks mined by each node that made it to the longest chain:", ratios)
        types = ['low_slow', 'high_slow', 'low_fast', 'high_fast']
        average_type_ratios = {}
        # iterate through the ratios and check for the type of the peer
        for type in types:
            sum = 0
            count = 0
            for key in ratios:
                peer = self.Peers[key]
                # cpu = 'low' if peer.low_CPU else 'high'
                cpu = 'honest' if peer.peer_type == 'honest' else 'selfish'
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
        
        '''

        # append values to csv file 
        # with open(f'./observations/Results/average_type_ratios.csv', 'a') as f:
        #     # f.write("Type, Average_Ratio \n")
        #     for key in average_type_ratios:
        #         f.write(key + ", " + str(average_type_ratios[key]) + "\n")

        '''
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
        '''
        # Here for each blk in blockchain check if it is made by honest or selfish miner and store the count 
        # check block chain n-1 peer 
        # check for the block chain of selfish miner
        # selfish_count1 = 0
        # selfish_count2 = 0
        # total_self_blks = 0
        # blockChain = self.Peers[self.n-1].blockchain
        # for blk in blockChain.bcTree.nodes():
        #     if blk == 0:
        #         continue
        #     creator = blockChain.id2blk[blk].creator
        #     if creator.peer_type == "selfish1" or creator.peer_type == "selfish2":
        #         selfish_count += 1
        #     total_self_blks += 1
        # print("Selfish count in the block chain of n-1 peer: ", selfish_count, " Total Selfish blocks: ", total_self_blks)

        longest_chain_length = 0
        # get total number of blocks 
        # for i in range(self.n):
        #     longest_chain_length = max(longest_chain_length, self.Peers[i].blockchain.long_Block.length)

        adv1_blk_created = self.Peers[0].blocksCreated
        adv2_blk_created = self.Peers[1].blocksCreated

        adv1_blk_in_chain = 0
        adv2_blk_in_chain = 0

        honest_Peer = 3


        honest_long_blk = self.Peers[honest_Peer].blockchain.long_Block
        longest_chain_length = honest_long_blk.length

        while honest_long_blk.id != 0:
            if honest_long_blk.creator.peer_type == "selfish1":
                adv1_blk_in_chain += 1
            if honest_long_blk.creator.peer_type == "selfish2":
                adv2_blk_in_chain += 1
            honest_long_blk = self.Peers[honest_Peer].blockchain.id2blk[honest_long_blk.pblkid]



        # print MPU only if adv1_blk_created is non zero else print 0 
        if len(adv1_blk_created) == 0:
            print("MPU of selfish miner 0: 0")
        else:
            print("MPU of selfish miner 0: ", adv1_blk_in_chain/len(adv1_blk_created))

        if len(adv2_blk_created) == 0:
            print("MPU of selfish miner 1: 0")
        else:
            print("MPU of selfish miner 1: ", adv2_blk_in_chain/len(adv2_blk_created))

        print("MPU overall: ", longest_chain_length/total_blocks())
        print("Blocks created by selfish miner 0: ", len(adv1_blk_created), " Blocks in longest chain: ", adv1_blk_in_chain)
        print("Blocks created by selfish miner 1: ", len(adv2_blk_created), " Blocks in longest chain: ", adv2_blk_in_chain)

        print("Length of longest Chain : ", longest_chain_length, " Total Blocks : ", total_blocks())
        

                
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
    parser.add_argument('-ttx', '--mean_inter_arrival', default=10, type=float, help='mean inter-arrival time between transactions')
    parser.add_argument('-I', '--average_block_mining_time', default=100, type=float, help='average time taken to mine a block')
    parser.add_argument('-s', '--save_events', default=False, type=bool, help='save the Events')

    parser.add_argument('-h0', '--hash_selfish0', default=0.3, type=float, help='hash power of selfish miner 0')
    parser.add_argument('-h1', '--hash_selfish1', default=0.3, type=float, help='hash power of selfish miner 1')
    parser.add_argument('-stop', '--stop_condition', default=False, type=float, help='stop condition after Blocks')


    # parser.add_argument('-zeta1', '--zeta_selfish1', default=0.3, type=float, help='Percentage of neighbors to selfish')
    # parser.add_argument('-zeta2', '--zeta_selfish2', default=0.3, type=float, help='Percentage of neighbors to selfish')


    args = parser.parse_args()

    n = args.num_nodes  #  n-2 + 2 
    z0 = args.percent_slow
    ttx = args.mean_inter_arrival # 10 
    I = args.average_block_mining_time  # 10 minutes
    save = args.save_events

    h0 = args.hash_selfish0
    h1 = args.hash_selfish1
    stop = args.stop_condition
    # zeta1 = args.zeta_selfish1
    # zeta2 = args.zeta_selfish2


    '''
    n : number of peers in the network
    z0 : percentage of slow peers
    h0 : hash power of selfish miner 1
    h1 : hash power of selfish miner 2
    stop : stop condition after Blocks
    ttx : mean inter-arrival time between transactions
    I : average time taken to mine a block
    save : save the events in the file
    '''

    # if h1 or h2 assign it very small value 
    if h0 == 0:
        h0 = 0.0001
    if h1 == 0:
        h1 = 0.0001


    print (f"Simulating the cryptocurrency network with {n} peers")
    print(f"z0 = {z0}, ttx = {ttx}, I = {I}, h0 = {h0}, h1 = {h1}, stop = {stop}")


    hash_selfish = [h0, h1]
    # zeta = [zeta1, zeta2]


    sim = Simulator(n, z0, ttx, I, hash_selfish, save_Events=save, stop_condition=stop)
    sim.checkFolder()
    sim.simulate()
    # sim.drawBlockChains(save=True)
    sim.printDetails()
    # sim.printRes()
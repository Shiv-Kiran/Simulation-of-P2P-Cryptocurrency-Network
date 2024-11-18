from queue import PriorityQueue 
from numpy.random import default_rng
import networkx as nx
from utils.generators import getLatency
from collections import deque

#Global variables

EventList = PriorityQueue() # Contains all the events in the network.
seed = 0
random_gen = default_rng(seed)
Ttx = 10
maxTransactions = 100




class Peer:
    '''
    Class Peer to represent the peer in the network.
    Contains the following attributes:
    unique_id : Unique ID of the peer.
    slow : Boolean value to represent if the peer is slow or not.
    low_CPU : Boolean value to represent if the peer has low CPU or not.
    balance : Balance in the account of the peer.
    pushed_txns : Set of transactions which are already pushed into a blockChain
    pending_txns : Set of transactions which are not already in a blockChain 
    neighbors : List of neighbors of the peer.
    blockchain : Blockchain of the peer.
    num_blks : Number of blocks created by the peer.
    blocksCreated : Set of blocks created by the peer.
    
    
    For Selfish peer:
    reveal_blkID : Block ID to reveal in the network.
    hidden_blks : Dictionary of hidden blocks.
    zero_state : Boolean value to represent if the peer is in zero state or not.

    '''

    def __init__(self, unique_id, slow = False, low_CPU = False, balance = 200 , neighbors = [], gensis = None, peer_type = "honest"):
        self.unique_id = unique_id
        self.slow = slow 
        self.low_CPU = low_CPU 
        self.balance = balance # Balance in the account of the peer.
        self.pushed_txns = set() # Transacxtions which are already pushed into a block.
        self.pending_txns = set() # Transactions which are not already in a block.
        self.neighbors = neighbors
        self.blockchain = BlockChain(self, gensis) # Blockchain of the peer.
        self.num_blks = 0 
        self.blocksCreated = set()
        self.peer_type = peer_type
        if peer_type != "honest":
            self.reveal_blkID = gensis.id
            self.hidden_blks  = {} 
            self.zero_state = False



    
    def createTransaction(self,event, delta_t):
        '''
        createTransaction function to create a transaction by the peer.
        

        Same Function for both honest and selfish peers.
        '''
        if self.balance <= 1:
            return
        time_s = event.timestamp
        random_neighbor = random_gen.choice(list(self.neighbors))
        txn_amount = random_gen.integers(1,self.balance)//10

        # create Transaction only if the txn_amount is less than the balance of the peer in blockChain. 
        if txn_amount < self.balance:
            txn = Transaction(peer1=self,peer2=random_neighbor, amount=txn_amount, timestamp=time_s)
            with open(f'./observations/Transactions/peer_{self.unique_id}_Transactions.txt', 'a') as f:
                f.write(f"{txn.txid}: {txn.peer1.unique_id} pays {txn.peer2.unique_id} {txn.amount} coins \n")
            with open(f'./observations/Transactions/All_Transactions.txt', 'a') as f:
                f.write(f"{txn.txid}: {txn.peer1.unique_id} pays {txn.peer2.unique_id} {txn.amount} coins \n")
                
            self.pending_txns.add(txn)
            next_time = time_s + delta_t
            EventList.put((next_time, Event(next_time, "Transaction_Gen", sender=self)))

            for peer in self.neighbors:
                if peer.unique_id == txn.peer1.unique_id or peer.unique_id == event.sender.unique_id:
                    continue
                message = 1 
                latency = getLatency(self, peer, message)
                EventList.put((time_s + latency, Event(time_s+latency, "Transaction_Rec", sender=self, receiver=peer, txn=txn)))

    def receiveTransaction(self,event):
        '''
        receiveTransaction function to receive a transaction by the peer and send it to the neighbors.

        Same Function for both honest and selfish peers.
        '''
        time_s = event.timestamp
        txn = event.txn 
        if txn not in self.pending_txns or txn in self.pushed_txns:
            self.pending_txns.add(txn)

            for peer in self.neighbors:
                if peer.unique_id == txn.peer1.unique_id or peer.unique_id == event.sender.unique_id:
                    continue
                message = 1 
                latency = getLatency(self, peer, message)
                EventList.put((time_s + latency, Event(time_s+latency, "Transaction_Rec", sender=self, receiver=peer, txn=txn)))

    def sendBlockNeighbour(self, time_s, block):
        '''
        function to send the block to the neighbors of the peer.
        '''
        for peer in self.neighbors:
            if peer.unique_id == block.creator.unique_id:
                continue
            message = len(block.txns)
            latency = getLatency(self, peer, message)
            EventList.put((time_s + latency, Event(time_s+latency, "Block_Rec", sender=self, receiver=peer, block=block)))



    def createBlock(self, event, delta_t, stop=False):
        '''
        function to create a block by the peer check for the pending transactions and create a block.
        
        Selfish Peer : Send the Block only if competing with the main Blockchain.

        '''
        if stop and self.peer_type == "honest":
            return
        if stop and self.peer_type != "honest":
            while self.reveal_blkID != self.blockchain.long_Block.id:
                self.reveal_blkID = self.hidden_blks[self.reveal_blkID]
                self.sendBlockNeighbour(event.timestamp, self.blockchain.id2blk[self.reveal_blkID])
            return

        time_s = event.timestamp 
        coinbase = Transaction(peer1=self, amount=50, timestamp=time_s, is_coinbase=True)
        newBlock = Block(time_s, self.blockchain.long_Block.id, self, coinbase=coinbase, balances=self.blockchain.long_Block.balances)

        self.blocksCreated.add(newBlock.id)


        newBlock.balances[self.unique_id] += 50
        # with open(f'./observations/Transactions/peer_{self.unique_id}_Transactions.txt', 'a') as f:
        #     f.write(f"{coinbase.txid}: {self.unique_id} mines 50 coins  \n")
        # with open(f'./observations/Transactions/All_Transactions.txt', 'a') as f:
        #     f.write(f"{coinbase.txid}: {self.unique_id} mines 50 coins  \n")
        transactions_to_remove = []

        for txn in self.pending_txns:
            if len(newBlock.txns) >= maxTransactions:
                break
            if txn.amount > newBlock.balances[txn.peer1.unique_id]:
                continue
            newBlock.balances[txn.peer1.unique_id] -= txn.amount
            newBlock.balances[txn.peer2.unique_id] += txn.amount
            newBlock.txns.append(txn)
            self.pushed_txns.add(txn)
            transactions_to_remove.append(txn)

        # Remove the processed transactions from pending_txns after iteration
        for txn in transactions_to_remove:
            self.pending_txns.remove(txn)

        self.balance = newBlock.balances[self.unique_id]
        self.blockchain.id2blk[newBlock.id] = newBlock
        self.blockchain.bcTree.add_edge(newBlock.pblkid, newBlock.id)
        self.blockchain.arrival_time[newBlock.id] = time_s
        self.blockchain.long_Block = newBlock
        # print(self.unique_id, " created block ", newBlock.id, " with parent ", newBlock.pblkid, " at time ", time_s, len(newBlock.txns), "at Peer ", self.unique_id)
        if self.peer_type == "honest":
            self.sendBlockNeighbour(time_s, newBlock)

        # print("Balances ", newBlock.balances)
        else : 

            '''
            Store in blocks generated in hidden_blks 
            Check zero_state and send the block to the network if competing with the main chain.
            
            '''
            self.hidden_blks[newBlock.pblkid] = newBlock.id
            if self.zero_state:
                # We are competing with other equally length chain
                self.sendBlockNeighbour(time_s, newBlock)
                self.zero_state = False
            
        EventList.put((time_s + delta_t, Event(time_s + delta_t, "Block_Gen", generator=self)))



    def receiveBlock(self, event, stop=False):
        '''
        Check if current received Block has a parent in the blockchain. If not, add it to the orphan list.
        If the parent is present, add the block to the blockchain and process the orphan list.

        Selfish Peer: 
        1. Check if the block is valid or not.
        2. If valid, add the block to the blockchain.
        3. Check for lengths and send the blocks to the network accordingly.

        '''
        time_s = event.timestamp
        block = event.block
        # if self.peer_type == "honest" and stop:
        #     return
        if block.id in self.blockchain.id2blk_orphan or block.id in self.blockchain.id2blk:
            return
        self.blockchain.arrival_time[block.id] = time_s
        if block.pblkid not in self.blockchain.id2blk:
            self.blockchain.id2blk_orphan[block.id] = block
            return

        # validate the transactions in the block by checking the balances with its parent block.
        temp_balances = self.blockchain.id2blk[block.pblkid].balances.copy()

        # verifying block 
        for txn in block.txns:
            if txn.peer2 is None:
                temp_balances[txn.peer1.unique_id] += txn.amount
                continue
            temp_balances[txn.peer1.unique_id] -= txn.amount
            temp_balances[txn.peer2.unique_id] += txn.amount
        
        # invalid block return 
        if temp_balances != block.balances:
            return 
        
        
        # there is new childs present in orphan 
        processOrphans = deque() 
        prevBlock = block 
        processOrphans.append(prevBlock)
        while len(processOrphans) > 0:
            blk = processOrphans.popleft()
            self.blockchain.id2blk[blk.id] = blk
            self.blockchain.arrival_time[prevBlock.id] = time_s
            self.blockchain.bcTree.add_edge(blk.pblkid, blk.id)
            if blk.length > prevBlock.length:
                prevBlock = blk
            if self.peer_type == "honest":
                self.sendBlockNeighbour(time_s, blk)


            orphans_to_remove = []

            for child in self.blockchain.id2blk_orphan.values():
                if child.pblkid == blk.id:
                    processOrphans.append(child)
                    orphans_to_remove.append(child.id)

            # Remove the orphan blocks from the dictionary after iteration
            for orphan_id in orphans_to_remove:
                self.blockchain.id2blk_orphan.pop(orphan_id)
        
        # check for fork in the blockchain
        if self.peer_type == "honest":
            if prevBlock.length > self.blockchain.long_Block.length:
                # if prevBlock.pblkid != self.blockchain.long_Block.id:
                #     print("Fork")
                self.blockchain.long_Block = prevBlock
                self.blockchain.len = prevBlock.length
        else :
            # After stopping just send your own blocks 
            if stop:
                while self.reveal_blkID != self.blockchain.long_Block.id:
                    self.reveal_blkID = self.hidden_blks[self.reveal_blkID]
                    self.sendBlockNeighbour(time_s, self.blockchain.id2blk[self.reveal_blkID])
                return

            # case of new block in state 2. release to the network
            if prevBlock.length == self.blockchain.long_Block.length -1:
                while self.reveal_blkID != self.blockchain.long_Block.id:
                    self.reveal_blkID = self.hidden_blks[self.reveal_blkID]
                    self.sendBlockNeighbour(time_s, self.blockchain.id2blk[self.reveal_blkID])
            # case when new > old O to O or O' to O 
            elif prevBlock.length > self.blockchain.long_Block.length:
                if self.zero_state:
                    self.zero_state = False
                self.blockchain.long_Block = prevBlock
                self.blockchain.len = prevBlock.length
                self.reveal_blkID = prevBlock.id
            # case when 1 to 0'
            elif prevBlock.length == self.blockchain.long_Block.length and self.blockchain.long_Block.creator.unique_id == self.unique_id:
                self.zero_state = True
                while self.reveal_blkID != self.blockchain.long_Block.id:
                    self.reveal_blkID = self.hidden_blks[self.reveal_blkID]
                    self.sendBlockNeighbour(time_s, self.blockchain.id2blk[self.reveal_blkID])
            # n to n-1 just reveal 1 block if your chain len decreases 
            else: 
                while self.blockchain.id2blk[self.reveal_blkID].length < prevBlock.length:
                    self.reveal_blkID = self.hidden_blks[self.reveal_blkID]
                    self.sendBlockNeighbour(time_s, self.blockchain.id2blk[self.reveal_blkID])
                





class BlockChain: 
    def __init__(self, creator, gen):
        self.creator = creator
        self.long_Block = gen
        self.id2blk_orphan = {}
        self.id2blk = {gen.id: gen}
        self.arrival_time = {gen.id: 0}
        self.len = 1
        self.bcTree = nx.DiGraph()


    




# a class called Transaction.
txID = 10
class Transaction:
    '''
    Transaction class to represent the transaction in the network.
    '''
    def __init__(self, peer1=None, peer2=None, amount=None, timestamp=None, is_coinbase=False):
        # self.txid = txid #Transaction ID
        global txID
        self.txid = txID
        txID += 1 
        self.peer1 = peer1 #Peer which is paying.
        self.peer2 = peer2 #Peer which is receiving.
        self.amount = amount #Amount transferred from Peer1 to Peer2.
        self.timestamp = timestamp #Timestamp of this transaction.
        self.is_coinbase = is_coinbase #Check if the txn is a coinbase txn or not.

    def print_txn(self):
        if(self.peer2 is None):
            self.is_coinbase = True
        if(self.is_coinbase):
            return str(self.txid) + ":" + " " + self.peer1.unique_id + " mines " + " " + self.amount + " coins"
        else:
            return str(self.txid) + ":" + " " + self.peer1.unique_id + " pays " + self.peer1.unique_id + " " + self.amount + " coins"


class Event:
    '''
    Event class to simulate the event Loop in BlockChain Network 
    
    '''
    def __init__(self, timestamp, event_type, sender=None, receiver=None, generator = None,  txn=None, block=None, blockID=None):
        self.timestamp = timestamp
        self.event_type = event_type
        self.txn = txn
        self.block = block
        self.sender = sender
        self.receiver = receiver
        self.generator = generator
        self.blockID = blockID


blockId = 1
class Block: 
    '''
    Block class to represent the block in the network.
    Contians the following attributes:
    id : Unique ID of the block.
    length : Length of the block.
    vtime : Virtual time of the block.
    pblkid : Parent block ID of the block.
    creator : Creator of the block.
    txns : List of transactions in the block.
    balances : List of balances of upto the Block in the blockchain.
    '''
    def __init__(self, vtime, pblkid, creator, coinbase, txns= None, gen=False, balances = []):
        global blockId
        if gen:
            self.id = 0
            self.length = 1
            self.pblk = None
        else:
            # print("Block ID: ", blockId, " Parent Block ID: ", creator.blockchain.id2blk[pblkid].id, " created by Peer_" + str(creator.unique_id))
            self.id = blockId 
            self.length = creator.blockchain.id2blk[pblkid].length + 1
            blockId += 1   
            self.pblk = creator.blockchain.id2blk[pblkid]
        self.vtime = vtime
        self.pblkid = pblkid
        self.creator = creator
        self.txns = []
        self.txns.append(coinbase)
        # make a deep copy of the balances of the parent block
        self.balances = balances.copy()
        

def total_blocks():
    return blockId



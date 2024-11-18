from numpy import random 

# create a seed random 
seed = 0
random.seed(seed)


def ExponentialDist(rate):
    # introduce a seeded random dist 
    return lambda: random.exponential(rate)


def getHashDist( Peers, I,hash_selfish, min=1, max=10 ):
    '''
    Helpler function to get the hash distribution for the peers
    '''

    n = len(Peers)
    val = min*(1 - hash_selfish[0] - hash_selfish[1]) / (n -2 )
    honestHash = ExponentialDist(I/val)
    return honestHash

def UniformDist(low, high):
    '''
    labmda function to generate values from uniform distribution.
    '''
    return lambda: random.uniform(low, high)


def getLatency(peerX, peerY, message):
    '''
    Hellper function to get the latency between the peers.
    '''
    if( not peerX.slow and not peerY.slow):
        cij = 100 # mb
    else:
        cij = 5
    dij = random.exponential(96.0/ (cij)) #msec
    rhoij = random.uniform(10.0, 500.0) #msec
    return rhoij + (message*8)/(cij) + dij
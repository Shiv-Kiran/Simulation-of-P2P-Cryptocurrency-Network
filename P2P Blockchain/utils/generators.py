from numpy import random 

# create a seed random 
seed = 0
random.seed(seed)


def ExponentialDist(rate):
    # introduce a seeded random dist 
    return lambda: random.exponential(rate)


def getHashDist( Peers, I, min=1, max=10):
    '''
    Helpler function to get the hash distribution for the peers.
    '''
    high_count = 0 
    n = len(Peers)
    for peer in Peers:
        if not peer.low_CPU:
            high_count += 1
    val1 = min / (n + 9 * high_count)
    val2 = max / (n + 9 * high_count)
    for peer in Peers:
        if peer.low_CPU:
            peer.hp = val1
        else:
            peer.hp = val2
    slowHash = ExponentialDist(I/val1)
    fastHash = ExponentialDist(I/val2)
    return slowHash, fastHash

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
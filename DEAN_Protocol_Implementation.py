import hashlib
import datetime as date
import random
import time
import threading

class Transaction:
    def __init__(self, sender, recipient, amount, signature=None):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.signature = signature

    def to_dict(self):
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "signature": self.signature,
        }

    def sign(self, signature):
        self.signature = signature

class Block:
    def __init__(self, index, timestamp, transactions, previous_hash, nonce=0, network_node=None):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.network_node = network_node  # Link block to a network node
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_header = str(self.index) + str(self.timestamp) + str(self.previous_hash) + str(self.nonce) + str(self.network_node)
        block_transactions = "".join([str(tx.to_dict()) for tx in self.transactions])
        hash_string = block_header + block_transactions
        return hashlib.sha256(hash_string.encode()).hexdigest()

    def mine_block(self, difficulty):
        target = '0' * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        print("Block mined: ", self.hash)

class SimpleBlockchain:
    def __init__(self, difficulty=2):
        self.chain = [self.create_genesis_block()]
        self.difficulty = difficulty
        self.pending_transactions = []
        self.mining_reward = 10

    def create_genesis_block(self):
        return Block(0, date.datetime.now(), [], "0", network_node=None)

    def mine_pending_transactions(self, mining_reward_address):
        print("Starting to mine pending transactions...")
        if not self.pending_transactions:
            print("No transactions to mine.")
            return

        valid_transactions = [tx for tx in self.pending_transactions if self.validate_transaction(tx)]
        if not valid_transactions:
            print("No valid transactions to mine.")
            return

        print(f"Mining a block with {len(valid_transactions)} transactions.")
        block = Block(len(self.chain), date.datetime.now(), valid_transactions, self.get_latest_block().hash)
        block.mine_block(self.difficulty)

        print(f"Block successfully mined! Hash: {block.hash}")
        self.chain.append(block)
        self.pending_transactions = [Transaction(None, mining_reward_address, self.mining_reward)]

    def get_latest_block(self):
        return self.chain[-1]

    def create_transaction(self, transaction):
        self.pending_transactions.append(transaction)

    def validate_transaction(self, transaction):
        if transaction.amount <= 0:
            return False
        if not transaction.sender or not transaction.recipient:
            return False
        return True

    def is_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]

            if current_block.hash != current_block.calculate_hash():
                return False
            if current_block.previous_hash != previous_block.hash:
                return False
        return True


# 2 Leader Election for Block Validation
class ScaleFreeNetwork:
    def __init__(self, initial_nodes=3):
        self.nodes = list(range(initial_nodes))
        self.edges = [(i, j) for i in self.nodes for j in self.nodes if i != j]
        self.m = 1  # Default value of m, dynamically adjusted later

    def node_degree(self, node):
        return sum(1 for edge in self.edges if node in edge)

    def adjust_m_based_on_network_conditions(self):
        print("Adjusting 'm' based on network conditions...")
        network_size = len(self.nodes)
        average_degree = sum(self.node_degree(node) for node in self.nodes) / network_size
        target_degree = 8  # Example target connectivity

        if average_degree < target_degree:
            self.m += 1
        elif average_degree > target_degree and self.m > 1:
            self.m -= 1
        # Ensure 'm' stays within practical limits
        self.m = max(1, min(self.m, 5))

        # Print the current value of 'm' after adjustment
        print(f"Value of 'm' adjusted to: {self.m}")

    def add_node(self):
        new_node_id = len(self.nodes)
        self.nodes.append(new_node_id)
        self.adjust_m_based_on_network_conditions()  # Adjust 'm' dynamically based on network conditions

        potential_edges = [(new_node_id, node) for node in self.nodes if node != new_node_id]
        chosen_edges = random.choices(potential_edges, weights=[self.node_degree(node) for node in self.nodes if node != new_node_id], k=self.m)
        self.edges.extend(chosen_edges)
        return new_node_id

    def elect_leaders(self):
        degrees = {node: 0 for node in self.nodes}
        for edge in self.edges:
            degrees[edge[0]] += 1
            degrees[edge[1]] += 1
        sorted_nodes = sorted(degrees, key=degrees.get, reverse=True)
        return sorted_nodes[:max(3, len(self.nodes) // 10)]

class Blockchain(SimpleBlockchain):
    def __init__(self, difficulty=2):
        super().__init__(difficulty)
        print("Initializing Blockchain with a scale-free network...")
        self.network = ScaleFreeNetwork()
        self.adapt_difficulty()  # Adapt initial difficulty based on network conditions
    
    def adapt_difficulty(self):
        self.difficulty = max(2, min(self.difficulty, len(self.network.nodes) // 10))
        print(f"Difficulty adjusted to {self.difficulty}.")

    def mine_pending_transactions(self, mining_reward_address):
        start_time = time.time()
        super().mine_pending_transactions(mining_reward_address)
        end_time = time.time()
        print(f"Mining took {end_time - start_time} seconds.")

    def validate_block_with_leaders(self, block):
        # Leader election and block validation
        leaders = self.network.elect_leaders()
        return any(leader == block.network_node for leader in leaders)

    def mine_in_parallel(self, mining_reward_address):
        # Parallel block mining
        new_node_id = self.network.add_node()
        leaders = self.network.elect_leaders()
        if new_node_id in leaders:
            self.mine_pending_transactions(mining_reward_address)
            self.chain[-1].network_node = new_node_id


    @staticmethod
    def perform_measurement(blockchain):
        # Logic to measure performance
        start_time = time.time()
        for _ in range(100):
            blockchain.create_transaction(Transaction("Sender", "Recipient", 10))
            blockchain.mine_pending_transactions("Miner")
        end_time = time.time()
        throughput = 100 / (end_time - start_time)
        latency = (end_time - start_time) / 100
        return throughput, latency

    def measure_performance(self):
        print("Measuring performance with 100 transactions...")
        result = Blockchain.perform_measurement(self)  # Use the class name directly to avoid recursion
        print(f"Throughput: {result[0]} transactions/second, Latency: {result[1]} seconds/transaction")


    @staticmethod
    def simulate_parallel_mining(blockchain):
        # Simulate parallel execution for mining
        threads = []
        for _ in range(len(blockchain.network.elect_leaders())):
            thread = threading.Thread(target=blockchain.mine_in_parallel, args=("Miner",))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()

def test_network_performance():
    blockchain = Blockchain(difficulty=2)
    # Simulate network growth
    for _ in range(50):
        blockchain.network.add_node()
        if random.random() < 0.5:  # Simulate transaction creation
            blockchain.create_transaction(Transaction("Mohsin", "Ali", random.randint(1, 100)))

    # Mine some blocks to process transactions
    for _ in range(10):
        blockchain.mine_pending_transactions("MinerAddress")

    # Measure network performance
    blockchain.measure_performance()

    # Validate dynamic adjustment of 'm'
    print(f"Final value of 'm': {blockchain.network.m}")
    assert blockchain.network.m >= 1 and blockchain.network.m <= 5, "m adjusted beyond limits"

test_network_performance()


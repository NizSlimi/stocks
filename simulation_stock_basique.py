import simpy
import numpy as np
import matplotlib.pyplot as plt


def warehouse_run(env, order_cutoff, order_target):
    global inventory, balance, num_ordered

    inventory = order_target
    balance = 0.
    num_ordered = 0

    while True:
        interarrival = generate_interarrival()
        yield env.timeout(interarrival)
        balance -= inventory*2*interarrival #holding costs = 2
        demand = generate_demand()
        if demand < inventory:
            balance += 100*demand #prix de vente 100
            inventory -= demand
            print("{:.2f}, sold {}".format(env.now, demand))
        else:
            balance += 100*inventory
            inventory = 0
            print("{:.2f}, sold {} (out of stock)".format(env.now, inventory))


        if inventory < order_cutoff and num_ordered == 0:
            env.process(handle_order(env, order_target))

def handle_order(env, order_target):
    global inventory, balance, num_ordered

    num_ordered = order_target - inventory
    print("{:.2f}, place order of {}".format(env.now, num_ordered))
    balance -= 50*num_ordered #couts achat
    yield env.timeout(2.) # 2 jours lead time appro
    inventory += num_ordered
    num_ordered = 0
    print("{:.2f}, order recieved. {} in inventory".format(env.now, inventory))



def generate_interarrival():
    return np.random.exponential(1./5)

def generate_demand():
    return np.random.randint(1,5)


def observe(env, obs_time, inventory_level):
    global inventory

    while True:
        obs_time.append(env.now)
        inventory_level.append(inventory)
        yield env.timeout(0.1)


def run_simulation(print_=False):
    np.random.seed(0)
    env = simpy.Environment()
    env.process(warehouse_run(env, 5,40))

    obs_time = []
    inventory_level = []

    env.process(observe(env, obs_time, inventory_level))
    env.run(until=10.)

    if print_ == True:
        fig, ax = plt.subplots()
        ax.step(obs_time,inventory_level)
        ax.set_xlabel('Time in days')
        ax.set_ylabel('Inventory level')
        plt.show()

if __name__ == '__main__':
    run_simulation(print_=True)

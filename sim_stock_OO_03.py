import simpy
import numpy as np
import matplotlib.pyplot as plt

class warehouse(object):

    # initialize warehouse object
    def __init__(self, env, initial_inventory, inventory_policy, customer):
        self.env = env

        #Product inventory policy
        self.reorder_point = dict(zip(inventory_policy['product_name'],inventory_policy['reorder_point']))
        self.target_inv = dict(zip(inventory_policy['product_name'],inventory_policy['target_inv']))
        self.lead_time = dict(zip(inventory_policy['product_name'],inventory_policy['lead_time']))
        self.list_products = initial_inventory.keys()

        #Inventory level
        self.on_hand_inv = initial_inventory
        self.order_qty = {k:0 for k in initial_inventory.keys()}

        #Monitoring
        self.onHandMonitoring = {k:[] for k in initial_inventory.keys()}
        self.obs_time = {k:[] for k in initial_inventory.keys()}

        #Custoemr
        self.customer = customer

        # start processes
        self.env.process(self.serve_customer())
        self.env.process(self.chek_inventory_and_order())


    # process to serve Customer
    def serve_customer(self):
        while True:
            yield self.env.timeout(1)
            demand = self.customer.demand
            for p,d in demand.items():
                if d < self.on_hand_inv[p]:
                    self.on_hand_inv[p] -= d
                    print("{:.2f}, sold {} of {}".format(self.env.now, d,p))
                else:
                    print("{:.2f}, sold {} (out of stock) of {}".format(self.env.now, self.on_hand_inv[p],p))
                    self.on_hand_inv[p] = 0

    # process to place order
    def chek_inventory_and_order(self):
        while True:
            for p in self.list_products:
                self.onHandMonitoring[p].append(self.on_hand_inv[p])
                self.obs_time[p].append(self.env.now)
                yield self.env.timeout(1.0)
                if self.on_hand_inv[p] <= self.reorder_point[p] and self.order_qty[p] == 0:
                    self.order_qty[p] = self.target_inv[p] - self.on_hand_inv[p]
                    print("{:.2f}, place order of {} of {}".format(self.env.now, self.order_qty[p],p))
                    yield self.env.timeout(self.lead_time[p])
                    self.on_hand_inv[p] += self.order_qty[p]
                    self.order_qty[p] = 0
                    print("{:.2f}, order recieved. {} in inventory of {}".format(self.env.now, self.on_hand_inv[p],p))

class customer(object):
    """docstring for customer."""

    def __init__(self, env, demand_parameters):
        self.env = env

        #Product
        self.interarrival = dict(zip(demand_parameters['product_name'],demand_parameters['interarrival']))
        self.demand_param = dict(zip(demand_parameters['product_name'],demand_parameters['mean']))
        self.demand = {k:0 for k in demand_parameters['product_name']}
        self.list_products = demand_parameters['product_name']

        self.env.process(self.order())

    def order(self):
        while True:
            for p in self.list_products:
                yield self.env.timeout(self.interarrival[p])
                self.demand[p] = np.random.randint(1,self.demand_param[p])
                print("{:.2f}, demand {} of {}".format(self.env.now, self.demand[p],p))



def run_simulation(print_=False):
    np.random.seed(0)
    env = simpy.Environment()

    #Data
    inventory_policy = {
        'product_name':['P1','P2'],
        'lead_time':[4,2.],
        'target_inv':[100,40],
        'reorder_point':[15,5]
    }

    initial_inventory = {
    'P1':10,
    'P2':40
    }

    demand_parameters = {
        'product_name':['P1','P2'],
        'interarrival':[1,1],
        'mean':[7,5]
    }

    c = customer(env, demand_parameters)
    s = warehouse(env, initial_inventory, inventory_policy, c)
    env.run(until=100.)


    if print_ == True:
        fig, ax = plt.subplots()
        for p in initial_inventory.keys():
            ax.step(s.obs_time[p],s.onHandMonitoring[p])
        ax.set_xlabel('Time in days')
        ax.set_ylabel('Inventory level')
        plt.show()


if __name__ == '__main__':
    run_simulation(print_=True)

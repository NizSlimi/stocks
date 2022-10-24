import simpy
import numpy as np
import matplotlib.pyplot as plt

class warehouse(object):

    # initialize warehouse object
    def __init__(self, env, initial_inv, reorder_point, target_inv, lead_time, customer):
        self.env = env

        #Product
        self.on_hand_inv = initial_inv
        self.reorder_point = reorder_point
        self.target_inv = target_inv
        self.lead_time = lead_time
        self.order_qty = 0

        #Monitoring
        self.onHandMonitoring = []
        self.obs_time = []

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
            if demand < self.on_hand_inv:
                self.on_hand_inv -= demand
                print("{:.2f}, sold {}".format(self.env.now, demand))
            else:
                print("{:.2f}, sold {} (out of stock)".format(self.env.now, self.on_hand_inv))
                self.on_hand_inv = 0

    # process to place order
    def chek_inventory_and_order(self):
        while True:
            self.onHandMonitoring.append(self.on_hand_inv)
            self.obs_time.append(self.env.now)
            yield self.env.timeout(1.0)
            if self.on_hand_inv <= self.reorder_point and self.order_qty == 0:
                self.order_qty = self.target_inv - self.on_hand_inv
                print("{:.2f}, place order of {}".format(self.env.now, self.order_qty))
                yield self.env.timeout(self.lead_time)
                self.on_hand_inv += self.order_qty
                self.order_qty = 0
                print("{:.2f}, order recieved. {} in inventory".format(self.env.now, self.on_hand_inv))

class customer(object):
    """docstring for customer."""

    def __init__(self, env, interarrival, demand_param):
        self.env = env

        #Product
        self.interarrival = interarrival
        self.demand_param = demand_param
        self.demand = 0

        self.env.process(self.order())

    def order(self):
        while True:
            yield self.env.timeout(self.interarrival)
            self.demand = np.random.randint(1,self.demand_param)
            print("{:.2f}, demand {}".format(self.env.now, self.demand))



def run_simulation(print_=False):
    np.random.seed(0)
    env = simpy.Environment()

    c = customer(env, 1, 5)
    s = warehouse(env, 40, 5, 40, 2., c)
    env.run(until=40.)

    print(type(env.timeout(1.0)))
    print(type(s.serve_customer()))


    if print_ == True:
        fig, ax = plt.subplots()
        ax.step(s.obs_time,s.onHandMonitoring)
        ax.set_xlabel('Time in days')
        ax.set_ylabel('Inventory level')
        plt.show()


if __name__ == '__main__':
    run_simulation(print_=True)

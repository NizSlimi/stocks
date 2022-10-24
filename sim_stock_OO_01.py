import simpy
import numpy as np
import matplotlib.pyplot as plt

class warehouse(object):

    # initialize warehouse object
    def __init__(self, env, initial_inv, reorder_point, target_inv, lead_time):
        self.env = env
        self.on_hand_inv = initial_inv
        self.reorder_point = reorder_point
        self.target_inv = target_inv
        self.lead_time = lead_time
        self.order_qty = 0
        self.onHandMonitoring = []
        self.obs_time = []

        # start processes
        self.env.process(self.serve_customer())
        self.env.process(self.chek_inventory_and_order())


    # process to serve Customer
    def serve_customer(self):
        while True:
            interarrival = 1 #np.random.exponential(1./1)
            yield self.env.timeout(interarrival)
            demand = np.random.randint(1,5)
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




def run_simulation(print_=False):
    np.random.seed(0)
    env = simpy.Environment()

    s = warehouse(env, 40, 5, 40, 2.)
    env.run(until=40.)

    print(type(s))
    print(type(s.serve_customer()))
    print(s.order_qty)
    print(type(env.timeout(1.0)))


    if print_ == True:
        fig, ax = plt.subplots()
        ax.step(s.obs_time,s.onHandMonitoring)
        ax.set_xlabel('Time in days')
        ax.set_ylabel('Inventory level')
        plt.show()


if __name__ == '__main__':
    run_simulation(print_=True)

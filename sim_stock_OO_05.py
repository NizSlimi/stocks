import simpy
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

class new_order(object):
    """
    Commande d'approvisionnement d'un entrepôt vers l'amont
    """

    def __init__(self, requester, order_qty):
        self.requester = requester
        self.orderQty = order_qty

class warehouse(object):
    """
    Un entrepôt du réseau de distribution
    """

    # initialize warehouse object
    def __init__(self, env, id, is_source, initial_inventory, inventory_policy, upstream_warehouse, customer):
        self.env = env

        #Warehouse caracteristics
        self.name = "Entrepôt " +str(id)
        self.is_source = is_source
        self.upstream_warehouse = upstream_warehouse

        #Product inventory policy
        self.reorder_point = inventory_policy['reorder_point']
        self.target_inv = inventory_policy['target_inv']
        self.lead_time = inventory_policy['lead_time']
        #self.list_products = initial_inventory.keys()

        #Inventory level
        self.on_hand_inv = initial_inventory
        self.inventory_position = initial_inventory
        self.order_qty = 0
        self.orders = []

        #Monitoring
        self.onHandMonitoring = []
        self.obs_time = []

        #Custoemr
        self.customer = customer

        # start processes
        self.env.process(self.check_inventory())
        self.env.process(self.prepare_replenishment())
        if self.customer != None:
            self.env.process(self.serve_customer())


    # process to serve Customer
    def serve_customer(self):
        while True:
            yield self.env.timeout(1.)
            demand = self.customer.demand
            shipment = min(demand, self.on_hand_inv)
            self.on_hand_inv -= shipment
            self.inventory_position -= shipment
            print("{:.2f}, sold {}".format(self.env.now, demand))



    # process to place order
    def check_inventory(self):
        while True:
            self.onHandMonitoring.append(self.on_hand_inv)
            self.obs_time.append(self.env.now)
            yield self.env.timeout(1.0)

            if self.inventory_position <= self.reorder_point:
                self.order_qty = self.target_inv - self.on_hand_inv
                order = new_order(self, self.order_qty)
                if not self.is_source:
                    self.upstream_warehouse.orders.append(order)
                    self.inventory_position += self.order_qty
                    print("{:.2f}, place order of {}".format(self.env.now, self.order_qty))
                else:
                    yield self.env.timeout(self.lead_time)
                    self.on_hand_inv += order.orderQty
                    order.orderQty = 0
                    print("{:.2f}, order recieved. {} in inventory".format(self.env.now, self.on_hand_inv))

    #prepare replenishment
    def prepare_replenishment(self):
        while True:
            if len(self.orders) > 0:
                order = self.orders.pop(0)
                shipment = min(order.orderQty, self.on_hand_inv)

                if not self.is_source:
                    self.inventory_position -= shipment
                    self.on_hand_inv -= shipment

                remaining_order = order.orderQty - shipment
                if remaining_order > 0:
                    while not self.on_hand_inv >= remaining_order:
                        yield self.env.timeout(1.0)
                    self.inventory_position -= remaining_order
                    self.on_hand_inv -= remaining_order
                self.env.process(self.ship(order.orderQty, order.requester))
            else:
                yield self.env.timeout(1.)

    #process to deliver replenishment
    def ship(self, qty, requester):
        lead_time = self.lead_time
        yield self.env.timeout(lead_time)
        requester.on_hand_inv += qty
        print("{:.2f}, delivery of {}".format(self.env.now, qty))


class customer(object):
    """docstring for customer."""

    def __init__(self, env, demand_parameters):
        self.env = env

        #Product
        self.interarrival = demand_parameters['interarrival']
        self.demand_param = demand_parameters['mean']
        self.demand = 0
        #self.list_products = demand_parameters['product_name']

        self.env.process(self.order())

    def order(self):
        while True:
            yield self.env.timeout(self.interarrival)
            self.demand = np.random.randint(1,self.demand_param)
            print("{:.2f}, demand {}".format(self.env.now, self.demand))



def run_simulation(print_=False):
    np.random.seed(0)
    env = simpy.Environment()

    #Data
    inventory_policy = {
        'lead_time':2.,
        'target_inv':50,
        'reorder_point':15
    }

    initial_inventory = 30

    inventory_policy_1 = {
        'lead_time':1.,
        'target_inv':40,
        'reorder_point':8
    }

    initial_inventory_1 = 30

    inventory_policy_cdc = {
        'lead_time':20,
        'target_inv':600,
        'reorder_point':45
    }

    initial_inventory_cdc = 300

    inventory_policy_dc = {
        'lead_time':6,
        'target_inv':400,
        'reorder_point':150
    }

    initial_inventory_dc = 100

    demand_parameters = {
        'interarrival':1,
        'mean':7
    }

    demand_parameters_2 = {
        'interarrival':1,
        'mean':10
    }

    c = customer(env, demand_parameters)
    c2 = customer(env, demand_parameters_2)
    cdc = warehouse(env, 0, 1, initial_inventory_cdc, inventory_policy_cdc, None, None)
    dc = warehouse(env, 1, 0, initial_inventory_dc, inventory_policy_dc, cdc, None)
    dc2 = warehouse(env, 1, 0, initial_inventory, inventory_policy, dc, c2)
    dc3 = warehouse(env, 1, 0, initial_inventory_1, inventory_policy_1, dc, c)

    env.run(until=150.)


    if print_ == True:
        sns.set_style("darkgrid")
        fig, axs = plt.subplots(3)
        axs[1].step(dc2.obs_time,dc2.onHandMonitoring)
        axs[2].step(dc3.obs_time,dc3.onHandMonitoring)
        axs[0].step(dc.obs_time,dc.onHandMonitoring)
        axs[1].set_xlabel('Time in days')
        axs[0].set_ylabel('Inventory level')
        plt.show()


if __name__ == '__main__':
    run_simulation(print_=True)

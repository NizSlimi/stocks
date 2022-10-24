import simpy
import numpy as np
import matplotlib.pyplot as plt

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
        self.reorder_point = dict(zip(inventory_policy['product_name'],inventory_policy['reorder_point']))
        self.target_inv = dict(zip(inventory_policy['product_name'],inventory_policy['target_inv']))
        self.lead_time = dict(zip(inventory_policy['product_name'],inventory_policy['lead_time']))
        self.list_products = initial_inventory.keys()

        #Inventory level
        self.on_hand_inv = initial_inventory
        self.inventory_position = initial_inventory
        self.order_qty = {k:0 for k in initial_inventory.keys()}
        self.orders = {k:[] for k in initial_inventory.keys()}

        #Monitoring
        self.onHandMonitoring = {k:[] for k in initial_inventory.keys()}
        self.obs_time = {k:[] for k in initial_inventory.keys()}

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
            for p,d in demand.items():
                shipment = min(d, self.on_hand_inv[p])
                self.on_hand_inv[p] -= shipment
                self.inventory_position[p] -= shipment
                print("{:.2f}, sold {} of {}".format(self.env.now, d,p))



    # process to place order
    def check_inventory(self):
        while True:
            for p in self.list_products:
                self.onHandMonitoring[p].append(self.on_hand_inv[p])
                self.obs_time[p].append(self.env.now)
            yield self.env.timeout(1.0)

            for p in self.list_products:
                if self.inventory_position[p] <= self.reorder_point[p]:
                    self.order_qty[p] = self.target_inv[p] - self.on_hand_inv[p]
                    order = new_order(self, self.order_qty[p])
                    if not self.is_source:
                        self.upstream_warehouse.orders[p].append(order)
                        self.inventory_position[p] += self.order_qty[p]
                        print("{:.2f}, place order of {} of {}".format(self.env.now, self.order_qty[p],p))
                    else:
                        yield self.env.timeout(self.lead_time[p])
                        self.on_hand_inv[p] += order.orderQty
                        print("{:.2f}, order recieved. {} in inventory of {}".format(self.env.now, self.on_hand_inv[p],p))

    #prepare replenishment
    def prepare_replenishment(self):
        while True:
            for p in self.list_products:
                test = 0
                if len(self.orders[p]) > 0:
                    test += 1
            if test > 0:
                for p in self.list_products:
                    if len(self.orders[p]) > 0:
                        order = self.orders[p].pop(0)
                        shipment = min(order.orderQty, self.on_hand_inv[p])

                    if not self.is_source:
                        self.inventory_position[p] -= shipment
                        self.on_hand_inv[p] -= shipment

                    remaining_order = order.orderQty - shipment
                    if remaining_order > 0:
                        while not self.on_hand_inventory[p] >= remaining_order:
                            yield self.env.timeout(1.0)
                        if not self.is_source:
                            self.inventory_position[p] -= remaining_order
                            self.on_hand_inv[p] -= remaining_order
                self.env.process(self.ship(order.orderQty, order.requester))
            else:
                yield self.env.timeout(1.)

    #process to deliver replenishment
    def ship(self, qty, requester):
        lead_time = 2.
        yield self.env.timeout(lead_time)
        for p in self.list_products:
            requester.on_hand_inv[p] += qty
            print("{:.2f}, delivery of {} of {}".format(self.env.now, qty,p))


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
        'lead_time':[2.,2.],
        'target_inv':[100,40],
        'reorder_point':[15,5]
    }

    initial_inventory = {
    'P1':10,
    'P2':40
    }

    inventory_policy_cdc = {
        'product_name':['P1','P2'],
        'lead_time':[10,30],
        'target_inv':[800,600],
        'reorder_point':[45,20]
    }

    initial_inventory_cdc = {
    'P1':1000,
    'P2':800
    }

    demand_parameters = {
        'product_name':['P1','P2'],
        'interarrival':[1,1],
        'mean':[7,5]
    }

    c = customer(env, demand_parameters)
    cdc = warehouse(env, 0, 1, initial_inventory_cdc, inventory_policy_cdc, None, None)
    dc = warehouse(env, 1, 0, initial_inventory, inventory_policy, cdc, c)

    env.run(until=100.)


    if print_ == True:
        fig, axs = plt.subplots(2)
        for p in initial_inventory.keys():
            axs[1].step(dc.obs_time[p],dc.onHandMonitoring[p])

        for p in initial_inventory_cdc.keys():
            axs[0].step(cdc.obs_time[p],cdc.onHandMonitoring[p])
        axs[0].set_xlabel('Time in days')
        axs[0].set_ylabel('Inventory level')
        plt.show()


if __name__ == '__main__':
    run_simulation(print_=True)

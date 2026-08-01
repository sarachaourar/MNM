import yaml
import cmd
import argparse

###############################################################################
#
# Configuration
#
###############################################################################

#
# Command-line input
#
parser = argparse.ArgumentParser()
parser.add_argument('--config', type=str, default='config.yml')
parser.add_argument('--gold', type=float, default=1500)
parser.add_argument('--product', type=float, default=0)
args = parser.parse_args()

#
# Configuration
#
try:
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    print("File doesn't exist")
except PermissionError:
    print("No read access")
except OSError as e:
    print(f"OS error: {e}")

###############################################################################
#
# Classes
#
###############################################################################

class Port():
    """
    A Port allows to sell and purchase products.

    Attributes
    ----------
    name : str
        The name of the port
    shipping_cost : float
        the amount of gold required to bring the product from one port to another.

    Methods
    ----------
    purchase_product(amount)
        Buys product from the port.
    sell_product(amount)
        Sells product from the port.
    """

    def __init__(self, name, shipping_cost):
        """ Initialises the Mine using a name and the shipping cost.

        Parameters
        ----------
        name : str
            The name of the port.
        shipping_cost : float
            The amount of gold required to bring the product from one port to another.
        """

        self.name = name
        self.shipping_cost = shipping_cost

    def purchase_product(self, amount):
        """Method to buy product

        This method allows to buy a certain amount of products from a port.

        Parameters
        ----------
        amount : float
            The amount of product that should be bought.

        Returns
        -------
        float
            The cost of the product that was purchased.
        """

        cost = amount * (config["trading"]["costs"]["buy_cost"] + self.shipping_cost)
        return cost

    def sell_product(self, amount):
        """Method to sell product

        This method allows to sell a certain amount of product to a port.

        Parameters
        ----------
        amount : float
            The amount of product that should be sold.

        Returns
        -------
        float
            The revenue from the product that was sold.
        """

        revenue = amount * (config["trading"]["revenue"]["price"] - self.shipping_cost)
        return revenue    

class Stock():
    """
    The Stock manages your product and gold

    Attributes
    ----------
    gold : float
        The amount of gold in the stock in kilogram.
    salt : float
        the amount of product in the stock in kilogram.
    MAX_STOCK : float
        the maximum amount of product in the stock in kilogram.

    Methods
    ----------
    get_product()
        Returns the amount of product in kilogram.
    get_gold()
        Returns the amount of gold in stock.
    add_product(amount)
        Adds products to the stock (in kilogram).
    remove_product(amount)
        Removes products from the stock (in kilogram).
    add_gold(amont)
        adds gold to the stock.
    remove_gold(amount)
        removes gold from the stock.
    """

    def __init__(self, gold, product):
        """ Initialises the Stock using a default gold and product amount.

        Parameters
        ----------
        gold : float
            The initial amount of gold in the stock.
        product : float
            The initial amount of product in the stock (usually 0).
        """

        self.gold = gold
        self.product = product
        self.MAX_STOCK = config["trading"]["stock"]["max"]

    def get_product(self):
        """Returns the amount of product in stock in kilogram.

        Returns
        -------
        float
            The the amount of product currently in the stock (in kg).
        """

        return self.product

    def get_gold(self):
        """Returns the amount of gold in stock.

        Returns
        -------
        float
            The the amount of gold currently in the stock.
        """

        return self.gold

    def add_product(self, amount):
        """Method to add product to the stock.

        This method adds products to the stock if there is still enough space. If
        the amount exceeds the MAX_STOCK parameter, the product will be rejected.

        Parameters
        ----------
        amount : float
            The amount of product that should be added.
        """

        if (self.product + amount) > self.MAX_STOCK:
            raise Exception(f"You are full! You have {self.product}kg of products and can not add another {amount}kg")

        self.product += amount

    def remove_product(self, amount):
        """Method to remove product from the stock.

        This method removes products from the stock if it is in there. If the amount
        exceeds the current amount of products in stock, an exception will be
        thrown.

        Parameters
        ----------
        amount : float
            The amount of products that should be removed.
        """

        if amount > self.products:
            raise Exception(f"You can't remove {amount}kg of products from your stock, you only have {self.product}kg")

        self.product -= amount

    def add_gold(self, amount):
        """Method to add gold to the stock

        Parameters
        ----------
        amount : float
            The amount of gold that should be added.
        """

        self.gold += amount

    def remove_gold(self, amount):
        """Method to remove gold from the stock

        Parameters
        ----------
        amount : float
            The amount of gold that should be removed.
        """

        if amount > self.gold:
            raise Exception(f"Can not remove more gold than you currently have. You have {self.gold} gold")
        self.gold -= amount

###############################################################################
#
# Start of the program.
# This is the heart of the mechanism.
#
###############################################################################

if __name__ == "__main__":

    class MarisNostriMercatores(cmd.Cmd):
        intro = """
        Welcome to the Mediterranean Sea waters, governor!

        You can see your stock by typing 'list_stock'. Type 'purchase <amount> <port>'
        to purchase products from a port. For example: 'purchase 100 Algiers' to
        purchase 100kg of products from the Algiers port. Type 'sell <amount> <port>'
        to sell products to a port. For example: 'sell 100 Genoa' to sell 100kg
        of products to Genoa.
        """
        prompt = "Maris Notris Mercatores> "

        my_stock = Stock(gold = args.gold, product = args.product)
        ports = {}

        def __init__(self):
            super().__init__()
            for port in config["ports"]:
                self.ports[port] = Port(port, shipping_cost = config["trading"]["costs"]["shipping_cost"])

        def do_list_stock(self, _):
            "List your stock"
            print(f"You have {self.my_stock.get_product()}kg of products and {self.my_stock.get_gold()} gold")

        def do_purchase(self, line):
            "Purchase products from a port"
            amount, port = line.split()
            amount = int(amount)

            try:
                cost = self.ports[port].purchase_product(amount)
                self.my_stock.remove_gold(cost)
                self.my_stock.add_product(amount)
                print(f"Purchased {amount}kg of products for {cost} gold.")
            except Exception as e:
                print(e)

        def do_sell(self, line):
            "Sell products to a port"
            amount, port = line.split()
            amount = int(amount)

            try:
                revenue = self.ports[port].sell_product(amount)
                self.my_stock.remove_product(amount)
                self.my_stock.add_gold(revenue)
                print(f"Sold {amount}kg of products for {revenue} gold")
            except Exception as e:
                print(e)

        def do_exit(self, _):
            "Exit the game"
            return True

    MarisNostriMercatores().cmdloop()
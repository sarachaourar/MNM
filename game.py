import yaml
import cmd
import argparse
from interfaceGPT2 import Interface

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
parser.add_argument('--name', type=str, default='Player')
parser.add_argument('--port', type=str, default='Tripoli')
parser.add_argument('--gold', type=float, default=1500)
parser.add_argument('--goods', type=float, default=0)
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

class Port(abc.ABC):
    def __init__(self, name, player):
        self.name = name
        self.player =player

    def 

class Stock(Port):
    def __init__(self, gold, goods):
        super().__init__(name, player)
        self.gold = gold
        self.goods = goods
        self.MAX_STOCK = config["trading"]["stock"]["max"] 

    def purchase_goods(self, amount):
        """Method to buy product

        This method allows to buy a certain amount of goods from another port-city.

        Parameters
        ----------
        amount : float
            The amount of goods that should be bought.

        Returns
        -------
        float
            The cost of the goods that were purchased.
        """

        cost = amount * (config["trading"]["costs"]["buy_cost"] + self.shipping_cost)
        return cost    

    def send_goods(self, amount): 
        #SARA's note
        #This version does not take into account the fact that the sent 
        #goods might not be purchased, all goods sent are purchased in this version.
        """Method to sell product

        This method allows to send a certain amount of goods to a port.

        Parameters
        ----------
        amount : float
            The amount of goods that should be sent.

        Returns
        -------
        float
            The revenue from the goods that were sold.
        """

        revenue = amount * (config["trading"]["revenue"]["price"] - self.shipping_cost)
        return revenue

    def add_goods(self, amount):
        """Method to add goods to the port.

        This method adds products to the stock if there is still enough space. If
        the amount exceeds the MAX_STOCK parameter, the product will be rejected.

        Parameters
        ----------
        amount : float
            The amount of product that should be added.
        """

        if (self.goods + amount) > self.MAX_STOCK:
            raise Exception(f"You are full! You have {self.goods}kg of products and can not add another {amount}kg")

        self.goods += amount   

    def remove_goods(self, amount):
        """Method to remove product from the stock.

        This method removes products from the stock if it is in there. If the amount
        exceeds the current amount of products in stock, an exception will be
        thrown.

        Parameters
        ----------
        amount : float
            The amount of products that should be removed.
        """

        if amount > self.goods:
            raise Exception(f"You can't remove {amount}kg of products from your stock, you only have {self.goods}kg")

        self.goods -= amount

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

class MNM(cmd.Cmd):
    intro = """
    Welcome to the Mediterranean Sea waters, governor!

    You can see your stock by typing 'list_stock'. Type 'purchase <amount> <port>'
    to purchase products from a port. For example: 'purchase 100 Algiers' to
    purchase 100kg of products from the Algiers port. Type 'sell <amount> <port>'
    to sell products to a port. For example: 'sell 100 Genoa' to sell 100kg
    of products to Genoa.
    """
    prompt = "Maris Notris Mercatores> "

    ports = {}

    def __init__(self):
        super().__init__()

        self.player = Player(name = args.name, port = args.port)

        for i, port in enumerate(config["ports"]):
            self.ports[port] = (Port(port, gold = args.gold, goods = args.goods, shipping_cost = config["trading"]["costs"]["shipping_cost"]), "player" + str(i+1))
        print(self.ports)
        self.message = ""

    def get_stats(self):
        for port in self.ports:
            return (
                f"Port : {port}\n"
                f"Gold : {self.ports[f"{port}"][0].get_gold():.1f}\n"
                f"Goods: {self.ports[f"{port}"][0].get_goods()}\n\n"
                f"Last message:\n"
                f"{self.message}"
            )                 

    def do_player(self, line):

        for port in self.ports:
            print(self.ports)
            name, port = line.split()

        try:
            player = Player(name, port)
            self.message = (f"Player {player.name} chose the {player.port} port")
        except Exception as e:
            self.message = str(e)

    def governor():
        player.port 


    def do_exit(self, _):
        self.message = "Leaving game."
        return True

###############################################################################
#
# Program
#
###############################################################################

if __name__ == "__main__":

    game = MNM()

    gui = Interface()

    while gui.is_running():

        gui.set_stats(game.get_stats())

        gui.draw()

        command = gui.get_command()

        if command is None:
            continue

        if game.onecmd(command):
            break

        # Reload the map every turn.
        gui.set_map("assets/map.png")

    gui.close()    
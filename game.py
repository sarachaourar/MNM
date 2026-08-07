import yaml
import cmd
import argparse
import abc
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
parser.add_argument('--gold', type=float, default=1500)
parser.add_argument('--goods', type=float, default=20)
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
    def __init__(self, name, player):
        self.name = name
        self.player = player

    def does_something(self):
        pass

    def does_something(self):
        pass

class Stock():
    def __init__(self, gold, goods):
        self.gold = gold
        self.goods = goods
        self.shipping_cost = config["trading"]["costs"]["shipping_cost"]
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


        if (self.goods + amount) > self.MAX_STOCK:
            raise Exception(f"You have to increase the stock! Your maximum capacity is {self.MAX_STOCK}, you have {self.goods}kg of goods and can not add another {amount}kg")
        
        cost = amount * (config["trading"]["costs"]["buy_cost"] + self.shipping_cost)

        if (self.gold - cost) < 0:
            raise Exception(f"You do not have enough gold! This transaction costs {cost}g")
        
        self.goods += amount       
        self.gold -= cost
        return f" You have purchased {amount}kg of goods for {cost}g"  

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
        if amount > self.goods:
            raise Exception(f"You can't get {amount}kg of goods from this port, it only has {self.goods}kg")

        self.goods -= amount

        revenue = amount * (config["trading"]["revenue"]["price"] - self.shipping_cost)
        self.gold += amount
        return revenue  

           

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

        players = []

        while len(config["ports"]) != len(players):

            print("Choose you port:")
            player = input()
            if player in config["ports"]:
                print(f"You are playing as the the {player} port")
                players.append(player)
                i = config["ports"].index(player)
                config["ports"][i]
            else:
                players.append("computer")
                print("This port is not available...")
                
        for players in players:
            for port in config["ports"]:
                if port == player:
                    self.ports[port] = (Port(port, player), Stock(gold = args.gold, goods = args.goods))
                    print(self.ports)
            else:
                pass
        print(self.ports)
        self.message = ""

    def current_player(self):
        pass

    def get_stats(self):
        for port in self.ports:
            return (
                f"Port : {port}\n"
                f"Gold : {self.ports[f"{port}"][1].gold:.1f}\n"
                f"Goods: {self.ports[f"{port}"][1].goods}\n\n"
                f"Last message:\n"
                f"{self.message}"
            )                 

    def list_players(self, line):
        print("Choose your port:")
        port = line()
        print(port)
        pass

    def do_trade(self, line):
        port1, amount, port2 = line.split()
        amount = int(amount)
        self.ports[port1][1].send_goods(amount)
        self.ports[port2][1].purchase_goods(amount)
        print(f'{port1} sold {amount}kg of goods to {port2}')


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
        pass


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
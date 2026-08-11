import yaml
import cmd
import argparse
from shapely import Point
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
# Functions
#
###############################################################################  
    
def parse_point(pointstring):
    halves = pointstring.split(',')
    x = float(halves[0].lstrip('Point(')) # longitude 
    y = float(halves[1].rstrip(')')) # latitude
    point = Point(x,y)
    return point

###############################################################################
#
# Classes
#
###############################################################################

class Port():
    __slots__ = ('name', 'player', 'gold', 'coord', 'hinterland')
    def __init__(self, name, player, gold, coord, hinterland):
        self.name = name
        self.player = player
        self.coord = coord
        self.gold = gold
        self.hinterland = hinterland
        
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

        cost = amount * (config["trading"]["costs"]["buy_cost"] + config["trading"]["costs"]["shipping_cost"])

        if (self.gold - cost) < 0:
            raise Exception(f"You do not have enough gold! This transaction costs {cost}g")
        
        self.hinterland.goods += amount       
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
        if amount > self.hinterland.goods:
            raise Exception(f"You can't get {amount}kg of goods from this port, it only has {self.hinterland.goods}kg")

        self.hinterland.goods -= amount

        revenue = amount * (config["trading"]["revenue"]["price"] - config["trading"]["costs"]["shipping_cost"])
        self.gold += revenue
        return revenue  

    
class Hinterland(): #to be replaced by a GDF
    __slots__ = ('goods', 'happiness', 'population', 'size')
    def __init__(self, goods):
        self.goods = goods
        self.happiness = 100
        self.population = 20_000
    
class MNM(cmd.Cmd):

    ports = []
    available_ports = []
    player_count=0
    turn_index = 0

    def __init__(self, n_players):
        super().__init__()
        self.n_players = n_players
        
        for port in config["ports"]:
            self.available_ports.append(port)
    
    def choose_port(self, chosen_port):
        if chosen_port in self.available_ports:
            self.message = f"You are playing as the the {chosen_port} port\n"
            
            self.ports.append(Port(chosen_port,
                                   f"Player {self.player_count+1}",
                                   args.gold,
                                   parse_point(config["ports"][chosen_port]),
                                   Hinterland(args.goods)
                                   )
                              )
            self.player_count+=1
            self.available_ports.remove(chosen_port)
            
        else:
            self.mesage = "This port is not available. Choose something else..."

    def get_stats(self):
        return (
            f"Port : {self.current_port.name}\n"
            f"Gold : {self.current_port.gold}\n"
            f"Goods: {self.current_port.hinterland.goods}\n\n"
            "You can trade goods with other cities using the command trade <amount> <port>\n\n"
            f"Last message:\n"
            f"{self.message}"
        )                 

    def round(self, mess):
        self.current_turn = self.turn_index % self.n_players
        self.current_port = self.ports[self.current_turn]
        self.message = mess

    def do_trade(self, line):
        try:
            amount, port2_name = line.split()
            port1 = self.current_port
            
            port2 = None
            
            for potential_port in self.ports:
                if port2_name == potential_port.name:
                    port2 = potential_port
                    break
            
            if port2 == None:
                raise Exception(f"{port2_name} is not a valid name.")

            if port1 != port2:
                amount = int(amount)
                port1.send_goods(amount)
                port2.purchase_goods(amount)
                trade_message = f'{port1.name} sold {amount}kg of goods to {port2.name}'
                self.turn_index += 1
                self.round(trade_message)
            else:
                raise Exception("You can't trade with yourself!")
        except Exception as e:
            self.message = str(e)

###############################################################################
#
# Program
#
###############################################################################

if __name__ == "__main__":
    
    gui = Interface()
    
    n_players = None
    initial_message = """Welcome to the Mediterranean!
Your goal is to become the most powerful trading hub in the Mediterranean Sea!
How many people are playing?"""
    error_message = ""
    
    while gui.is_running() and n_players==None:
        gui.set_stats(initial_message+error_message, "Hello, governors!")

        gui.draw()
        
        n_command = gui.get_command()
        
        if n_command!=None:
            try:
                n_players = int(n_command)
                
                if n_players<0 or n_players>len(config["ports"]):
                    n_players = None
                    raise Exception()
                
            except Exception:
                error_message = f"\nPlease pick a number between 0 and {len(config["ports"])}"
            
    game = MNM(n_players)
    
    while gui.is_running() and (game.n_players != len(game.ports)):
        
        pick_message = f"""Please, pick your port by entering the name of one of the cities available on the map.
Available ports : {game.available_ports}"""

        gui.set_stats(pick_message, f"Player {game.player_count+1}")

        gui.draw()

        choice = gui.get_command()

        if choice is None:
            continue
        game.choose_port(choice)

    game.round("")    

    gui = Interface()

    while gui.is_running():

        gui.set_stats(game.get_stats(), f"{game.current_port.player}")

        gui.draw()

        command = gui.get_command()

        if command is None:
            continue

        if game.onecmd(command):
            break

        # Reload the map every turn.
        gui.set_map("assets/map.png")

    gui.close()    
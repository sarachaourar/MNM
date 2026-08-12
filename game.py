import yaml
import cmd
import argparse
import random
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

class Stock():
    def __init__(self, foreign_goods, foreign_port):
        self.foreign_port = foreign_port
        self.foreign_goods = foreign_goods
        self.max_stock = 10

    def increase_storage():
        pass

    def maintenance_cost():
        pass

class Port():
    __slots__ = ('name', 'player', 'gold', 'coord', 'hinterland', 'imported_goods')

    def __init__(self, name, player, gold, coord, hinterland):
        self.name = name
        self.player = player
        self.coord = coord
        self.gold = gold
        self.hinterland = hinterland
        self.imported_goods = {}
        for port in config["ports"]:
            if self.name == port:
                pass
            else:
                self.imported_goods[port] = Stock(foreign_goods = 0, foreign_port = port)

    def receive_goods(self, amount, port1):

        self.imported_goods[port1].foreign_goods += amount
        tax = 10
        self.gold += tax
        return tax 

    def send_goods(self, amount, port2): 
        #SARA's note
        #This version does not take into account the fact that the sent 
        #goods might not be purchased, all goods sent are purchased in this version.

        self.imported_goods[port2].foreign_goods += amount
        tax = 10
        self.gold -= tax
        return tax   

    
class Hinterland(): #to be replaced by a GDF
    __slots__ = ('goods', 'happiness', 'population', 'size')
    def __init__(self, goods):
        self.goods = goods
        self.happiness = 100
        self.population = 20_000
    
class MNM(cmd.Cmd):

    ports = []
    remaining_ports = []
    player_count=0
    turn_index = -1

    def __init__(self, n_players):
        super().__init__()
        self.n_players = n_players
        
        for port in config["ports"]:
            self.remaining_ports.append(port)
            
    def add_port_to_list(self, port_name, player_name):
        """
        Adds a port to the list
        
        It creates a Port object corresponding to the chosen port and adds it to the list of ports

        Parameters
        ----------
        port_name : str
            The name of the port to be added to the list
            
        player_name : str
            The name of the player controlling this port
        """
        
        self.ports.append(Port(port_name,
                               player_name,
                               args.gold,
                               parse_point(config["ports"][port_name]),
                               Hinterland(args.goods)
                               )
                          )

    
    def choose_port(self, chosen_port_name):
        """
        Function that allows players to pick their port
        
        It announces the player's selection, increases the player count
        and removes the chosen port from the list of remaining ports

        Parameters
        ----------
        chosen_port_name : str
            Name of the port chosen by the player
        """
        
        if chosen_port_name in self.remaining_ports:
            player_name = f"Player {self.player_count+1}"
            self.message = f"{player_name} is playing as the {chosen_port_name} port\n"
            
            self.add_port_to_list(chosen_port_name, player_name)
            
            self.player_count+=1
            self.remaining_ports.remove(chosen_port_name)
            
        else:
            self.mesage = "This port is not available. Choose something else..."

    def get_stats(self):
        """
        Function that is used to transmit stats to the GUI
        
        It prints the desired stats
        """
        text = []

        for port_key in self.current_port.imported_goods:
            text.append(f"{port_key} imported goods: {self.current_port.imported_goods[port_key].foreign_goods}")
        
        return (
            f"Port : {self.current_port.name}\n"
            f"Gold : {self.current_port.gold}\n"
            f"{text[0]}\n{text[1]}\n{text[2]}\n{text[3]}\n\n"
            "You can trade goods with other cities using the command trade <amount> <port>\n\n"
            f"Last message:\n"
            f"{self.message}"
        )                 

    def round(self):
        self.turn_index += 1
        
        self.current_turn = self.turn_index % self.n_players
        self.current_port = self.ports[self.current_turn]
        
        if self.turn_index!=0 and self.current_turn==0:
            #Computer time!!!
            computer_messages = self.message
            for computer_port_name in self.remaining_ports:
                temp_port_list = [temp_port for temp_port in self.ports if temp_port.name!=computer_port_name]
                random_port = random.choice(temp_port_list)
                random_amount = random.randint(1, 10)
                
                for potential_computer_port in self.ports:
                    if computer_port_name == potential_computer_port.name:
                        computer_port = potential_computer_port
                        break
                
                try:
                    computer_messages+=self.trade_general(computer_port, random_amount, random_port)
                except Exception as e:
                    self.message = str(e)
            
            self.message = computer_messages
                
                
    def trade_general(self, port1, amount, port2):

        if port1 != port2:
            amount = int(amount)
            port1.send_goods(amount, port2.name)
            port2.receive_goods(amount, port1.name)
            self.message = f'{port1.name} traded {amount} goods with {port2.name}\n'
            return(self.message)
        else:
            raise Exception("You can't trade with yourself!")


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

            self.trade_general(port1, amount, port2)
            self.round()
            
        except Exception as e:
            self.message = str(e)


    def do_pass(self):
        self.round()


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
Available ports : {game.remaining_ports}"""

        gui.set_stats(pick_message, f"Player {game.player_count+1}")

        gui.draw()

        choice = gui.get_command()

        if choice is None:
            continue
        game.choose_port(choice)
        
    for remaining_port_name in game.remaining_ports:
        game.add_port_to_list(remaining_port_name, "Computer")
        
    game.round()    

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
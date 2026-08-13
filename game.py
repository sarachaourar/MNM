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
    """
    A Stock allows ports to store and sort the foreign goods they traded with other ports.

    Attributes
    ----------
    foreign_port: str
        The name of the port from which the foreign good is from.
        
    foreign_goods: float
        The amount of a given foreign good from a foreign port.
    """
    def __init__(self, foreign_goods, foreign_port):
        self.foreign_port = foreign_port
        self.foreign_goods = foreign_goods

    def maintenance_cost():
        pass

class Port():
    """
    A Port manages the trading of goods between ports.

    Attributes
    ----------
    name: str
        Name of the port.
        
    player: str
        Name of the player/governor in charge of the port.
        
    gold: float
        The amount of gold in the port.
        
    coord: Point
        Coordinates of the port.
        
    hinterland: Hinterland
        Hinterland associated with the port
        
    imported_goods: dict
        Dictionary of the port's stock containing goods from other ports.
        
    max_stock: float
        The maximum amount of foreign goods a port can hold.
        
    total_wealth: int
        The total amount of goods in a port.
        
    visits: int
        The aggregated number of visits of during the last rounds

    Methods:
    --------
    receive_goods()
        Adds the amount of foreign goods received to the port's stock. Returns money gained from taxes.
        
    send_goods()
        Adds the amount of foreign goods received to the port's stock. Returns money paid in taxes.
    """
    
    
    __slots__ = ('name', 'player', 'gold', 'coord', 'hinterland', 'imported_goods', 'max_stock', 'total_wealth', 'visits')

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

        self.max_stock = 10
        self.total_wealth = 0        
        self.visits = 0

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
    __slots__ = ('name', 'goods', 'happiness', 'population', "imported_goods", 'size')
    def __init__(self, name, goods):
        self.name = name
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
        self.n_rounds  = 11
        
        for port in config["ports"]:
            self.remaining_ports.append(port)
            
    def default(self, line):
        """
        Called when the input doesn't match any known command.
        Overridden so unknown commands report through the GUI instead of stdout.
        """
        command = line.split()[0] if line.split() else line
        self.message = f"Unknown command: '{command}'. Type 'help' for a list of commands."
            
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
                               Hinterland(port_name,args.goods)
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
            
            
        part1= (
            f"Port : {self.current_port.name}\n"
            f"Gold : {self.current_port.gold}\n"
            )
        
        part2= (
            f"Stock : {self.current_port.total_wealth} / {self.current_port.max_stock}\n"
            f"{text[0]}\n{text[1]}\n{text[2]}\n{text[3]}\n\n"
            f"Last message:\n"
            f"{self.message}"
            )
            
        if self.round_index >= (self.n_rounds - 10):
            return part1+f"Cumulative Visits : {self.current_port.visits}\n"+part2
        else:
            return part1+part2

    def turn(self):
        """
        Function that ends turns
        
        It moves the turn index into the next number and identifies the current player/port.
        If the turn before was the end of the round, it executes end_round().
        """
        self.turn_index += 1
        self.round_index = self.turn_index // self.n_players
        
        self.current_turn = self.turn_index % self.n_players
        self.current_port = self.ports[self.current_turn]
        
        if self.turn_index!=0 and self.current_turn==0:
            #Computer time!!!
            self.end_round(self.round_index)

            
    def end_round(self, round_number):
        """
        Function that ends rounds (a complete set of turns)
        
        It starts with computer time!
        All the non-playable ports perform actions controlled by the computer:
            First, selecting a random port to trade with.
            Second, selecting a random amount of goods to trade.
            And, finally, trading.
        All the messages that resulted from this process are aggregated and shown to the players at the beginning of the next turn.
        """
        
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
        """
        Function that executes trades between ports.
        
        It is summoned by "do_trade()".

        Parameters
        ----------
        port1 : Port
            Port that is sending goods

        amount : int
            Amount of goods being traded

        port2 : Port
            Port that is receiving goods
        """

        if port1 != port2:
            
            if port1.max_stock <= ((amount + port1.total_wealth) - 1):
                raise Exception(f"You can't trade {amount}, you don't have enough stock!")
            elif port2.max_stock <= ((amount + port2.total_wealth) - 1):
                raise Exception(f"The stock in the {port2.name} port can't take {amount} goods!")
            elif port1.max_stock <= ((amount + port1.total_wealth) - 1):
                raise Exception("You can't trade, your stock is full!")
                
                
            port1.send_goods(amount, port2.name)
            port2.receive_goods(amount, port1.name)
            port1.total_wealth += amount
            port2.total_wealth += amount
            
            self.message = f'{port1.name} traded {amount} goods with {port2.name}\n'
            return(self.message) #returns message, so that it can be aggregated with other messages from the computer-controled ports
        else:
            raise Exception("You can't trade with yourself!")
            
    def do_increase_stock(self, amount):
        """
        increase_stock <amount> 

        Increases the stock by a given amount.
        """
        try:
            self.current_port.max_stock += int(amount)
            self.current_port.gold -= 10
            self.message = f"You have increased your stock by {amount} for 10 gold."
        
        except Exception as e:
            self.message = str(e)

    def do_trade(self, line):
        """
        trade <amount> <port>
        Trade the given amount of goods with the specified port.
        """
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

            self.trade_general(port1, int(amount), port2)
            self.turn()
            
        except Exception as e:
            self.message = str(e)
            
    def do_change_player_name(self, line):
        """
        change_player_name <new name>
        Change the current player's name.
        """
        try:
            potential_name = line.lower()
            if len(potential_name)<=10:
                if "comput" not in potential_name:
                    self.current_port.player = potential_name.title()
                
                else:
                    raise Exception("That name is not allowed.")
                
            else:
                raise Exception("That name is too long.")
            
        except Exception as e:
            self.message = str(e)


    def do_pass(self, line):
        """
        pass
        Pass your turn.
        """
        self.message = f"{self.current_port.player} passed\n"
        self.turn()

        
    def do_help(self, line):
        """
        help [command]
        Lists all available commands, or shows detailed help for one command.
        """
        
        if line:
            # Help for a specific command
            func = getattr(self, f"do_{line}", None)
            if func is None:
                self.message = f"No help available: '{line}' is not a valid command."
            elif func.__doc__:
                self.message = func.__doc__
            else:
                self.message = f"No help text has been written for '{line}' yet."
        else:
            # List all available commands
            command_names = sorted(
                name[3:] for name in dir(self.__class__)
                if name.startswith("do_") and name != "do_help" and callable(getattr(self, name))
            )
            
            lines = ["Available commands:"]
            for name in command_names:
                func = getattr(self, f"do_{name}")
                if func.__doc__:
                    summary = func.__doc__.strip().split("\n")[0]
                    lines.append(f"  {summary}")
                else:
                    lines.append(f"  {name}")
            
            lines.append("\nType 'help <command>' for more details on a specific command.")
            self.message = "\n".join(lines)


###############################################################################
#
# Program
#
###############################################################################

if __name__ == "__main__":
    
    gui = Interface()
    
    n_players = None
    initial_message = ("Welcome to the Mediterranean!\n"
                       "Your goal is to become the most powerful trading hub in the Mediterranean Sea!\n"
                       "How many people are playing?"
                       )
    error_message = ""
    
    while gui.is_running() and n_players==None:
        gui.set_stats(initial_message+error_message, "Hello, governors!")

        gui.draw()
        
        n_command = gui.get_command()
        
        if n_command!=None:
            try:
                n_players = int(n_command)
                
                if n_players<1 or n_players>len(config["ports"]):
                    n_players = None
                    raise Exception()
                
            except Exception:
                error_message = f"\nPlease pick a number between 1 and {len(config["ports"])}"
            
    game = MNM(n_players)
    
    while gui.is_running() and (game.n_players != len(game.ports)):
        
        pick_message = ("Please, pick your port by entering the name of one of the cities available on the map.\n"
                        f"Available ports : {game.remaining_ports}")

        gui.set_stats(pick_message, f"Player {game.player_count+1}")

        gui.draw()

        choice = gui.get_command()

        if choice is None:
            continue
        game.choose_port(choice)
        
    for remaining_port_name in game.remaining_ports:
        game.add_port_to_list(remaining_port_name, "Computer")
        
    game.turn()    

    while gui.is_running():

        gui.set_stats(game.get_stats(), f"""Round {game.round_index + 1}: {game.current_port.player}""")

        gui.draw()

        command = gui.get_command()

        if command is None:
            continue

        if game.onecmd(command):
            break

        # Reload the map every turn.
        gui.set_map("assets/map.png")

    gui.close()    
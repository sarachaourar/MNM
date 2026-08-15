import yaml
import cmd
import argparse
import random
from shapely import Point
from interfaceGPT3 import Interface

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

class Hinterland(): #to be replaced by a GDF
    __slots__ = ('name', 'goods', 'happiness', 'population', "imported_goods", 'size')
    def __init__(self, name, goods):
        self.name = name
        self.goods = goods
        self.happiness = 40 #100
        self.population = 20_000
        
class Stock():
    """
    A Stock stores foreign goods traded with other ports.

    Attributes
    ----------
    imported_goods: dict
        Dictionary of the amounts of foreign goods from their respective  foreign ports.
        
    max_stock: float
        The maximum amount of foreign goods a port can hold.
        
    total_wealth: int
        The total amount of goods in a port.
    """
    def __init__(self, name):
        self.max_stock = 10

        self.imported_goods = {}        
        for port in config["ports"]:
            if name == port:
                pass
            else:
                self.imported_goods[port] = 0

        self.total_wealth = 0                   

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
        
    stock: Stock
        Stock associated with the port
        
    visits: int
        The aggregated number of visits of during the last rounds

    Methods:
    --------
    receive_goods()
        Adds the amount of foreign goods received to the port's stock. Returns money gained from fees.
        
    send_goods()
        Adds the amount of foreign goods received to the port's stock. Returns money paid in fees.
    """
    
    
    __slots__ = ('name', 'player', 'gold', 'coord', 'hinterland', 'stock', 'visits')

    def __init__(self, name, player, gold, coord, hinterland):
        self.name = name
        self.player = player
        self.coord = coord
        self.gold = gold
        self.hinterland = hinterland
        self.stock = Stock(self.name)     
        self.visits = 0

    def receive_goods(self, amount, port1):
        """Method to receive goods when a trade is called.

        This method allows a port to recieve goods and gold after the player calls a trade with it.

        Prameters
        ---------
        amount: float
            The amount of goods that is received.

        port1: str
            The port from which the foreign goods are being imported. 
        """
        self.stock.imported_goods[port1] += amount
        fee = 10
        self.gold += fee
        return fee 

    def send_goods(self, amount, port2):
        """Method to send goods when a trade is called.

        This method allows a port/player to send goods and to pay a fee in gold after they call a trade.

        Parameters
        ----------
        amount: float
            The amount of goods that is sent.

        port2: str
            The port from which the foreign goods are gained during the trade. 
        """
        self.stock.imported_goods[port2] += amount
        fee = 10
        self.gold -= fee
        return fee   
    
class MNM(cmd.Cmd):

    __slots__ = ('n_players_og', 'n_players_real', 'n_rounds', 'ports',
                 'remaining_ports', 'player_count', 'turn_index', 'round_index',
                 'message', 'current_turn', 'current_port')

    def __init__(self, n_players):
        super().__init__()
        self.n_players_og = n_players
        self.n_players_real = n_players
        self.n_rounds  = 11
        self.ports = []
        self.remaining_ports = []
        self.player_count=0
        self.turn_index = -1
        self.round_index = 0
        
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
            
            self.add_port_to_list(chosen_port_name, player_name)
            
            self.player_count+=1
            self.remaining_ports.remove(chosen_port_name)
            
            return f"{player_name} is playing as the {chosen_port_name} port.\n"
            
        else:
            return ""

    def get_stats(self):
        """
        Function that is used to transmit stats to the GUI
        
        It prints the desired stats
        """
        text = []

        for port_key in self.current_port.stock.imported_goods:
            text.append(f"{port_key} imported goods: {self.current_port.stock.imported_goods[port_key]}")
            
            
        part1= (
            f"Port : {self.current_port.name}\n"
            f"Hinterland Population : {int(self.current_port.hinterland.population/1_000)}k\n"
            f"Happiness : {self.current_port.hinterland.happiness}\n"
            f"Gold : {self.current_port.gold}\n"
            )
        
        part2= (
            f"Stock : {self.current_port.stock.total_wealth} / {self.current_port.stock.max_stock}\n"
            f"{text[0]}\n{text[1]}\n{text[2]}\n{text[3]}\n\n"
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
        self.current_turn = self.turn_index % self.n_players_og
        self.current_port = self.ports[self.current_turn]
        
        if self.turn_index != 0:
            if self.current_turn==0:
                #Computer time!!!
                self.end_round(self.round_index) 

        if self.round_index != 0: 
            port_maintenance = (self.current_port.stock.max_stock - 9)*10
            self.current_port.gold -= port_maintenance
        
        if self.current_port.hinterland.happiness<=0 and self.current_port.player!="Computer":
            self.current_port.hinterland.happiness=0
            
            randomizer = random.random()
            if randomizer>0.5:
                #the player has a 50% of being deposed (and losing the game) if the happiness reaches 0
                self.n_players_real = self.n_players_real - 1
                self.message = (f"The population of {self.current_port.name} has revolted.\n"
                                f"{self.current_port.player} has been deposed and no longer controls the city.\n"
                                )
                self.current_port.player = "Computer"

        if self.current_port.player=="Computer":
            self.turn()
            print(f"{self.current_port.name} paid a tax of {port_maintenance}")
            
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
            for potential_computer_port in self.ports:
                if computer_port_name == potential_computer_port.name:
                    computer_port = potential_computer_port
                    if self.round_index != 0: 
                        port_maintenance = (computer_port.stock.max_stock - 9)*10
                        computer_port.gold -= port_maintenance
                    break

            temp_port_list = [temp_port for temp_port in self.ports if temp_port.name!=computer_port_name]
            
            cig = computer_port.stock.imported_goods
            not_random_port = list(cig.items())
            not_random_port= sorted(not_random_port, key=lambda tup: tup[1])

            minamount = int(not_random_port[0][1])

            try:
                if computer_port.stock.total_wealth > 0.9 * computer_port.stock.max_stock:
                    computer_messages+=self.increase_stock_general(computer_port, 10)
            except Exception as e:
                computer_messages+=str(e)            

            for p in temp_port_list:
                if cig[p.name] == minamount:
                    try:
                        computer_messages+=self.trade_general(computer_port, 2, p)
                    except Exception as e:
                        computer_messages+=str(e)
                
        self.message = computer_messages   
                
        for port in self.ports:
            ig = port.stock.imported_goods
            happiness_change = 10/(len(ig)-1)
            all_foreign_goods = True
            goods_change = -int(port.hinterland.population / 1_000_000 + 1) #so that, for every million, the goods gone in each turn decreases by 1
            for foreign_port, foreign_goods in ig.items():
                if foreign_goods==0:
                    all_foreign_goods = False
                    happiness_change+=-10/(len(ig)-1)
                else:
                    ig[foreign_port]+=goods_change
                    port.stock.total_wealth+=goods_change
            if all_foreign_goods:
                #gets a little extra
                happiness_change+=10/(len(ig)-1)
            port.hinterland.happiness+=int(happiness_change)
            
            productivity_tax = port.hinterland.happiness / 1_000_000 #so that at happiness=100, a 10_000 gives 1 gold
            port.gold+=int(round(productivity_tax*port.hinterland.population))
        
        self.round_index +=1 
                
    def increase_stock_general(self, port, amount):
            """
            Function that increases the stock of a port
            
            It is summoned by "do_increase_stock()".
    
            Parameters
            ----------
            port : Port
                Port whose stock is to be increased
    
            amount : int
                Change in stock
            """
    
            if amount<0:
                raise Exception("Nice try! Please use positive numbers.\n")
                
            elif amount>port.gold:
                raise Exception(f"{port.name} tried to increase stock by {amount}, but doesn't have the gold to pay for it!\n")
    
            port.stock.max_stock += amount
            port.gold -= amount
            self.message = f"{port.player} has increased the stock of {port.name} by {amount}.\n"
            return(self.message)
            
    def do_increase_stock(self, amount):
        """
        increase_stock <amount> 

        Increases the stock by a given amount for the same amount of gold.
        """
        try:
            self.increase_stock_general(self.current_port, int(amount))
        
        except Exception as e:
            self.message = str(e)
                
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
            
            if port1.stock.max_stock <= ((amount + port1.stock.total_wealth) - 1):
                raise Exception(f"{port1.name} tried to trade {amount}, but the {port1.name} port doesn't have enough stock!\n")
            elif port2.stock.max_stock <= ((amount + port2.stock.total_wealth) - 1):
                raise Exception(f"{port1.name} tried to trade with {port2.name}, but the {port2.name} port can't take {amount} goods!\n")               
                
            port1.send_goods(amount, port2.name)
            port2.receive_goods(amount, port1.name)
            port1.stock.total_wealth += amount
            port2.stock.total_wealth += amount
            
            self.message = f'{port1.name} traded {amount} goods with {port2.name}\n'
            return(self.message) #returns message, so that it can be aggregated with other messages from the computer-controled ports
        else:
            raise Exception("You can't trade with yourself!")
    
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


    def do_end_turn(self, line):
        """
        end_turn
        End your turn.
        """
        self.message = f"{self.current_port.player} ended their turn\n"
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
    n_ports = len(config["ports"])
    
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
                
                if n_players<1 or n_players>n_ports:
                    n_players = None
                    raise Exception()
                
            except Exception:
                error_message = f"\nPlease pick a number between 1 and {n_ports}"
            
    game = MNM(n_players)
    
    extra_message="The map contains the list of port cities available to play.\n"
                    
    choice=None
    
    while gui.is_running() and (game.n_players_og != len(game.ports)):
        
        if extra_message=="":
            extra_message="That is not an available port.\n"
        elif len(game.ports)>0 and choice!=None:
            extra_message+=f"Now, it's your turn, Player {game.player_count+1}.\n"
        
        pick_message = (extra_message+
                        f"Available ports : {game.remaining_ports}\n"+
                        "Type the name of an available port to pick it for yourself.")

        gui.set_stats(pick_message, f"Player {game.player_count+1}")

        gui.draw()

        choice = gui.get_command()

        if choice is None:
            continue
        
        extra_message=game.choose_port(choice)
    
        
    for remaining_port_name in game.remaining_ports:
        game.add_port_to_list(remaining_port_name, "Computer")
        
    game.message=extra_message
        
    game.turn()    

    while gui.is_running():

        gui.set_stats(game.get_stats(), f"""Round {game.round_index + 1}: {game.current_port.player}""")
        gui.set_message(game.message)
        
        gui.draw()

        command = gui.get_command()

        if command is None:
            continue

        if game.onecmd(command):
            break

        # Reload the map every turn.
        gui.set_map("assets/map.png")

    gui.close()    

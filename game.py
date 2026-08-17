import yaml
import cmd
import argparse
import random
import sys
import rasterio
import json
import statistics
import geopandas as gpd
import rioxarray as rioxr
from PIL import Image, ImageDraw
from shapely import Point, Polygon
from shapely.ops import unary_union
from skimage.graph import route_through_array
from rasterio.transform import rowcol
from interfaceGPT4 import Interface

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
parser.add_argument('--fee', type=float, default=10)
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
    
ROUTE_COLORS = [
    "#FF5733", "#33C1FF", "#8DFF33", "#FF33F6", "#FFD433",
    "#33FFAA", "#B833FF", "#FF3383", "#33FFF6", "#B4FF33",
    "#33FF57", "#F633FF"
]
    
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

BASE_MAP = Image.open('assets/map_background.png').convert('RGBA') #AI
LABELS_OVERLAY = Image.open('assets/map_overlay.png').convert('RGBA') #AI

def render_frame(game, mnm_map, out_path='assets/map_frame.png'):
    '''partially AI-Generated Function'''
    frame = BASE_MAP.copy()
    draw = ImageDraw.Draw(frame)

    for route in game.active_routes:
        pts = mnm_map.route_pixels(route[0], route[1])
        draw.line(pts, fill=route[2], width=10)

    # Labels/dots go on top, so routes never cover port names
    frame = Image.alpha_composite(frame, LABELS_OVERLAY)
    frame.convert('RGB').save(out_path)
    return out_path

###############################################################################
#
# Classes
#
###############################################################################

class Hinterland(): #to be replaced by a GDF
    __slots__ = ('name', 'goods', 'happiness', 'hinter_indices', 'area', 'population', 'geometry')
    def __init__(self, name, goods, hinter_indices, area, population, geometry):
        self.name = name
        self.goods = goods
        self.happiness = 50 #100
        self.hinter_indices = hinter_indices
        self.area = area
        self.population = population
        self.geometry = geometry        
        
class Stock():
    """
    A Stock stores foreign goods traded with other ports.

    Attributes
    ----------
    imported_goods: dict
        Dictionary of the goods from other ports.
        
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
        
    shipping_costs: int
        Dictionary of the cost to ship to other ports.

    fee: int
        Fee paid by the incoming ports.

    queue: list
        List of boats waiting to be handled by the port once it has enough stock.

    Methods:
    --------
    receive_goods()
        Adds the amount of foreign goods received to the port's stock.
    send_boat()
        Creates a boat object and sends it to the destination port with a set amount of cargo.
    handle_queue()
        Loops throught the list of qeued ports and takes on their goods if the stock can handle it.
        It then sends the boats back to their home ports with the port's own cargo.
    maintenance_cost()
        Function that applies maintenance cost
    hapiness_and_goods()
        Function that recalculates the happiness level and the goods
    """
    
    
    __slots__ = ('name', 'player', 'gold', 'fee', 'coord', 'hinterland', 'stock', 'shipping_costs', 'closest_port', 'queue')

    def __init__(self, name, player, gold, fee, coord, hinterland):
        self.name = name
        self.player = player
        self.coord = coord
        self.gold = gold
        self.fee = fee
        self.hinterland = hinterland
        self.stock = Stock(self.name)
        self.queue = []
        self.shipping_costs = {}   

    def send_boat(self, amount, destination_port, cargo):
        """
        Function that sends boats to other ports. If the destination port has enough stock to handle 
        the sent goods, the boat drops it's goods and comes back immediatly. If the destination port
        can't handle those goods because their stock is full, the boat will be added to the queue of 
        boats waiting to drop their goods.
        
        It is summoned by "do_send()".

        Parameters
        ----------
        amount : int
            Amount of goods being traded

        port2 : Port
            Port that is receiving goods
        """        
        if self != destination_port:
            boat = Boat(self, destination_port, amount, cargo)

            if amount > boat.capacity:
                raise Exception(f"You can't send {amount} to {destination_port.name} your boat's capacity is {self.boats[destination_port.name].capacity}")
            
            elif self.gold <= self.shipping_costs[destination_port.name]:
                raise Exception(f"{self.name} tried to send a boat to {destination_port.name}, but it can't afford the journey!\n")
            elif self.gold <= self.shipping_costs[destination_port.name] + destination_port.fee:
                raise Exception(f"{self.name} tried to send a boat to {destination_port.name}, but it can't afford {destination_port.name}'s {destination_port.fee} fee!\n")
                
            self.gold -= (destination_port.fee + self.shipping_costs[destination_port.name])
            destination_port.queue.append(boat)
            
            if cargo.player!="Computer":
                game.active_routes.append((cargo.name, destination_port.name, game.port_colors[cargo.name]))
                gui.set_map(render_frame(game, mnm_map))
                
            elif destination_port.player!="Computer":
                game.active_routes.append((cargo.name, destination_port.name, game.port_colors[cargo.name]))
            
            return f"{self.name} sent their boat to get {amount} of {destination_port.name}'s goods. It is waiting in queue\n"

        else:
            return "You can't send boats to yourself!"

    def handle_queue(self):
        og_queue = self.queue.copy()
        messages = ""
        for boat in og_queue:
            if self.stock.max_stock < (boat.amount + self.stock.total_wealth):
                break
            self.receive_goods(boat.amount, boat.cargo)
            self.queue.remove(boat)
            messages += f"{boat.flag.name}'s boat reached the {self.name} port and dropped {boat.amount} goods.\n"
            if boat.flag.name != self.name:
                boat.cargo = self
                boat.flag.queue.append(boat)
        return messages
                
    def maintenance_cost(self):
        """
        Function that applies maintenance costs
        
        It is summoned by "turn()" and "end_round()".
        """
        
        port_maintenance = (self.stock.max_stock - 10)*1
        if (self.gold - port_maintenance) <= 0:
            self.gold = 0
            self.stock.max_stock = 10
            return f"{self.name} can't afford to maintain their port anymore, their stock goes back to 10"
        else:
            self.gold -= port_maintenance   
            return ""
        
    def happiness_and_goods(self):
        """
        Function that recalculates the happiness level and the goods
        
        It is summoned by "turn()" and "end_round()".
        """

        ig = self.stock.imported_goods
        happiness_change = 5/(1-1/len(ig)) # = 10*(len(ig)/2)/(len(ig)-1) so that, if half the goods're missing, the happiness doesn't decrease
        all_foreign_goods = True
        goods_change = -int(self.hinterland.population / 1_000_000 + 1) #so that, for every million, the goods gone in each turn increases by 1
        for foreign_port, foreign_goods in ig.items():
            if (foreign_goods + goods_change) < 0:
                all_foreign_goods = False
                self.stock.total_wealth-=ig[foreign_port]
                ig[foreign_port] = 0
                happiness_change+=-10/(len(ig)-1)
            else:
                ig[foreign_port]+=goods_change
                self.stock.total_wealth+=goods_change
        if all_foreign_goods:
            #gets a little extra
            happiness_change+=10/(len(ig)-1)
        self.hinterland.happiness+=int(happiness_change)
        
        productivity_tax = self.hinterland.happiness / 100_000 #so that, at happiness=100, a 10_000 population gives 10 gold
        self.gold+=int(round(productivity_tax*self.hinterland.population))
        
    def receive_goods(self, amount, port1):
        """Method to receive goods when a trade is called.

        This method allows a port to recieve goods and gold after the player calls a trade with it.

        Prameters
        ---------
        amount: float
            The amount of goods that is received.

        port1: Port
            The port from which the foreign goods are being imported. 
        """           
        self.stock.imported_goods[port1.name] += amount
        self.stock.total_wealth += amount
        self.gold += self.fee
        

class Boat():
    """
    A boat takes cargo from it's home port, heads to a destination port, waits in queue, 
    loads the cargo with goods once it is handeled and heads back home.
    """
    __slots__ = ('flag', 'destination', 'capacity', 'route', 'amount', 'cargo')

    def __init__(self, flag, destination, amount, cargo):
        self.amount = amount
        self.cargo = cargo
        self.flag = flag
        self.destination = destination
        self.capacity = 5
    
    
class Map():
    """
    Class for spatial calculations and deriving information from the map

    Attributes
    ----------
    pop_raster: xarray DataArray
        raster with the population density values
        
    pop_gdf: geopandas GeoDataFrame
        raster with the population density values
        
    land_resistance: int
        value assigned to land pixels to prevent routes from going in-land
        
    resistance: numpy.ndarray
        array with resistance values to calculate routes

    Methods
    ----------
        
    find_routes()
        calculates the shortest route from port1 to port2
    
    calc_shipping_costs()
        calcukates the cost of travel from every port to every port and finds their nearest port

    geo_to_pixel()
        converts real coordinates to image pixels

    route_pixels()
        turns the real geographical routes into lines connected by pixels

    """

    def __init__(self):

        try:
            with rioxr.open_rasterio(config["raster"]) as tif:
                self.pop_raster = tif.load()
            #print('Success!')
        except Exception as e:
            print(e)
            sys.exit()
    
        self.pop_raster = self.pop_raster.squeeze()
        
        raster_val = self.pop_raster.values
        
        self.resistance = raster_val.copy()
        
        self.land_resistance = 1000
    
        self.resistance[self.resistance!=-9999] = self.land_resistance
        self.resistance[self.resistance!= self.land_resistance] = 1
        
        
        shapes = rasterio.features.shapes(raster_val, transform=self.pop_raster.rio.transform()) #AI
        
        geometries = []
        colvalues = []
        for (geom, colval) in shapes:
            geometries.append(Polygon(geom["coordinates"][0]))
            colvalues.append(colval)
        
        self.pop_gdf = gpd.GeoDataFrame({"value": colvalues, "geometry": geometries})
        self.pop_gdf.crs = self.pop_raster.spatial_ref.crs_wkt #or raster.rio.crs
        
        self.pop_gdf['area']= (self.pop_gdf.to_crs("EPSG:2062")).geometry.area / 10**6
        self.pop_gdf['pop'] = (self.pop_gdf['value'] * self.pop_gdf['area']).astype(int)
        
        self.route_cache = {} #AI
        with open('assets/map_bounds.json') as f: #AI
            b = json.load(f) #AI
        self.map_bounds = b #AI
        self.img_w = b["img_w"] #AI
        self.img_h = b["img_h"] #AI
        
    def find_route(self, port1, port2):
        
        start_row, start_col = rowcol(self.pop_raster.rio.transform(), port1.coord.x, port1.coord.y) #AI
        end_row, end_col = rowcol(self.pop_raster.rio.transform(), port2.coord.x, port2.coord.y) #AI
        
        indices, weight = route_through_array(
            self.resistance,
            (start_row, start_col),
            (end_row, end_col),
            fully_connected=True,
            geometric=True
        )
        
        return(indices, int(weight-self.land_resistance))
    
    def calc_shipping_costs(self):
        for index1, port1 in enumerate(game.ports):
            min_cost = 1_000_000
            neighbour_port_name = ""
            for index2, port2 in enumerate(game.ports):
                if index2 == index1:
                    continue
                
                elif index2 < index1:
                    if port1.shipping_costs[port2.name] < min_cost:
                        min_cost = port1.shipping_costs[port2.name]
                        neighbour_port_name = port2.name
                    
                    continue

                else:
                    indices, cost = self.find_route(port1, port2)
                    self.route_cache[frozenset({port1.name, port2.name})] = indices  # NEW
    
                    port1.shipping_costs[port2.name] = cost
                    port2.shipping_costs[port1.name] = cost
                    
                    if cost< min_cost:
                        min_cost = cost
                        neighbour_port_name = port2.name
                        
            port1.closest_port = game.fetch_port(neighbour_port_name)
            
    def geo_to_pixel(self, x, y):
        '''AI-generated function'''
        b = self.map_bounds
        px = (x - b["left"]) / (b["right"] - b["left"]) * self.img_w
        py = (b["top"] - y) / (b["top"] - b["bottom"]) * self.img_h
        return (px, py)
                    
    def route_pixels(self, name1, name2):
        """AI-generated function
        convert a cached raster path into image pixel coordinates."""
        indices = self.route_cache[frozenset({name1, name2})]
        transform = self.pop_raster.rio.transform()
        pts = []
        for row, col in indices:
            x, y = transform * (col + 0.5, row + 0.5)
            pts.append(self.geo_to_pixel(x, y))
        return pts


class MNM(cmd.Cmd):

    __slots__ = ('n_players_og', 'n_players_real', 'n_rounds', 'ports',
                 'remaining_ports', 'player_count', 'turn_index', 'round_index',
                 'message', 'current_turn', 'current_port', 'GAME_OVER',
                 'port_colors', 'active_routes')

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
        self.message = ""
        self.GAME_OVER = False
        self.port_colors = {}
        self.active_routes = []
        
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
        
        port_coords = parse_point(config["ports"][port_name])
        
        gdf_intersec = mnm_map.pop_gdf[mnm_map.pop_gdf.intersects(port_coords)]
        port_pixel = mnm_map.pop_gdf[mnm_map.pop_gdf.intersects(port_coords)].iloc[0]
        gdf_nonulls = mnm_map.pop_gdf[mnm_map.pop_gdf['value']>0]
            
        neighbour_gdf = gdf_nonulls[gdf_nonulls.touches(port_pixel.geometry)]
        
        #To exclude the diagonal neighbours:
        neighbour_intersections = neighbour_gdf.geometry.intersection(port_pixel.geometry).to_crs("EPSG:2062") #AI
        shared_length = neighbour_intersections.length #AI
        close_neighbour_gdf = neighbour_gdf[shared_length > 0] #AI
        
        hinter_indices = gdf_intersec.index.tolist() #AI
        hinter_indices+=list(set(close_neighbour_gdf.index))
        
        subset = gdf_nonulls.loc[hinter_indices]
        
        self.ports.append(Port(port_name,
                               player_name,
                               args.gold,
                               args.fee,
                               port_coords,
                               Hinterland(port_name,
                                          args.goods,
                                          hinter_indices,
                                          subset['area'].sum(),
                                          subset['pop'].sum(),
                                          unary_union(subset.geometry)
                                          )
                               )
                          )
        
        self.port_colors[port_name] = ROUTE_COLORS[len(self.ports) - 1]
    
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
        
    def fetch_port(self, port_name):
        """
        Function to fetch the port object with a given name

        Parameters
        ----------
        port_name : str
            Name of the port
            
        Returns
        ----------
        Port
            Port object with given name
        """
        
        for potential_port in self.ports:
            if port_name == potential_port.name:
                return potential_port

    def get_stats(self, port, allparts=True):
        """
        Function that is used to transmit stats to the GUI
        
        It prints the desired stats
        """
        text_list = []
        text = ""

        for port_key in port.stock.imported_goods:
            text_list.append(f"{port_key}: {port.stock.imported_goods[port_key]}")

        for item in text_list:
            text += f"{item}\n"    
            
        part1= (
            f"Port : {port.name}\n"
            f"Port Fee : {port.fee}\n"
            f"Hinterland Population : {int(port.hinterland.population/1_000)}k\n"
            f"Happiness : {port.hinterland.happiness}\n"
            f"Gold : {port.gold}\n"
            )
        
        part2= (
            f"Port Queue : {len(port.queue)}\n"
            f"Stock : {port.stock.total_wealth} / {port.stock.max_stock}\n\n"
            f"Imported goods list:\n"
            f"{text}\n\n"
            )
            
        #if self.round_index >= (self.n_rounds - 10):
        #    return part1+f"Cumulative Visits : {port.visits}\n"+part2
        #else:
        #    return part1+part2
        if allparts:
            return part1+part2
        else:
            return part1

    def turn(self):
        """
        Function that ends turns
        
        It moves the turn index into the next number and identifies the current player/port.
        If the turn before was the end of the round, it executes end_round().
        Afterwards, deduces maintenance costs and recalculates happiness and goods.
        If the happiness is 0, there's a chance the player will be deposed.
        If so, from then on, that player's turn is skipped.
        """
        self.turn_index += 1
        self.current_turn = self.turn_index % self.n_players_og
        self.current_port = self.ports[self.current_turn]
        
        self.active_routes = [r for r in self.active_routes if r[0] != self.current_port.name]
        gui.set_map(render_frame(game, mnm_map))

        if self.turn_index!=0 and self.current_turn==0:
            #Computer time!!!
            self.end_round(self.round_index)

        if self.round_index != 0: 
            self.message += self.current_port.maintenance_cost()
            
            self.current_port.happiness_and_goods()
            
        if self.turn_index!=0 :
            self.message += self.current_port.handle_queue()
        
        if self.current_port.hinterland.happiness<=0 and self.current_port.player!="Computer":
            self.current_port.hinterland.happiness=0
            
            randomizer = random.random()
            if randomizer>0.5:
                #the player has a 50% chance of being deposed (and losing the game) if the happiness reaches 0
                self.n_players_real = self.n_players_real - 1
                self.message += (f"The population of {self.current_port.name} has revolted.\n"
                                f"{self.current_port.player} has been deposed and no longer controls the city.\n"
                                )
                self.current_port.player = "Computer"
                
        if self.n_players_real==0:
            self.GAME_OVER = True

        elif self.current_port.player=="Computer":
            self.turn()

            
    def end_round(self, round_number):
        """
        Function that ends rounds (a complete set of turns)
        
        It starts with computer time!
        All the non-playable ports perform actions controlled by the computer:
            First, paying the port's maintenance cost.
            Second, if stock space is lacking, try to increase the stock.
            Third, adjust fees according to needs.
            Fourth, trading.
            Fifth, increase stock again, if necessary.
        All the messages that resulted from this process are aggregated and shown to the players at the beginning of the next turn.
        After the computer actions, the game renders a new map with the relevant routes.
        """
        
        computer_messages = self.message
        for computer_port_name in self.remaining_ports:
            
            computer_port = self.fetch_port(computer_port_name)
            
            self.active_routes = [r for r in self.active_routes if r[0] != computer_port_name]
            
            computer_port.maintenance_cost()
            computer_port.happiness_and_goods()
            computer_port.handle_queue()
                
            try:
                if computer_port.stock.total_wealth > 0.8 * computer_port.stock.max_stock:
                    self.increase_stock_general(computer_port, 10)
                    #print(f"{computer_port.name} increase stock to {computer_port.stock.max_stock}")
            except Exception as e:
                str(e)
                
            if computer_port.hinterland.happiness<=20:
                computer_port.fee=0
            elif computer_port.gold<=200:
                computer_port.fee+=50
            
            cig = computer_port.stock.imported_goods
            
            if cig[computer_port.closest_port.name]<=1 and computer_port.closest_port.fee<100:
                #always trade with the closest port if lacking their goods and they have an honest fee
                try:
                    if computer_port.closest_port.player != 'Computer':
                        computer_messages+=computer_port.send_boat(5, computer_port.closest_port, computer_port)
                        
                    else:
                        computer_port.send_boat(5, computer_port.closest_port, computer_port)
                except Exception as e:
                    if computer_port.closest_port.player != 'Computer':
                        computer_messages+=str(e)
                    else:
                        pass
            
            not_random_port = list(cig.items()) #the name "not_random_port" is a joke, because it used to be a random port in an earlier version of the game
            not_random_port = sorted(not_random_port, key=lambda tup: tup[1])
            
            minamount = int(not_random_port[0][1])
            
            min_list = [tup[0] for tup in not_random_port if tup[1]==minamount]
            
            fees_list = [(game.fetch_port(p_name)).fee for p_name in min_list]
            median_fee = statistics.median(fees_list)                           

            for p_name in min_list:
                p = game.fetch_port(p_name)
                if p.fee<median_fee:
                    #print(median_fee)
                    try:
                        if p.player != 'Computer':
                            computer_messages+=computer_port.send_boat(5, p, computer_port)
                        else:
                            computer_port.send_boat(5, p, computer_port)
                    except Exception as e:
                        if p.player != 'Computer':
                            computer_messages+=str(e)
                        else:
                            pass
                        
            try:
                if computer_port.stock.total_wealth > 0.8 * computer_port.stock.max_stock:
                    self.increase_stock_general(computer_port, 10)
                    #print(f"{computer_port.name} increase stock to {computer_port.stock.max_stock}")
            except Exception as e:
                str(e)
                
        self.message = computer_messages
        self.round_index +=1
        gui.set_map(render_frame(game, mnm_map))
        
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
            
        elif (10*amount)>port.gold:
            raise Exception(f"{port.name} tried to increase stock by {amount}, but doesn't have the gold to pay for it!\n")

        port.stock.max_stock += amount
        port.gold -= 10*amount
        port.handle_queue()
        self.message = f"{port.player} has increased the stock of {port.name} by {amount}.\n"
        return(self.message)
        
    def do_increase_stock(self, amount):
        """
        increase_stock <amount> 
        Increases the stock by a given amount for 10x that amount of gold.
        For every unit of stock you increase, you will pay 1 more unit of gold of port maintenance every turn
        """
        try:
            self.increase_stock_general(self.current_port, int(amount))
        
        except Exception as e:
            self.message = str(e)
                
    def do_send(self, line):
        """
        send <amount> <port>
        Executed if you have enough money to pay for the specified port's fees and the trip there.
        In that case, you'll give the stated amount of goods to the specified port.
        In return, you'll receive the same amount of that port's goods        
        """
        try:
            amount, port2_name = line.split()
            port2 = self.fetch_port(port2_name) 

            if port2 == None:
                raise Exception(f"{port2_name} is not a valid name.")  

            self.message = self.current_port.send_boat(int(amount), port2, self.current_port)
                      
        except Exception as e:
            self.message = str(e)
            
    def do_travel_costs(self, line):
        """
        travel_costs 
        Check how much it would cost to travel to the other cities from your port
        """
        costs_mess = f"Travelling Costs from {self.current_port.name}:\n"
        for port_name in self.current_port.shipping_costs:
            costs_mess+= f"  {port_name}: {self.current_port.shipping_costs[port_name]} gold.\n"
        
        self.message = costs_mess
        
    def do_port_fees(self, line):
        """
        port_fees 
        Check the current port fees of the other ports. Beware that they might change!
        """
        costs_mess = "Current port fees:\n"
        for port_name in self.current_port.shipping_costs:
            port = self.fetch_port(port_name)
            costs_mess+= f"  {port_name}: {port.fee} gold.\n"
        
        self.message = costs_mess
            
    def do_change_fee_to(self, line):
        """
        change_fee_to <new value>
        Change your port's current fee for visitors.
        """
        try:
            
            new_fee = int(line)
            
            if new_fee<0:
                raise Exception("That's not allowed.\n")
            
            else:
                self.current_port.fee = new_fee
                self.message = f"{self.current_port.name} has a new port fee."
            
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
                if len(potential_name)>=0:
                    if "comput" not in potential_name:
                        self.current_port.player = potential_name.title()
                        self.message = f"{self.current_port.name}'s player has a new name."
                        
                    else:
                        raise Exception("That name is not allowed.")
                        
                else:
                    raise Exception("That name is too short.")
                
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
                       "And you must also insure your population remains happy, by providing them with goods from every port!\n"
                       "The larger your population is and the happier they are, the higher your productivity revenue will be every turn!\n"
                       "Beware, though: an unhappy population might try to depose their governor!"
                       )
    error_message = ""
    
    while gui.is_running() and n_players==None:
        gui.set_stats(initial_message+error_message, "Hello, governors!")
        gui.set_message("Throughout the game, messages concerning the players will appear here.\n"+
                        "The computer-controlled ports might trade between themselves, but the related messages will not be printed.\n"+
                        "The same is true for the routes drawn on the map.\n"
                        "Now, are you ready? How many people are playing?")

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
    
    if gui.is_running():
    
        gui.set_stats("Building World Map...", "Loading...")
        gui.draw()
            
        mnm_map = Map()
                
        game = MNM(n_players)
        
        extra_message=" "
                       
        choice=None
    
    while gui.is_running() and (game.n_players_og != len(game.ports)):
        
        if extra_message=="":
            extra_message="That is not an available port.\n"
        elif len(game.ports)>0 and choice!=None:
            extra_message+=f"Now, it's your turn, Player {game.player_count+1}.\n"
        
        pick_message = ("The map contains the list of port cities available to play.\n"
                        f"Available ports : {game.remaining_ports}\n"+
                        "Type the name of an available port to pick it for yourself.")

        gui.set_stats(pick_message, f"Player {game.player_count+1}")
        gui.set_message(extra_message+game.message)

        gui.draw()

        choice = gui.get_command()

        if choice is None:
            continue
        
        extra_message=game.choose_port(choice)
        
    if gui.is_running():
    
        game.message=extra_message
        gui.set_stats("Creating remaining ports...", "Loading...")
        gui.draw()
            
        for remaining_port_name in game.remaining_ports:
            game.add_port_to_list(remaining_port_name, "Computer")
        
        mnm_map.calc_shipping_costs()        
            
        game.turn()
    
    while gui.is_running() and not game.GAME_OVER:

        gui.set_stats(game.get_stats(game.current_port), f"Round {game.round_index + 1}: {game.current_port.player}")
        gui.set_message(game.message)
        
        gui.draw()

        command = gui.get_command()

        if command is None:
            continue

        if game.onecmd(command):
            break

        if game.round_index==20:
            
            winner = None
            winner_gold = 0
            
            for port in game.ports:
                if port.gold > winner_gold:
                    winner = port
                    winner_gold = port.gold
                
            while gui.is_running() and not game.GAME_OVER:
        
                gui.set_stats(game.get_stats(winner, False), f"Hooray, {winner.player}!!!")
                gui.set_message(game.message+
                                f"{winner.player}, governing over {winner.name} has won the game!\n"+
                                "If you wish to continue playing, write 'continue'.\n"
                                )
                
                gui.draw()
        
                command = gui.get_command()
        
                if command is None:
                    continue
        
                if command=='continue':
                    break

    
    while gui.is_running() and game.GAME_OVER:
        gui.set_stats("All the players have been deposed!", "GAME OVER")
        gui.set_message(game.message)
        
        gui.draw()

        command = gui.get_command()
        
    gui.close()    

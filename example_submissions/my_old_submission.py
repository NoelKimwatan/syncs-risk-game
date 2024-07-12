from collections import defaultdict, deque
import random
from typing import Optional, Tuple, Union, cast
from risk_helper.game import Game
from risk_shared.models.card_model import CardModel
from risk_shared.queries.query_attack import QueryAttack
from risk_shared.queries.query_claim_territory import QueryClaimTerritory
from risk_shared.queries.query_defend import QueryDefend
from risk_shared.queries.query_distribute_troops import QueryDistributeTroops
from risk_shared.queries.query_fortify import QueryFortify
from risk_shared.queries.query_place_initial_troop import QueryPlaceInitialTroop
from risk_shared.queries.query_redeem_cards import QueryRedeemCards
from risk_shared.queries.query_troops_after_attack import QueryTroopsAfterAttack
from risk_shared.queries.query_type import QueryType
from risk_shared.records.moves.move_attack import MoveAttack
from risk_shared.records.moves.move_attack_pass import MoveAttackPass
from risk_shared.records.moves.move_claim_territory import MoveClaimTerritory
from risk_shared.records.moves.move_defend import MoveDefend
from risk_shared.records.moves.move_distribute_troops import MoveDistributeTroops
from risk_shared.records.moves.move_fortify import MoveFortify
from risk_shared.records.moves.move_fortify_pass import MoveFortifyPass
from risk_shared.records.moves.move_place_initial_troop import MovePlaceInitialTroop
from risk_shared.records.moves.move_redeem_cards import MoveRedeemCards
from risk_shared.records.moves.move_troops_after_attack import MoveTroopsAfterAttack
from risk_shared.records.record_attack import RecordAttack
from risk_shared.records.types.move_type import MoveType

import time

#Homabase
home_base = -1

# We will store our enemy in the bot state.
class BotState():
    def __init__(self):
        self.enemy: Optional[int] = None




def main():
    
    # Get the game object, which will connect you to the engine and
    # track the state of the game.
    game = Game()
    bot_state = BotState()

    global attack_probability_threshold 
    attack_probability_threshold = 0.75

    #battleprob,risk_probability
    global p_obj
    p_obj = risk_probability()




   
    # Respond to the engine's queries with your moves.
    while True:


        # Get the engine's query (this will block until you receive a query).
        query = game.get_next_query()
        #print("Player: {}".format(game.state.me.player_id),flush=True)


        # Based on the type of query, respond with the correct move.
        def choose_move(query: QueryType) -> MoveType:
            match query:
                case QueryClaimTerritory() as q:
                    return handle_claim_territory(game, bot_state, q)

                case QueryPlaceInitialTroop() as q:
                    #return handle_place_initial_troop(game, bot_state, q)
                    return handle_place_initial_troop_with_clusters(game, bot_state, q)

                case QueryRedeemCards() as q:
                    return handle_redeem_cards(game, bot_state, q)

                case QueryDistributeTroops() as q:
                    return handle_distribute_troops(game, bot_state, q)

                case QueryAttack() as q:
                    #return handle_attack(game, bot_state, q)
                    #return handle_attack_new_new(game, bot_state, q)
                    #return handle_attack_probability(game, bot_state, q)
                    return handle_attack_probability_simplified(game, bot_state, q)

                case QueryTroopsAfterAttack() as q:
                    #return handle_troops_after_attack(game, bot_state, q)
                    return handle_troops_after_attack_new(game, bot_state, q)

                case QueryDefend() as q:
                    return handle_defend(game, bot_state, q)

                case QueryFortify() as q:
                    #return handle_fortify(game, bot_state, q)
                    return handle_fortify_new(game, bot_state, q)
                    
        
        # Send the move to the engine.
        game.send_move(choose_move(query))
                

def handle_claim_territory(game: Game, bot_state: BotState, query: QueryClaimTerritory) -> MoveClaimTerritory:
    """At the start of the game, you can claim a single unclaimed territory every turn 
    until all the territories have been claimed by players."""

    unclaimed_territories = game.state.get_territories_owned_by(None)
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    #print("My territories: ",my_territories,flush=True)

    # We will try to always pick new territories that are next to ones that we own,
    # or a random one if that isn't possible.
    adjacent_territories = game.state.get_all_adjacent_territories(my_territories)
    #print("Adjacent territories: ",adjacent_territories,flush=True)

    # We can only pick from territories that are unclaimed and adjacent to us.
    available = list(set(unclaimed_territories) & set(adjacent_territories))
    #print("Available territories: ",available)
    if len(available) != 0:

        # We will pick the one with the most connections to our territories
        # this should make our territories clustered together a little bit.
        # def count_adjacent_friendly(x: int) -> int:
        #     return len(set(my_territories) & set(game.state.map.get_adjacent_to(x)))

        # selected_territory = sorted(available, key=lambda x: count_adjacent_friendly(x), reverse=True)[0]

        #Pick territory that most of its territories are friendly
        def count_adjacent_friendly(x: int) -> float:
            return len(set(my_territories) & set(game.state.map.get_adjacent_to(x))) / len(game.state.map.get_adjacent_to(x))

        selected_territory = sorted(available, key=lambda x: count_adjacent_friendly(x), reverse=True)[0]
    
    # Or if there are no such territories, we will pick just an unclaimed one with the greatest degree.
    else:
        #selected_territory = sorted(unclaimed_territories, key=lambda x: len(game.state.map.get_adjacent_to(x)), reverse=True)[0]
        #Change to select territory with the least amount of territories bordering it
        #Change to start by selecting a position in either Africa, South Ameria or Australia

        #Give each preffered territory a weight
        def territorySelectionPreference(territory):
            territoryWeight = {
                8:15,
                28: 10, #South America is the most preffered
                37: 9,  #Followed by South Africa
                41: 8,  #Followed by Western Ausralia
                38: 8   #Finally Eastern Australia
            }

            return territoryWeight[territory]
        
        preferredStartingPoint = [41,28,37,8]
        prefferedAvailable = list(set(preferredStartingPoint) & set(unclaimed_territories))
        
        if len(prefferedAvailable) != 0:
            prefferedAvailable = sorted(prefferedAvailable,key=territorySelectionPreference,reverse=True)
            selected_territory = prefferedAvailable[0]
            #print("Preffered territory available",flush=True)
        else:
            selected_territory = sorted(unclaimed_territories, key=lambda x: len(game.state.map.get_adjacent_to(x)))[0]
            #print("Preffered territory NOT available",flush=True)


        if len(my_territories) == 0:
            global home_base
            home_base = selected_territory
            print("Home base is: ",home_base,flush=True)
        
        #print("Selected territory: ",selected_territory,flush=True)
        
    return game.move_claim_territory(query, selected_territory)

# def connected_to_base(game:Game,territories:list,checked:list):
#     territories_connected_to_base = set()
#     my_territories = game.state.get_territories_owned_by(game.state.me.player_id)

#     for territory in territories:
#         adjuscent_territories = game.state.map.get_adjacent_to(territory)
#         adjuscent_territories_owned = list(set(adjuscent_territories) & set(my_territories))
#         checked.append(territory)

#         if home_base in adjuscent_territories_owned:
#             territories_connected_to_base.add(territory)
#         else:
#             if len(adjuscent_territories_owned) != 0:
#                 connected_to_base(game,adjuscent_territories_owned)

#     return list(territories_connected_to_base)

# def get_home_base_territories(game: Game, home_base: int,home_base_territories:set, checked: list):
#     my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
#     adjuscent_territories = game.state.map.get_adjacent_to(home_base)

#     adjuscent_owned_territories = list(set(my_territories) & set(adjuscent_territories))

#     for territory in adjuscent_owned_territories:
#         if territory not in home_base_territories and territory not in checked:
#             home_base_territories.add(territory)
#             checked.append(territory)
#             get_home_base_territories(game,territory,home_base_territories,checked)
#         else:
#             checked.append(territory)

#     print("Home base territories:",home_base_territories)

def find_clusters(game:Game,territories:list[int]):
    pass


def get_home_base_territories(game:Game, home_base:int):
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    checked = list()
    home_base_territories = set()

    def get_adjuscent_owned_territories(territory):
        adjuscent = game.state.map.get_adjacent_to(territory)
        adjuscent.append(territory)
        adjuscent_owned_territories = list(set(my_territories) & set(adjuscent))
        #print("Adjuscent owned territories: ",adjuscent_owned_territories,flush=True)

        for territory in adjuscent_owned_territories:
            if territory not in home_base_territories and territory not in checked:
                #print("Territory: {} Not in adjuscent or checked".format(territory))
                home_base_territories.add(territory)
                checked.append(territory)
                get_adjuscent_owned_territories(territory)

    get_adjuscent_owned_territories(home_base)

    return list(home_base_territories)


def get_territory_clusters(game:Game):
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    checked = []
    cluster_dict = dict()
    cluster_count = 0

    def get_cluster(territory):
        checked.append(territory)
        adjuscent = game.state.map.get_adjacent_to(territory)
        adjuscent_friendly = list(set(my_territories) & set(adjuscent))
        adjuscent_unchecked = [x for x in adjuscent_friendly if x not in checked]

        if len(adjuscent_unchecked) != 0:
            for t in adjuscent_unchecked:
                cluster_dict[t] = cluster_count
                get_cluster(t)

    for index,territory in enumerate(my_territories):    
        # print(f"[Get Cluster Function] -- Index: {index} Territory: {territory}")    
        if cluster_dict.get(territory,None) == None:
            cluster_dict[territory] = cluster_count
            get_cluster(territory)
            cluster_count = cluster_count + 1

    #Cluster dict {2: 0, 8: 0, 3: 0, 6: 0, 5: 0, 7: 0, 28: 1, 38: 2}
    return cluster_dict

    # print(f"[Get Cluster Function] -- Cluster dict {cluster_dict}")
    # print(f"[Get Cluster Function] -- My territories {my_territories}")

def handle_place_initial_troop_with_clusters(game: Game, bot_state: BotState, query: QueryPlaceInitialTroop) -> MovePlaceInitialTroop:
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
        # We will place troops along the territories on our border.
    all_border_territories = game.state.get_all_border_territories(
        game.state.get_territories_owned_by(game.state.me.player_id)
    )

    territory_clusters = get_territory_clusters(game)
    no_of_clusters = len(set([x for x in territory_clusters.values()]))
    cluster_list = [[] for x in range(no_of_clusters)]

    for key,value in territory_clusters.items():
        cluster_list[value].append(key)

    cluster_list_ordered = sorted(cluster_list,key=lambda x: len(x),reverse=True)
    non_abandoned_border_territories = game.state.get_all_border_territories(cluster_list_ordered[0])

    print("[handle_place_initial_troop_with_clusters] --> Clustered territories ordered {}".format(cluster_list_ordered),flush=True)
    print(f"[handle_place_initial_troop_with_clusters] - My territories: {my_territories}",flush=True)
    print(f"[handle_place_initial_troop_with_clusters] - Non abandoned territories: {cluster_list_ordered[0]}",flush=True)
    print(f"[handle_place_initial_troop_with_clusters] - Non abandoned Border territories: ",non_abandoned_border_territories,flush=True)
    print(f"[handle_place_initial_troop_with_clusters] - Abandoned border territories: ",list(set(my_territories) - set(cluster_list_ordered[0])),flush=True)


    #First place troops on border territories where there is a difference between their no of troops and the maximum no of enemy troops
    border_territory_placement = []
    for territory in non_abandoned_border_territories:
        adjuscent_territory = game.state.map.get_adjacent_to(territory)
        adjuscent_enemy = list(set(adjuscent_territory) - set(my_territories))
        max_enemy_troops = max([ game.state.territories[x].troops for x in adjuscent_enemy])
        difference = max_enemy_troops - game.state.territories[territory].troops

        if difference >= 1:
            border_territory_placement.append((territory,difference))

    border_territory_placement = sorted(border_territory_placement,key=lambda x: x[1], reverse=True)

    print(f"[handle_place_initial_troop_with_clusters] - Border territory difference is: {border_territory_placement}",flush=True)

    #If there is a border territory with less than the max of its negbouring enemies, add troops there starting with the one with the biggest differen
    if len(border_territory_placement) > 0:
        print(f"[handle_place_initial_troop_with_clusters] -- Placing a troop in {border_territory_placement[0][0]} because it has the greatest difference of {border_territory_placement[0][1]}")
        return game.move_place_initial_troop(query, border_territory_placement[0][0])
    else:
        #If all the territories have an equal number to the max of their enemy, place troops on the territory with the most troops
        max_troops = max(non_abandoned_border_territories,key=lambda x: game.state.territories[x].troops)
        print(f"[handle_place_initial_troop_with_clusters] -- All territories have an equal number to their largest enemy neighbouring force. place troops on {max_troops} because it has max troops of {game.state.territories[max_troops].troops}",flush=True)
        return game.move_place_initial_troop(query, max_troops)





#Place troops on territories that have a friendlies, when a territory has no friendly troop around it, abandone it
def handle_place_initial_troop_new(game: Game, bot_state: BotState, query: QueryPlaceInitialTroop) -> MovePlaceInitialTroop:
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
        # We will place troops along the territories on our border.
    all_border_territories = game.state.get_all_border_territories(
        game.state.get_territories_owned_by(game.state.me.player_id)
    )

    

    non_abandoned_border = []

    for border_t in all_border_territories:
        adjuscent = game.state.map.get_adjacent_to(border_t)
        adjuscent_owned = list(set(my_territories) & set(adjuscent))

        #Adjuscent friendly need to be more than 1
        if len(adjuscent_owned) > 1:
            non_abandoned_border.append(border_t)

    print("[handle_place_initial_troop_new] - Border territories: ",all_border_territories,flush=True)
    print("[handle_place_initial_troop_new] - Non abandoned Border territories: ",non_abandoned_border,flush=True)


    #Get friendly territory difference
    def get_enemy_terriroty_troops_difference(friendly_territories):
        border_territory_placement = []
        for friendly in friendly_territories:
            adjuscent = game.state.map.get_adjacent_to(friendly)
            adjuscent_enemy = list(set(adjuscent) - set(my_territories))
            enemy_troops = sum([ game.state.territories[x].troops for x in adjuscent_enemy])
            difference = enemy_troops - game.state.territories[friendly].troops

            if difference > 1:
                border_territory_placement.append((friendly,difference))

        border_territory_placement = sorted(border_territory_placement, key=lambda x: x[1],reverse=True)
        return border_territory_placement

    #If there are non abandoned territories

    if len(non_abandoned_border) > 0:
        # for border_t in non_abandoned_border:
        #     adjuscent = game.state.map.get_adjacent_to(border_t)
        #     adjuscent_enemy = list(set(adjuscent) - set(my_territories))
        #     enemy_troops = sum([ game.state.territories[x].troops for x in adjuscent_enemy])
        #     difference = enemy_troops - game.state.territories[border_t].troops

        #     if difference > 1:
        #         border_territory_placement.append((border_t,difference))

        border_territory_placement = get_enemy_terriroty_troops_difference(non_abandoned_border)
        print("[handle_place_initial_troop_new] - Non abandoned border territories is greater than 0")
        print("[handle_place_initial_troop_new] - Border territory placement: ",border_territory_placement,flush=True)

        if len(border_territory_placement) >=1:
            return game.move_place_initial_troop(query, border_territory_placement[0][0])
        else:
            max_troops = max(non_abandoned_border,key=lambda x: game.state.territories[x].troops)
            return game.move_place_initial_troop(query, max_troops)
        
    #If there are no non abandoned territories 
    else:
        print("[handle_place_initial_troop_new] - Non abandoned border territories is 0")
        home_base_territories = get_home_base_territories(game,home_base)
        home_base_border_territories = list(set(home_base_territories) & set(all_border_territories))

        home_base_border_territory_placement = get_enemy_terriroty_troops_difference(home_base_border_territories)

        print("[handle_place_initial_troop_new] - Home base territories: ",home_base_territories)
        print("[handle_place_initial_troop_new] - Home base border territories: ",home_base_border_territory_placement)

        if len(home_base_border_territory_placement) >= 1:
            return game.move_place_initial_troop(query, home_base_border_territory_placement[0][0])
        else:
            max_troops = max(home_base_territories,key=lambda x: game.state.territories[x].troops)
            return game.move_place_initial_troop(query, max_troops)










    #For territories bordered by just 1 player just place enoung troops to defend


def handle_place_initial_troop(game: Game, bot_state: BotState, query: QueryPlaceInitialTroop) -> MovePlaceInitialTroop:
    """After all the territories have been claimed, you can place a single troop on one
    of your territories each turn until each player runs out of troops."""

    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)

    # print("-------------------------------------------------------------------------------------------------",flush=True)
    # print("Mt territories: ",my_territories)
    home_base_territories = get_home_base_territories(game,home_base)
    # print("Home base territories: ",home_base_territories,flush=True)
    # print("-------------------------------------------------------------------------------------------------",flush=True)
    
    # We will place troops along the territories on our border.
    all_border_territories = game.state.get_all_border_territories(
        game.state.get_territories_owned_by(game.state.me.player_id)
    )

    #Place troops in border territories on home base
    border_territories_home_base = list(set(home_base_territories) & set(all_border_territories))
    
    # # We will place a troop in the border territory with the least troops currently
    # # on it. This should give us close to an equal distribution.
    border_territory_models = [game.state.territories[x] for x in border_territories_home_base]
    # #min_troops_territory = min(border_territory_models, key=lambda x: x.troops)
    max_troops_territory = max(border_territory_models, key=lambda x: x.troops)


    

    #return game.move_place_initial_troop(query, max_troops_territory.territory_id)
    return game.move_place_initial_troop(query, border_territories_home_base[0])


def handle_redeem_cards(game: Game, bot_state: BotState, query: QueryRedeemCards) -> MoveRedeemCards:
    """After the claiming and placing initial troops phases are over, you can redeem any
    cards you have at the start of each turn, or after killing another player."""

    # We will always redeem the minimum number of card sets we can until the 12th card set has been redeemed.
    # This is just an arbitrary choice to try and save our cards for the late game.

    print(f"[handle_redeem_cards] -- My current cards no: {len(game.state.me.cards)} which are {game.state.me.cards}")

    # We always have to redeem enough cards to reduce our card count below five.
    card_sets: list[Tuple[CardModel, CardModel, CardModel]] = []
    cards_remaining = game.state.me.cards.copy()

    #Before redeem cards when greater than 5
    while len(cards_remaining) >= 5:
        card_set = game.state.get_card_set(cards_remaining)

        # According to the pigeonhole principle, we should always be able to make a set
        # of cards if we have at least 5 cards.
        assert card_set != None
        card_sets.append(card_set)
        cards_remaining = [card for card in cards_remaining if card not in card_set]

    # Remember we can't redeem any more than the required number of card sets if 
    # we have just eliminated a player.

    # if game.state.card_sets_redeemed > 12 and query.cause == "turn_started":
    #     card_set = game.state.get_card_set(cards_remaining)
    #     while card_set != None:
    #         card_sets.append(card_set)
    #         cards_remaining = [card for card in cards_remaining if card not in card_set]
    #         card_set = game.state.get_card_set(cards_remaining)

    print(f"[handle_redeem_cards] -- Handling redeemed cards. No of already redeemed cards is {game.state.card_sets_redeemed}. My cards {cards_remaining}")

    ## Change and start redeeming cards when over 12 cards have been redeemed for greater effect
    if game.state.card_sets_redeemed > 20 and query.cause == "turn_started":
        card_set = game.state.get_card_set(cards_remaining)
        while card_set != None:
            card_sets.append(card_set)
            cards_remaining = [card for card in cards_remaining if card not in card_set]
            card_set = game.state.get_card_set(cards_remaining)
    print(f"[handle_redeem_cards] -- We have redeemed {len(card_sets)} cards")
    return game.move_redeem_cards(query, [(x[0].card_id, x[1].card_id, x[2].card_id) for x in card_sets])


def handle_distribute_troops(game: Game, bot_state: BotState, query: QueryDistributeTroops) -> MoveDistributeTroops:
    """After you redeem cards (you may have chosen to not redeem any), you need to distribute
    all the troops you have available across your territories. This can happen at the start of
    your turn or after killing another player.
    """

    # We will distribute troops across our border territories.
    total_troops = game.state.me.troops_remaining
    distributions = defaultdict(lambda: 0)
    border_territories = game.state.get_all_border_territories(
        game.state.get_territories_owned_by(game.state.me.player_id)
    )

    # We need to remember we have to place our matching territory bonus
    # if we have one.
    if len(game.state.me.must_place_territory_bonus) != 0:
        assert total_troops >= 2
        distributions[game.state.me.must_place_territory_bonus[0]] += 2
        total_troops -= 2


    # We will equally distribute across border territories in the early game,
    # but start doomstacking in the late game.
    if len(game.state.recording) < 4000:
        troops_per_territory = total_troops // len(border_territories)
        leftover_troops = total_troops % len(border_territories)
        for territory in border_territories:
            distributions[territory] += troops_per_territory
    
        # The leftover troops will be put some territory (we don't care)
        distributions[border_territories[0]] += leftover_troops
    
    else:
        my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
        weakest_players = sorted(game.state.players.values(), key=lambda x: sum(
            [game.state.territories[y].troops for y in game.state.get_territories_owned_by(x.player_id)]
        ))

        for player in weakest_players:
            bordering_enemy_territories = set(game.state.get_all_adjacent_territories(my_territories)) & set(game.state.get_territories_owned_by(player.player_id))
            if len(bordering_enemy_territories) > 0:
                print("my territories", [game.state.map.get_vertex_name(x) for x in my_territories])
                print("bordering enemies", [game.state.map.get_vertex_name(x) for x in bordering_enemy_territories])
                print("adjacent to target", [game.state.map.get_vertex_name(x) for x in game.state.map.get_adjacent_to(list(bordering_enemy_territories)[0])])
                selected_territory = list(set(game.state.map.get_adjacent_to(list(bordering_enemy_territories)[0])) & set(my_territories))[0]
                distributions[selected_territory] += total_troops
                break


    return game.move_distribute_troops(query, distributions)


def handle_attack_probability_simplified(game: Game, bot_state: BotState, query: QueryAttack) -> Union[MoveAttack, MoveAttackPass]:
    start = time.perf_counter()
     # We will attack someone.
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    bordering_territories = game.state.get_all_adjacent_territories(my_territories)
    
    #Attack from territory with the most troops
    my_territory_sorted = sorted(my_territories, key= lambda x: game.state.territories[x].troops,reverse=True )

    #We will decide on the territory to attack using the probability equation
    for attack_from in my_territory_sorted:
        print(f"[handle_attack_probability] Attack from for loop {(time.perf_counter() - start)*1000} milli seconds")
        #Attack territory with mostly surrounded by my territories
        attack_from_adjuscent = game.state.map.get_adjacent_to(attack_from)
        attack_from_adjuscent_enemies = list(set(attack_from_adjuscent) - set(my_territories))

        #Only try to attack if attack from territory has atleast 3 troops
        if game.state.territories[attack_from].troops >= 3 and len(attack_from_adjuscent_enemies) > 0:
            print("[handle_attack_new_new] --> Attack from territory has {} troops, and is surrounded by {} enemies".format(game.state.territories[attack_from].troops,len(attack_from_adjuscent_enemies)))

            #Getting troops from attack from location
            attack_from_troops = game.state.territories[attack_from].troops - 1
            attack_from_no_of_troops = game.state.territories[attack_from].troops

            #Get most surrounded enemy territory
            def territory_most_surrounded(territory):
                adjuscent = game.state.map.get_adjacent_to(territory)
                adjuscent_friendly = list(set(game.state.map.get_adjacent_to(territory)) & set(game.state.get_territories_owned_by(game.state.me.player_id)))
                return len(adjuscent) / len(adjuscent_friendly)
                

            print(f"[handle_attack_probability] Before sorting candidate attack {(time.perf_counter() - start)*1000} milli seconds")
            candidate_enemy_attack = sorted(attack_from_adjuscent_enemies,key=territory_most_surrounded)
            print(f"[handle_attack_probability] After sorting candidate attack {(time.perf_counter() - start)*1000} milli seconds")

            candidate_enemy_attack_and_troops = [(x,game.state.territories[x].troops) for x in candidate_enemy_attack]


            print(f"[handle_attack_probability] --> [NEW-TEST] Territory {attack_from} troops {attack_from_no_of_troops}. Possible candidates to attack and troops: {candidate_enemy_attack_and_troops}",flush=True)


            #Get territories where the attack probability is greater than probability threshold 
        

            #Attack first enemy with an attack probability greater than the threshold
            for candidate in candidate_enemy_attack:
                #Only atack if you have 3 more than the adjuscent enemy except the one you are attacking
                #Find maximum amount of adjuscent enemies around except the one attacking

                print(f"[handle_attack_probability] Before getting max adjuscent enemies {(time.perf_counter() - start)*1000} milli seconds")
                if len(candidate_enemy_attack) == 1:
                    max_adjuscent_enemies = 0
                else:
                    max_adjuscent_enemies = max([ game.state.territories[x].troops for x in candidate_enemy_attack if x != candidate])
                print(f"[handle_attack_probability] After getting max adjuscent enemies {(time.perf_counter() - start)*1000} milli seconds")

                #Only atack if you have 3 more than the adjuscent enemy
                if (attack_from_no_of_troops - max_adjuscent_enemies) < 2:
                    print(f"[handle_attack_probability] -- [NEW] Abandoned attack because attack from troops are {attack_from_no_of_troops} and max adjuscent enemies are {max_adjuscent_enemies}. Hence it is less than 3")
                    continue

                print(f"[handle_attack_probability] Before getting to_attack_enemy {(time.perf_counter() - start)*1000} milli seconds")
                to_attack_enemy = to_attack(attack_from_troops,game.state.territories[candidate].troops)
                print(f"[handle_attack_probability] After getting to_attack_enemy {(time.perf_counter() - start)*1000} milli seconds")

                #Attack first candidate where the attack probability is greater than threshold
                if to_attack_enemy:
                    print(f"[handle_attack_probability] --> Attacking from {attack_from} which has {attack_from_no_of_troops} to {candidate} which has {game.state.territories[candidate].troops} troops")
                    print(f"[handle_attack_probability] Before return {(time.perf_counter() - start)*1000} milli seconds")
                    #Attack with a minimum of 3 soldiers of the troops available
                    return game.move_attack(query,attack_from, candidate, min(3, attack_from_troops))
                else:
                    print(f"[handle_attack_probability] --> Not Attacking from {attack_from} which has {attack_from_no_of_troops} to {candidate} which has {game.state.territories[candidate].troops} troops because probability of success and below threshold")

        else:
            print(f"[handle_attack_probability] --> Passing attack from {attack_from}. Reason troops: {game.state.territories[attack_from].troops} or enemies: {attack_from_adjuscent_enemies}")
            pass
            
            
    print(f"[handle_attack_probability] [CHECK] --> There is no adjuscent territory available for attack at all. Proceeding without attack")
    return game.move_attack_pass(query)


def handle_attack_probability(game: Game, bot_state: BotState, query: QueryAttack) -> Union[MoveAttack, MoveAttackPass]:
    start = time.perf_counter()
     # We will attack someone.
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    bordering_territories = game.state.get_all_adjacent_territories(my_territories)
    
    #Attack from territory with the most troops
    my_territory_sorted = sorted(my_territories, key= lambda x: game.state.territories[x].troops,reverse=True )

    #We will decide on the territory to attack using the probability equation
    for attack_from in my_territory_sorted:
        print(f"[handle_attack_probability] Attack from for loop {(time.perf_counter() - start)*1000} milli seconds")
        #Attack territory with mostly surrounded by my territories
        attack_from_adjuscent = game.state.map.get_adjacent_to(attack_from)
        attack_from_adjuscent_enemies = list(set(attack_from_adjuscent) - set(my_territories))

        #Only try to attack if attack from territory has atleast 3 troops
        if game.state.territories[attack_from].troops >= 3 and len(attack_from_adjuscent_enemies) > 0:
            print("[handle_attack_new_new] --> Attack from territory has {} troops, and is surrounded by {} enemies".format(game.state.territories[attack_from].troops,len(attack_from_adjuscent_enemies)))

            #Getting troops from attack from location
            attack_from_troops = game.state.territories[attack_from].troops - 1
            attack_from_no_of_troops = game.state.territories[attack_from].troops

            #Get most surrounded enemy territory
            def territory_most_surrounded(territory):
                adjuscent = game.state.map.get_adjacent_to(territory)
                adjuscent_friendly = list(set(game.state.map.get_adjacent_to(territory)) & set(game.state.get_territories_owned_by(game.state.me.player_id)))
                return len(adjuscent) / len(adjuscent_friendly)
                

            print(f"[handle_attack_probability] Before sorting candidate attack {(time.perf_counter() - start)*1000} milli seconds")
            candidate_enemy_attack = sorted(attack_from_adjuscent_enemies,key=territory_most_surrounded)
            print(f"[handle_attack_probability] After sorting candidate attack {(time.perf_counter() - start)*1000} milli seconds")

            candidate_enemy_attack_and_troops = [(x,game.state.territories[x].troops) for x in candidate_enemy_attack]


            print(f"[handle_attack_probability] --> [NEW-TEST] Territory {attack_from} troops {attack_from_no_of_troops}. Possible candidates to attack and troops: {candidate_enemy_attack_and_troops}",flush=True)


            #Get territories where the attack probability is greater than probability threshold 
        

            #Attack first enemy with an attack probability greater than the threshold
            for candidate in candidate_enemy_attack:
                #Only atack if you have 3 more than the adjuscent enemy except the one you are attacking
                #Find maximum amount of adjuscent enemies around except the one attacking

                print(f"[handle_attack_probability] Before getting max adjuscent enemies {(time.perf_counter() - start)*1000} milli seconds")
                if len(candidate_enemy_attack) == 1:
                    max_adjuscent_enemies = 0
                else:
                    max_adjuscent_enemies = max([ game.state.territories[x].troops for x in candidate_enemy_attack if x != candidate])
                print(f"[handle_attack_probability] After getting max adjuscent enemies {(time.perf_counter() - start)*1000} milli seconds")

                #Only atack if you have 3 more than the adjuscent enemy
                if (attack_from_no_of_troops - max_adjuscent_enemies) < 2:
                    print(f"[handle_attack_probability] -- [NEW] Abandoned attack because attack from troops are {attack_from_no_of_troops} and max adjuscent enemies are {max_adjuscent_enemies}. Hence it is less than 3")
                    continue

                print(f"[handle_attack_probability] Before getting attack success probability {(time.perf_counter() - start)*1000} milli seconds")
                attack_success_prob = p_obj.battleprob(attack_from_troops,game.state.territories[candidate].troops)
                print(f"[handle_attack_probability] After getting attack success probability {(time.perf_counter() - start)*1000} milli seconds")

                #Attack first candidate where the attack probability is greater than threshold
                if attack_success_prob >= attack_probability_threshold:
                    print(f"[handle_attack_probability] --> Attacking from {attack_from} to {candidate} probability of success {attack_success_prob}")
                    print(f"[handle_attack_probability] Before return {(time.perf_counter() - start)*1000} milli seconds")
                    #Attack with a minimum of 3 soldiers of the troops available
                    return game.move_attack(query,attack_from, candidate, min(3, attack_from_troops))
                else:
                    print(f"[handle_attack_probability] --> Not attacking from {attack_from} to {candidate} because probability of success {attack_success_prob} and below threshold")

        else:
            print(f"[handle_attack_probability] --> Passing attack from {attack_from}. Reason troops: {game.state.territories[attack_from].troops} or enemies: {attack_from_adjuscent_enemies}")
            pass
            
            
    print(f"[handle_attack_probability] [CHECK] --> There is no adjuscent territory available for attack at all. Proceeding without attack")
    return game.move_attack_pass(query)

def handle_attack_new_new(game: Game, bot_state: BotState, query: QueryAttack) -> Union[MoveAttack, MoveAttackPass]:
    # We will attack someone.
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    bordering_territories = game.state.get_all_adjacent_territories(my_territories)
    
    #Attack from territory with the most troops
    my_territory_sorted = sorted(my_territories, key= lambda x: game.state.territories[x].troops,reverse=True )

    #print("My territories: ",my_territories,flush=True)
    #print("Attack home: {}. Has {} troops".format(attack_from,game.state.territories[attack_from].troops),flush=True)

    print("[handle_attack_new_new] --> Hand attack new new")

    print("[TEST] --> ",p_obj.battleprob(3,3,2))

    #battleprob


    for attack_from in my_territory_sorted:
        #Attack territory with mostly surrounded by my territories
        attack_from_adjuscent = game.state.map.get_adjacent_to(attack_from)
        attack_from_adjuscent_enemies = list(set(attack_from_adjuscent) - set(my_territories))

        if game.state.territories[attack_from].troops > 3 and len(attack_from_adjuscent_enemies) > 0:
            print("[handle_attack_new_new] --> Attack from territory has {} troops, and is surrounded by {} enemies".format(game.state.territories[attack_from].troops,len(attack_from_adjuscent_enemies)))

            #Get most surrounded enemy territory
            def territory_most_surrounded(territory):
                adjuscent = game.state.map.get_adjacent_to(territory)
                adjuscent_friendly = list(set(game.state.map.get_adjacent_to(territory)) & set(game.state.get_territories_owned_by(game.state.me.player_id)))
                return len(adjuscent) / len(adjuscent_friendly)
            
            candidate_attack = sorted(attack_from_adjuscent_enemies,key=territory_most_surrounded)[0]

            print("[DEFENDER] --> We plan to attack from {} to {}. Defender has {} troops".format(attack_from,candidate_attack,game.state.territories[candidate_attack].troops),flush=True)

            if game.state.territories[attack_from].troops > game.state.territories[attack_from].troops:
                pass

            move = game.move_attack(query,attack_from, candidate_attack, min(3, game.state.territories[attack_from].troops - 1))
            return move
        
    print("[CHECK] --> We do NOT have an enemy adjuscent to our stronghold",flush=True)
    return game.move_attack_pass(query)






def handle_attack_new(game: Game, bot_state: BotState, query: QueryAttack) -> Union[MoveAttack, MoveAttackPass]:
    # We will attack someone.
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    bordering_territories = game.state.get_all_adjacent_territories(my_territories)
    
    #Attack from territory with the most troops
    attack_from = sorted(my_territories, key= lambda x: game.state.territories[x].troops,reverse=True )[0]

    #print("My territories: ",my_territories,flush=True)
    #print("Attack home: {}. Has {} troops".format(attack_from,game.state.territories[attack_from].troops),flush=True)

    #Attack territory with mostly surrounded by my territories
    attack_from_adjuscent = game.state.map.get_adjacent_to(attack_from)
    attack_from_adjuscent_enemies = list(set(attack_from_adjuscent) - set(my_territories))

    if game.state.territories[attack_from].troops > 3:
        if len(attack_from_adjuscent_enemies) != 0:
            #print("We have an enemy adjuscent to our stronghold")
            def territory_most_surrounded(territory):
                adjuscent = game.state.map.get_adjacent_to(territory)
                adjuscent_friendly = list(set(game.state.map.get_adjacent_to(territory)) & set(game.state.get_territories_owned_by(game.state.me.player_id)))
                return len(adjuscent) / len(adjuscent_friendly)
            candidate_attack = sorted(attack_from_adjuscent_enemies,key=territory_most_surrounded)[0]
            #print("Attacking {} from {} ".format(candidate_attack,attack_from),flush=True)


            move = game.move_attack(query,attack_from, candidate_attack, min(3, game.state.territories[attack_from].troops - 1))
            return move
        else:
            #print("We do NOT have an enemy adjuscent to our stronghold",flush=True)
            return game.move_attack_pass(query)
    else:
        #print("No territory has more than 3 troops",flush=True)
        return game.move_attack_pass(query)



def handle_attack(game: Game, bot_state: BotState, query: QueryAttack) -> Union[MoveAttack, MoveAttackPass]:
    """After the troop phase of your turn, you may attack any number of times until you decide to
    stop attacking (by passing). After a successful attack, you may move troops into the conquered
    territory. If you eliminated a player you will get a move to redeem cards and then distribute troops."""
    
    # We will attack someone.
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    bordering_territories = game.state.get_all_adjacent_territories(my_territories)

    def attack_weakest(territories: list[int]) -> Optional[MoveAttack]:
        # We will attack the weakest territory from the list.
        territories = sorted(territories, key=lambda x: game.state.territories[x].troops)
        for candidate_target in territories:
            candidate_attackers = sorted(list(set(game.state.map.get_adjacent_to(candidate_target)) & set(my_territories)), key=lambda x: game.state.territories[x].troops, reverse=True)
            for candidate_attacker in candidate_attackers:
                if game.state.territories[candidate_attacker].troops > 1:
                    return game.move_attack(query, candidate_attacker, candidate_target, min(3, game.state.territories[candidate_attacker].troops - 1))


    if len(game.state.recording) < 4000:
        # We will check if anyone attacked us in the last round.
        new_records = game.state.recording[game.state.new_records:]
        enemy = None
        for record in new_records:
            match record:
                case MoveAttack() as r:
                    if r.defending_territory in set(my_territories):
                        enemy = r.move_by_player

        # If we don't have an enemy yet, or we feel angry, this player will become our enemy.
        if enemy != None:
            if bot_state.enemy == None or random.random() < 0.05:
                bot_state.enemy = enemy
        
        # If we have no enemy, we will pick the player with the weakest territory bordering us, and make them our enemy.
        else:
            weakest_territory = min(bordering_territories, key=lambda x: game.state.territories[x].troops)
            bot_state.enemy = game.state.territories[weakest_territory].occupier
            
        # We will attack their weakest territory that gives us a favourable battle if possible.
        enemy_territories = list(set(bordering_territories) & set(game.state.get_territories_owned_by(enemy)))
        move = attack_weakest(enemy_territories)
        if move != None:
            return move
        
        # Otherwise we will attack anyone most of the time.
        if random.random() < 0.8:
            move = attack_weakest(bordering_territories)
            if move != None:
                return move

    # In the late game, we will attack anyone adjacent to our strongest territories (hopefully our doomstack).
    else:
        strongest_territories = sorted(my_territories, key=lambda x: game.state.territories[x].troops, reverse=True)
        for territory in strongest_territories:
            move = attack_weakest(list(set(game.state.map.get_adjacent_to(territory)) - set(my_territories)))
            if move != None:
                return move

    return game.move_attack_pass(query)






def handle_troops_after_attack_new(game: Game, bot_state: BotState, query: QueryTroopsAfterAttack) -> MoveTroopsAfterAttack:
    # First we need to get the record that describes the attack, and then the move that specifies
    # which territory was the attacking territory.
    record_attack = cast(RecordAttack, game.state.recording[query.record_attack_id])
    move_attack = cast(MoveAttack, game.state.recording[record_attack.move_attack_id])
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    attacking_territory = move_attack.attacking_territory
    #defending_territory = move_attack.defending_territory

    attacking_territory_adjuscent = game.state.map.get_adjacent_to(attacking_territory)
    attacking_territory_adjuscent_enemy = list(set(attacking_territory_adjuscent) - set(my_territories))

    # print("",flush=True)
    # print(f"[handle_troops_after_attack_new_test] -- Query: {query}. ")
    # print("",flush=True)
    # print(f"[handle_troops_after_attack_new_test] -- Record attack id: {query.record_attack_id}")
    # print("",flush=True)

    # print(f"[handle_troops_after_attack_new] --[NEW-TEST] --> Details about game.state.mao {game.state.map} game state.map. Trying methods such as _continents: {game.state.map._continents} and _edges: {game.state.map._edges} and _vertex_names: {game.state.map._vertex_names} and get_continents: {game.state.map.get_continents} and get_vertex_name: {game.state.map.get_vertex_name} and get_vertices: {game.state.map.get_vertices} and is_adjacent: {game.state.map.is_adjacent}")


    # #['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_check_graph_validity', '_continent_bonuses', '_continents', '_edges', '_vertex_names', '_vertices', 'get_adjacent_to', 'get_continent_bonus', 'get_continents', 'get_vertex_name', 'get_vertices', 'is_adjacent']

    if len(attacking_territory_adjuscent_enemy) == 0:
        print("[handle_troops_after_attack_new] --> There are no adjuscent enemies around from territory",flush=True)
        territory_troops = game.state.territories[move_attack.attacking_territory].troops - 1
        print("[handle_troops_after_attack_new] --> We are therefore moving {} troops".format(territory_troops))
        #Move max
        return game.move_troops_after_attack(query,territory_troops)
    else:
        #Move troops less adjuscent enemies max
        adjuscent_enemies_max_troops = max([ game.state.territories[x].troops for x in attacking_territory_adjuscent_enemy])
        desired_move_value = game.state.territories[move_attack.attacking_territory].troops - adjuscent_enemies_max_troops
        troop_move_no = max(move_attack.attacking_troops,desired_move_value)

        print(f"[handle_troops_after_attack_new] --> Territory {move_attack.attacking_territory} has {game.state.territories[move_attack.attacking_territory].troops} troops. Max enemy adjuscent is {adjuscent_enemies_max_troops}. Desired move no is {desired_move_value} actual no of troops {troop_move_no}",flush=True)

        # We will always move the maximum number of troops we can.
        
        return game.move_troops_after_attack(query,troop_move_no)

def handle_troops_after_attack(game: Game, bot_state: BotState, query: QueryTroopsAfterAttack) -> MoveTroopsAfterAttack:
    """After conquering a territory in an attack, you must move troops to the new territory."""
    
    # First we need to get the record that describes the attack, and then the move that specifies
    # which territory was the attacking territory.
    record_attack = cast(RecordAttack, game.state.recording[query.record_attack_id])
    move_attack = cast(MoveAttack, game.state.recording[record_attack.move_attack_id])

    # We will always move the maximum number of troops we can.
    return game.move_troops_after_attack(query, game.state.territories[move_attack.attacking_territory].troops - 1)


def handle_defend(game: Game, bot_state: BotState, query: QueryDefend) -> MoveDefend:
    """If you are being attacked by another player, you must choose how many troops to defend with."""

    # We will always defend with the most troops that we can.

    # First we need to get the record that describes the attack we are defending against.
    move_attack = cast(MoveAttack, game.state.recording[query.move_attack_id])
    defending_territory = move_attack.defending_territory
    
    # We can only defend with up to 2 troops, and no more than we have stationed on the defending
    # territory.
    defending_troops = min(game.state.territories[defending_territory].troops, 2)
    return game.move_defend(query, defending_troops)

def handle_fortify_new(game: Game, bot_state: BotState, query: QueryFortify) -> Union[MoveFortify, MoveFortifyPass]:
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    inland_territories = []


    for territory in my_territories:
        adjuscent = game.state.map.get_adjacent_to(territory)
        adjuscent_enemy = list(set(adjuscent) - set(my_territories))

        #Find an inland territory with more than 2 troop
        if len(adjuscent_enemy) == 0 and game.state.territories[territory].troops >= 2:
            #print("Territory {} has no adjuscent enemy and has {} troops ".format(territory,game.state.territories[territory].troops),flush=True)
            inland_territories.append(territory)

    #Sort acccording to number of troops
    inland_territories = sorted(inland_territories,key=lambda x: game.state.territories[x].troops,reverse=True)
    inland_territories_troops = [(x,game.state.territories[x].troops) for x in inland_territories]

    print(flush=True)
    print(flush=True)
    print("My territories: ",my_territories,flush=True)
    print("Inland territory(no,troops): ",inland_territories_troops,flush=True)

    print("[TEST] -- ",game.state.territories[0],flush=True)

    #If we have inland territories we move them towards the strongest enemy. 
    if len(inland_territories) > 0:
        # We will always fortify towards the most powerful player (player with most troops on the map) to defend against them.
        total_troops_per_player = {}
        for player in game.state.players.values():
            total_troops_per_player[player.player_id] = sum([game.state.territories[x].troops for x in game.state.get_territories_owned_by(player.player_id)])

        most_powerful_players = sorted(total_troops_per_player.items(), key=lambda x: x[1],reverse=True)
        print("Most powerful players: ",most_powerful_players,flush=True)

        # If we are the most powerful, we move inland troops to the location with most troops, if we are not the most powerful player we move towards the most powerful player
        if most_powerful_players[0][0] == game.state.me.player_id:
            print("We are the strongest player",flush=True)


            border_territories = game.state.get_all_border_territories(my_territories)
            border_territories_ordered = sorted(border_territories,key=lambda x: game.state.territories[x].troops,reverse=True)
            border_territories_ordered_troops = [(x,game.state.territories[x].troops) for x in border_territories_ordered]


            for inland_territory in inland_territories:

                print("Border territory troops: ",border_territories_ordered_troops,flush=True)

                for border_territory in border_territories_ordered:
                    shortest_path = shortest_connected_path(game,inland_territory,border_territory)
                    print("Shortest path between {} and {} is {}".format(inland_territory,border_territory,shortest_path))

                    if len(shortest_path) >= 2:
                        print("----> Moving {} troops from {} to {} towards {}".format(game.state.territories[inland_territory].troops - 1,shortest_path[0],shortest_path[1],border_territory))
                        return game.move_fortify(query, shortest_path[0], shortest_path[1], game.state.territories[inland_territory].troops - 1)

            print("[handle_fortify_new] --> There is no shortest path")
            #Uf there is no nearby territory, will probably never reach
            return game.move_fortify_pass(query)
        else:
            print("We are NOT the strongest player",flush=True)
            border_territories = game.state.get_all_border_territories(my_territories)
            

            for powerful_player in most_powerful_players:

                border_territories_to_fortify = [] #(territory_id,no_of_troops)
                for border_territory in border_territories:
                    adjuscent_to_border = game.state.map.get_adjacent_to(border_territory)
                    territories_owned_by_powerful_player = game.state.get_territories_owned_by(powerful_player[0])

                    adjuscent_owned = list(set(adjuscent_to_border) & set(territories_owned_by_powerful_player))

                    if len(adjuscent_owned) > 0:
                        print("[handle_fortify_new] -- There is an adjuscent territory owned by {}".format(powerful_player))
                        print("[handle_fortify_new] -- Terriroty: ",adjuscent_owned)
                        border_territories_to_fortify.append((border_territory,game.state.territories[border_territory].troops))

                    
                #Fortify territory with the most troops
                border_territories_to_fortify = sorted(border_territories_to_fortify, key=lambda x: x[1],reverse=True)

                for inland_territory in inland_territories:
                    for border_territory in border_territories_to_fortify:

                        shortest_path = shortest_connected_path(game,inland_territory,border_territory[0])
                        print("Shortest path between {} and {} is {}".format(inland_territory,border_territory,shortest_path))

                        if len(shortest_path) >= 2:
                            print("----> Moving {} troops from {} to {} towards {}".format(game.state.territories[inland_territory].troops - 1,shortest_path[0],shortest_path[1],border_territory))
                            return game.move_fortify(query, shortest_path[0], shortest_path[1], game.state.territories[inland_territory].troops - 1)



            print("[handle_fortify_new] --> Investigate why")
            return game.move_fortify_pass(query)
    else:
        print("[handle_fortify_new] --> No inland territories")
        return game.move_fortify_pass(query)
    

    





def handle_fortify(game: Game, bot_state: BotState, query: QueryFortify) -> Union[MoveFortify, MoveFortifyPass]:
    """At the end of your turn, after you have finished attacking, you may move a number of troops between
    any two of your territories (they must be adjacent)."""


    # We will always fortify towards the most powerful player (player with most troops on the map) to defend against them.
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    total_troops_per_player = {}
    for player in game.state.players.values():
        total_troops_per_player[player.player_id] = sum([game.state.territories[x].troops for x in game.state.get_territories_owned_by(player.player_id)])

    most_powerful_player = max(total_troops_per_player.items(), key=lambda x: x[1])[0]

    # If we are the most powerful, we will pass.
    if most_powerful_player == game.state.me.player_id:
        return game.move_fortify_pass(query)
    
    # Otherwise we will find the shortest path between our territory with the most troops
    # and any of the most powerful player's territories and fortify along that path.
    candidate_territories = game.state.get_all_border_territories(my_territories)
    most_troops_territory = max(candidate_territories, key=lambda x: game.state.territories[x].troops)

    # To find the shortest path, we will use a custom function.
    shortest_path = find_shortest_path_from_vertex_to_set(game, most_troops_territory, set(game.state.get_territories_owned_by(most_powerful_player)))
    # We will move our troops along this path (we can only move one step, and we have to leave one troop behind).
    # We have to check that we can move any troops though, if we can't then we will pass our turn.
    if len(shortest_path) > 0 and game.state.territories[most_troops_territory].troops > 1:
        return game.move_fortify(query, shortest_path[0], shortest_path[1], game.state.territories[most_troops_territory].troops - 1)
    else:
        return game.move_fortify_pass(query)


def find_shortest_path_from_vertex_to_set(game: Game, source: int, target_set: set[int]) -> list[int]:
    """Used in move_fortify()."""

    # We perform a BFS search from our source vertex, stopping at the first member of the target_set we find.
    queue = deque()
    queue.appendleft(source)

    current = queue.pop()
    parent = {}
    seen = {current: True}

    while len(queue) != 0:
        if current in target_set:
            break

        for neighbour in game.state.map.get_adjacent_to(current):
            if neighbour not in seen:
                seen[neighbour] = True
                parent[neighbour] = current
                queue.appendleft(neighbour)

        current = queue.pop()

    path = []
    while current in parent:
        path.append(current)
        current = parent[current]

    return path[::-1]

def are_connected(game:Game, source:int, destination:int) -> bool:
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    checked = set()

    def connected_recersion(sorce_des):
        adjuscent = game.state.map.get_adjacent_to(sorce_des)
        adjuscent_owned = list(set(adjuscent) & set(my_territories))
        checked.add(sorce_des)

        # print("Source: {} Destination: {}".format(sorce_des,destination),flush=True)
        # print("Adjuscent territories: ",adjuscent)
        # print("Adjuscent owned territories: ",adjuscent_owned)

        if destination == sorce_des:
            #print("The are connected")
            return True
        else:
            for t in adjuscent_owned:
                if t not in checked:
                    return connected_recersion(t)
                
        # print("They are not connected",flush=True)
        # return False

    value = connected_recersion(source)

        
    return value if value is not None else False

def connection_path(game:Game, source:int, destination:int):
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    checked = set()
    path = []

    def connected_recersion(sorce_des):
        adjuscent = game.state.map.get_adjacent_to(sorce_des)
        adjuscent_owned = list(set(adjuscent) & set(my_territories))
        checked.add(sorce_des)

        
        
        path.append(sorce_des)

        # print("Source: {} Destination: {}".format(sorce_des,destination),flush=True)
        # print("Adjuscent territories: ",adjuscent,flush=True)
        # print("Adjuscent owned territories: ",adjuscent_owned,flush=True)

        if destination == sorce_des:
            print("----------------The are connected",flush=True)
            return path
        else:
            for t in adjuscent_owned:
                if t not in checked:
                    return connected_recersion(t)
        path.pop()
                
        # print("They are not connected",flush=True)
        # return False

    path = connected_recersion(source)

    if path == None:
        print("The are not connected")
        return []
    else:
        return path

def shortest_connected_path(game:Game, source:int, destination:int):
    my_territories = game.state.get_territories_owned_by(game.state.me.player_id)
    checked = set()
    path = []

    def connected_recersion(sorce_des):
        adjuscent = game.state.map.get_adjacent_to(sorce_des)
        adjuscent_owned = list(set(adjuscent) & set(my_territories))
        checked.add(sorce_des)

        path.append(sorce_des)

        if destination in adjuscent_owned:
            path.append(destination)
            return path
        else:
            for t in adjuscent_owned:
                if t not in checked:
                    return connected_recersion(t)
        path.pop()

                

    value = connected_recersion(source)
    final_value = []

    # print("[Inside]Value of path: ",path)
    # print("[Inside]Value of value: ",value)


    if value == None:
        #print("[Inside] Shortest path between {} and {} = {}".format(source,destination,None))
        return []
    else:
        next_value = 0
        while True:
            final_value.append(value[next_value])

            if next_value == len(value) - 1:
                break

            adjuscent = game.state.map.get_adjacent_to(value[next_value])
            adjuscent_list = list(set(value) & set(adjuscent))

            next_value = max([ value.index(x) for x in adjuscent_list])
            

        #print("[Inside] Shortest path between {} and {} = {} and first path {}".format(source,destination,final_value,value))
        return final_value
    

#Function to determine if a player should attack or not
def to_attack(no_attacker,no_defender):
    attack_probability_threshold = 0.7
    #p_obj
    if no_attacker <= 100 and no_defender <= 100:
        success_probability = p_obj.battleprob(no_attacker,no_defender)
        return True if success_probability >= attack_probability_threshold else False
    else:
        if no_attacker >= no_defender:
            return True
        else:
            return False


    
class risk_probability:

    def __init__(self):
        twodice = [[0]*6 for i in range(6)]
        threedice = [[0]*6 for i in range(6)]

        # get number of ways to have two dice with particular values,
        # as well as three dice where the highest 2 have particular values
        for i in range(6):
            for j in range(6):
                twodice[min(i,j)][max(i,j)] += 1
                for k in range(6):
                    ordered = sorted([i,j,k])
                    threedice[ordered[1]][ordered[2]] += 1

        total2dice = sum(sum(arr) for arr in twodice)
        total3dice = sum(sum(arr) for arr in threedice)

        flawless3v2 = 0 # probability of attacker rolling 3 dice against 2 and losing no pieces
        flawless2v2 = 0 # probability of attacker rolling 2 dice against 2 and losing no pieces
        for h in range(5):
            for i in range(h,5):
                # prob of defender rolling rolling h and i
                # we divide by attacker sample space now to avoid doing it repeatedly later
                temp3v2 = float(twodice[h][i])/(total2dice*total3dice)
                temp2v2 = float(twodice[h][i])/(total2dice*total2dice)
                for j in range(h+1,6):
                    for k in range(i+1,6):
                        # going through all ways attacker can defeat two armies
                        # without losing anybody in the process.
                        flawless3v2 += temp3v2*threedice[j][k]
                        flawless2v2 += temp2v2*twodice[j][k]

        flawed3v2 = 0 # probability of attacker rolling 3v2 and each losing 1 piece
        flawed2v2 = 0 # probability of attacker rolling 2v2 and each losing 1 piece
        for h in range(5):
            for i in range(h,6):
                # prob of defender rolling h and i
                # once again we factor out division of attacker sample space
                temp3v2 = float(twodice[h][i])/(total2dice*total3dice)
                temp2v2 = float(twodice[h][i])/(total2dice*total2dice)
                for j in range(h+1,6):
                    for k in range(j,i+1):
                        # attacker defeats low die but loses to high die
                        flawed3v2 += temp3v2*threedice[j][k]
                        flawed2v2 += temp2v2*twodice[j][k]
                if i==5: continue # attacker cannot beat high die
                for j in range(h+1):
                    for k in range(i+1,6):
                        # attacker defeats high die but loses to low die
                        flawed3v2 += temp3v2*threedice[j][k]
                        flawed2v2 += temp2v2*twodice[j][k]

        fatal3v2 = 1-flawless3v2-flawed3v2 # attacker loses two when rolling 3
        fatal2v2 = 1-flawless2v2-flawed2v2 # attacker loses two when rolling 2

        flawless1v2 = 0 # probability of attacker rolling 1 die and winning against 2 dice
        for i in range(5):
            for j in range(i,5):
                # prob of defender rolling i and j
                # factor out division by six (attacker sample space)
                temp1v2 = float(twodice[i][j])/(total2dice*6)
                for k in range(j+1,6):
                    flawless1v2 += temp1v2

        fatal1v2 = 1-flawless1v2 # probability of attacker rolling 1v2 and losing

        flawless3v1 = 0 # probability of attacker rolling 3v1 and winning
        flawless2v1 = 0 # probability of attacker rolling 2v1 and winning
        for i in range(5):
            temp3v1 = 1.0/(6*total3dice)
            temp2v1 = 1.0/(6*total2dice)
            for j in range(6):
                for k in range(max(j,i+1),6):
                    flawless3v1 += temp3v1*threedice[j][k]
                    flawless2v1 += temp2v1*twodice[j][k]

        fatal3v1 = 1-flawless3v1 # probability of attacker rolling 3v1 and losing
        fatal2v1 = 1-flawless2v1 # probabiliyy of attacker rolling 2v1 and losing


        flawless1v1 = 0 # prob of attacker rolling 1v1 and winning
        for i in range(5):
            for j in range(i+1,6):
                flawless1v1 += 1.0/36

        fatal1v1 = 1-flawless1v1

        # self.probs[x][y][z] means probability of attacker using x dice vs y dice with outcome z
        # (z=0 is a win, z=1 is a tie, z=2 is a loss)
        self.probs = [0, [0, [flawless1v1,0.0,fatal1v1], [flawless1v2,0.0,fatal1v2]],
                    [0, [flawless2v1,0.0,fatal2v1], [flawless2v2,flawed2v2,fatal2v2]],
                    [0, [flawless3v1,0.0,fatal3v1], [flawless3v2,flawed3v2,fatal3v2]]]
        self.bmem = {}
        self.omem = {}
        self.tmem = {}

    # Finds probability that army of size attackers will
    # defeat army of size defenders with at least minleft troops left.
    # Less general than outcomeprob.
    def battleprob(self,attackers, defenders, minleft=1):
        if attackers < minleft: return 0.0
        if defenders == 0: return 1.0

        h = (attackers, defenders, minleft)
        if h in self.bmem: return self.bmem[h]

        val = 0.0
        if attackers >= 3 and defenders >= 2:
            val = self.probs[3][2][0]*self.battleprob(attackers, defenders-2, minleft) + \
                self.probs[3][2][1]*self.battleprob(attackers-1, defenders-1, minleft) + \
                self.probs[3][2][2]*self.battleprob(attackers-2, defenders, minleft)
        elif attackers >= 3 and defenders == 1:
            val = self.probs[3][1][0] + \
                self.probs[3][1][2]*self.battleprob(attackers-1, defenders, minleft)
        elif attackers == 2 and defenders >= 2:
            val = self.probs[2][2][0]*self.battleprob(attackers, defenders-2, minleft) + \
                self.probs[2][2][1]*self.battleprob(attackers-1, defenders-1, minleft) + \
                self.probs[2][2][2]*self.battleprob(attackers-2, defenders, minleft)
        elif attackers == 2 and defenders == 1:
            val = self.probs[2][1][0] + \
                self.probs[2][1][2]*self.battleprob(attackers-1, defenders, minleft)
        elif attackers == 1 and defenders >= 2:
            val = self.probs[1][2][0]*self.battleprob(attackers, defenders-1, minleft)
        elif attackers == 1 and defenders == 1:
            val = self.probs[1][1][0]

        self.bmem[h] = val
        return val

    # Finds probability that an army of size attackers
    # battling an army of size defenders will result in
    # arem attackers and drem attackers remaining on either side.
    def outcomeprob(self,attackers, defenders, arem=1, drem=0):
        if attackers < arem or defenders < drem: return 0.0
        if defenders == drem:
            if drem == 0 and attackers != arem: return 0.0
            if attackers == arem: return 1.0

        h = (attackers, defenders, arem, drem)
        if h in self.omem: return self.omem[h]

        val = 0.0
        if attackers >= 3 and defenders >= 2:
            val = self.probs[3][2][0]*self.outcomeprob(attackers, defenders-2, arem, drem) + \
                self.probs[3][2][1]*self.outcomeprob(attackers-1, defenders-1, arem, drem) + \
                self.probs[3][2][2]*self.outcomeprob(attackers-2, defenders, arem, drem)
        elif attackers >= 3 and defenders == 1:
            val = self.probs[3][1][0]*self.outcomeprob(attackers, defenders-1, arem, drem) + \
                self.probs[3][1][2]*self.outcomeprob(attackers-1, defenders, arem, drem)
        elif attackers == 2 and defenders >= 2:
            val = self.probs[2][2][0]*self.outcomeprob(attackers, defenders-2, arem, drem) + \
                self.probs[2][2][1]*self.outcomeprob(attackers-1, defenders-1, arem, drem) + \
                self.probs[2][2][2]*self.outcomeprob(attackers-2, defenders, arem, drem)
        elif attackers == 2 and defenders == 1:
            val = self.probs[2][1][0]*self.outcomeprob(attackers, defenders-1, arem, drem) + \
                self.probs[2][1][2]*self.outcomeprob(attackers-1, defenders, arem, drem)
        elif attackers == 1 and defenders >= 2:
            val = self.probs[1][2][0]*self.outcomeprob(attackers, defenders-1, arem, drem)
        elif attackers == 1 and defenders == 1:
            val = self.probs[1][1][0]*self.outcomeprob(attackers, defenders-1, arem, drem)

        self.omem[h] = val
        return val

    # Finds probability of successful tour given:
    # a starting army of size attackers,
    # an array of armies darmies representing the defending armies in the order they will be attacked,
    # which defending army is being attacked (default 0 for the start),
    # the number of troops we want to leave behind at each country (default 1 for each country),
    # number of guys we want to leave behind in each country
    def tourprob(self,attackers, darmies, tindex=0, fortify=([1]*100)):
        if tindex == len(darmies): return 1.0
        if tindex == 0: # reset memoize table
            global tmem
            tmem = {}

        h = (attackers, tindex)
        if h in tmem: return tmem[h]

        army = attackers-fortify[tindex]
        minremaining = sum(fortify[i] for i in range(tindex+1,len(darmies)+1))

        val = 0.0
        for i in range(minremaining, army+1):
            val += self.outcomeprob(army, darmies[tindex], i)*self.tourprob(i, darmies, tindex+1, fortify)

        tmem[h] = val
        return val   


if __name__ == "__main__":
    main()
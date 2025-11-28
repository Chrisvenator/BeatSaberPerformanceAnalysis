from dataset.get_all_map_infos_for_user import get_maps_for_player_id
from dataset.get_all_scores_for_user import get_scores_for


def __main__():
    player_id = 76561198274713084

    get_scores_for(player_id)
    get_maps_for_player_id(player_id)



if __name__ == "__main__":
    __main__()

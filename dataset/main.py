import os

from dataset.create_dataset import create_dataset
from dataset.get_all_map_infos_for_user import get_maps_for_player_id
from dataset.get_all_scores_for_user import get_scores_for_player_id


def __main__():
    get_scores_for_player_id()
    get_maps_for_player_id()
    create_dataset()


if __name__ == "__main__":
    __main__()



def split_restaurant_nodes(places, windows_map):
    new_places, new_wins = [], []


    for place in places:
        pid = place["id"]
        wins = windows_map.get(pid)

        if wins is None:
            raise ValueError(f"장소 {pid}의 유효 시간 윈도우가 없습니다.")

        if place.get("category") == "restaurant" and len(wins) > 1:
            for o, c, meal in wins:
                node = {**place}
                label = meal or "default"
                node.update({
                    "name": f"{place['name']} ({label})",
                    "id": f"{pid}_{label}",
                    "org_id": pid
                })
                new_places.append(node)
                new_wins.append((o, c, meal))
        else:
            new_places.append(place)
            new_wins.append(wins[0] if wins else (None, None, None))

    return new_places, new_wins

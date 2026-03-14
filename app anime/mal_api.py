if __name__ == "__main__":
    try:
        # Tu código principal aquí (si aplica)
        pass
    except Exception as e:
        import traceback
        print(f"Error inesperado en mal_api.py:\n{e}\n\n{traceback.format_exc()}")
import requests
import logging

def get_mal_info(anime_title: str, client_id: str) -> dict:
    """
    Consulta la API pública de MyAnimeList para obtener info de un anime por título.
    Requiere un client_id de una app registrada en https://myanimelist.net/apiconfig
    Devuelve dict con rating, temporadas, episodios y géneros si se encuentra.
    """
    url = "https://api.myanimelist.net/v2/anime"
    params = {
        "q": anime_title,
        "limit": 1,
        "fields": "title,mean,num_episodes,start_season,genres"
    }
    headers = {"X-MAL-CLIENT-ID": client_id}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if "data" in data and data["data"]:
            entry = data["data"][0]["node"]
            return {
                "title": entry.get("title"),
                "rating": entry.get("mean"),
                "episodes": entry.get("num_episodes"),
                "season": entry.get("start_season", {}).get("season"),
                "year": entry.get("start_season", {}).get("year"),
                "genres": ", ".join([g["name"] for g in entry.get("genres", [])])
            }
        return {}
    except Exception as e:
        logging.warning(f"No se pudo obtener info de MAL para '{anime_title}': {e}")
        return {}

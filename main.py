from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests


app = FastAPI(title="Mini Pokédex")
templates = Jinja2Templates(directory="templates")

POKEAPI_URL = "https://pokeapi.co/api/v2"


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/pokemon/{name}")
def get_pokemon(name: str):
    name = name.lower().strip()
    url  = f"{POKEAPI_URL}/pokemon/{name}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Pokémon '{name}' não encontrado.")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Erro ao consultar a PokéAPI.")
        data = response.json()
        return {
            "id":     data["id"],
            "name":   data["name"],
            "height": data["height"] / 10,
            "weight": data["weight"] / 10,
            "image":  data["sprites"]["front_default"],
            "types":  [t["type"]["name"] for t in data["types"]],
            "stats":  {s["stat"]["name"]: s["base_stat"] for s in data["stats"]},
        }
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="A PokéAPI demorou muito. Tente novamente.")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Sem conexão com a PokéAPI.")


@app.get("/tipo/{tipo}")
def filtrar_por_tipo(tipo: str):
    url = f"{POKEAPI_URL}/type/{tipo.lower()}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Tipo '{tipo}' não encontrado.")
        data     = response.json()
        pokemons = [
            {
                "name": p["pokemon"]["name"],
                "url":  p["pokemon"]["url"]
            }
            for p in data["pokemon"]
        ]
        return {"tipo": tipo, "total": len(pokemons), "pokemons": pokemons}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/geracao/{numero}")
def filtrar_por_geracao(numero: int):
    url = f"{POKEAPI_URL}/generation/{numero}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Geração {numero} não encontrada.")
        data     = response.json()
        pokemons = [{"name": p["name"]} for p in data["pokemon_species"]]
        return {"geracao": numero, "total": len(pokemons), "pokemons": pokemons}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=str(e))
    
@app.get("/filtro")
def filtrar(tipo: str = None, geracao: int = None):
    try:
        lista_tipo = {}
        lista_gen  = set()

        # Busca por tipo
        if tipo:
            res = requests.get(f"{POKEAPI_URL}/type/{tipo.lower()}", timeout=10)
            if res.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Tipo '{tipo}' não encontrado.")
            data = res.json()
            for p in data["pokemon"]:
                nome = p["pokemon"]["name"]
                url  = p["pokemon"]["url"]
                # Extrai o ID direto da URL ex: .../pokemon/6/
                id_pokemon = int(url.rstrip("/").split("/")[-1])
                lista_tipo[nome] = id_pokemon

        # Busca por geração
        if geracao:
            res = requests.get(f"{POKEAPI_URL}/generation/{geracao}", timeout=10)
            if res.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Geração {geracao} não encontrada.")
            data = res.json()
            for p in data["pokemon_species"]:
                url = p["url"]
                id_pokemon = int(url.rstrip("/").split("/")[-1])
                lista_gen.add(id_pokemon)

        # Cruza os filtros
        if tipo and geracao:
            # Mantém só os que estão nos dois filtros
            pokemons = [
                {"name": nome, "id": id_p}
                for nome, id_p in lista_tipo.items()
                if id_p in lista_gen
            ]
        elif tipo:
            pokemons = [{"name": nome, "id": id_p} for nome, id_p in lista_tipo.items()]
        else:
            # Só geração — monta lista com os nomes da geração
            pokemons = [
                {"name": p["name"], "id": int(p["url"].rstrip("/").split("/")[-1])}
                for p in data["pokemon_species"]
            ]

        # Ordena pelo número da Pokédex
        pokemons = sorted(pokemons, key=lambda x: x["id"])

        return {"total": len(pokemons), "pokemons": pokemons}

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=str(e))
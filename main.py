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
        lista_tipo = set()
        lista_gen  = set()

        # Busca por tipo
        if tipo:
            res  = requests.get(f"{POKEAPI_URL}/type/{tipo.lower()}", timeout=10)
            if res.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Tipo '{tipo}' não encontrado.")
            data = res.json()
            for p in data["pokemon"]:
                lista_tipo.add(p["pokemon"]["name"])

        # Busca por geração
        if geracao:
            res  = requests.get(f"{POKEAPI_URL}/generation/{geracao}", timeout=10)
            if res.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Geração {geracao} não encontrada.")
            data = res.json()
            for p in data["pokemon_species"]:
                lista_gen.add(p["name"])

        # Cruza os dois filtros se ambos foram selecionados
        if tipo and geracao:
            nomes = lista_tipo & lista_gen   # interseção — só os que estão nos dois
        elif tipo:
            nomes = lista_tipo
        else:
            nomes = lista_gen

        pokemons = sorted([{"name": n} for n in nomes], key=lambda x: x["name"])

        return {"total": len(pokemons), "pokemons": pokemons}

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=str(e))
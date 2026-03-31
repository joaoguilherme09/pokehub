"""
Mini Pokédex - Backend com FastAPI
===================================
Este arquivo é o coração do nosso servidor.
Ele recebe as requisições do navegador e busca dados na PokéAPI.
"""

# ── Importações ──────────────────────────────────────────────────────────────
from fastapi import FastAPI, HTTPException  # FastAPI = nosso framework web
from fastapi.responses import HTMLResponse  # Para devolver páginas HTML
from fastapi.templating import Jinja2Templates  # Motor de templates HTML
from fastapi import Request                 # Representa a requisição do usuário
import requests                             # Para chamar APIs externas (PokéAPI)



# ── Configuração da aplicação ────────────────────────────────────────────────
app = FastAPI(title="Mini Pokédex")



# Dizemos ao FastAPI onde estão os arquivos HTML (pasta "templates")
templates = Jinja2Templates(directory="templates")

# URL base da PokéAPI — todas as chamadas partem daqui
POKEAPI_URL = "https://pokeapi.co/api/v2"


# ── Rota 1: Página principal ─────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """
    Quando o usuário acessa http://localhost:8000/
    o FastAPI devolve o arquivo index.html renderizado.
    """
    return templates.TemplateResponse("index.html", {"request": request})


# ── Rota 2: Buscar dados de um Pokémon ──────────────────────────────────────
@app.get("/pokemon/{name}")
def get_pokemon(name: str):
    """
    Recebe o nome OU número do Pokémon na URL.
    Ex: /pokemon/pikachu ou /pokemon/25
    Consulta a PokéAPI e devolve um JSON com os dados principais.
    """
    # Normalizamos para minúsculas (a API exige isso para nomes)
    name = name.lower().strip()

    # Montamos a URL completa para chamar a PokéAPI
    url = f"{POKEAPI_URL}/pokemon/{name}"

    try:
        # Fazemos a requisição GET para a PokéAPI com timeout de 10 segundos
        response = requests.get(url, timeout=10)

        # Se o Pokémon não existir, a API retorna status 404
        if response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Pokémon '{name}' não encontrado. Verifique o nome ou número."
            )

        # Se qualquer outro erro acontecer, também informamos o usuário
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Erro ao consultar a PokéAPI. Tente novamente mais tarde."
            )

        # Convertemos a resposta para dicionário Python
        data = response.json()

        # ── Extraindo os dados que nos interessam ──────────────────────────

        # ID numérico do Pokémon na Pokédex (ex: 25 para Pikachu)
        pokemon_id = data["id"]

        # Nome oficial do Pokémon
        pokemon_name = data["name"]

        # Altura em decímetros → convertemos para metros (divide por 10)
        height_meters = data["height"] / 10

        # Peso em hectogramas → convertemos para quilogramas (divide por 10)
        weight_kg = data["weight"] / 10

        # URL da imagem (sprite frontal padrão)
        image_url = data["sprites"]["front_default"]

        # Lista de tipos, ex: ["fire", "flying"]
        types = [t["type"]["name"] for t in data["types"]]

        # Estatísticas base: hp, attack, defense, etc.
        stats = {
            stat["stat"]["name"]: stat["base_stat"]
            for stat in data["stats"]
        }

        # Devolvemos um JSON completo para o frontend
        return {
            "id": pokemon_id,        # ← NOVO: número da Pokédex
            "name": pokemon_name,
            "height": height_meters,
            "weight": weight_kg,
            "image": image_url,
            "types": types,
            "stats": stats,
        }

    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="A PokéAPI demorou muito para responder. Tente novamente."
        )

    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Não foi possível conectar à PokéAPI. Verifique sua conexão."
        )



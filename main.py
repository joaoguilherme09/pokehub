# ── Importações
from fastapi import FastAPI, HTTPException, Request
# FastAPI é oframework que cria o servidor web e as rotas
# HTTPException é usado para retornar erros com mensagens personalizadas
# O Request representa a requisição feita pelo navegador

from fastapi.responses import HTMLResponse
# O HTMLResponse diz ao FastAPI que a resposta será uma página HTML

from fastapi.templating import Jinja2Templates
# O Jinja2Templates renderiza arquivos HTML (como o index.html)

import requests
# chama a biblioteca para fazer chamadas HTTP para a PokéAPI


# ── Configuração da app
app = FastAPI(title="Mini Pokédex")
# Cria o FastAPI, e o 'title' aparece na documentação automatica em /docs

templates = Jinja2Templates(directory="templates")
# Mostra ao FastAPI que os arquivos HTML estão na pasta "templates"

POKEAPI_URL = "https://pokeapi.co/api/v2"
# É a URL base da PokéAPI. 
# É onde sao feitos os chamados a API


# ── Rota 1: pagina principal
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    # Quando o usuário acessa http://localhost:8000/, o FastAPI devolve o arquivo index.html renderizado
    # O `request` é obrigatório para o Jinja2 funcionar
    return templates.TemplateResponse("index.html", {"request": request})




def buscar_relacoes_tipo(tipos: list):
    dano_recebido = {}
    
    for tipo in tipos:
        res = requests.get(f"{POKEAPI_URL}/type/{tipo}", timeout=10)
        if res.status_code != 200:
            continue
        data     = res.json()
        relacoes = data["damage_relations"]


        # Dano recebido
        for t in relacoes["double_damage_from"]:
            nome = t["name"]
            dano_recebido[nome] = dano_recebido.get(nome, 1) * 2

        for t in relacoes["half_damage_from"]:
            nome = t["name"]
            dano_recebido[nome] = dano_recebido.get(nome, 1) * 0.5

        for t in relacoes["no_damage_from"]:
            nome = t["name"]
            dano_recebido[nome] = 0



    return {
        "fraquezas":    [t for t, v in dano_recebido.items() if v > 1],
        "resistencias": [t for t, v in dano_recebido.items() if 0 < v < 1],
        "imunidades":   [t for t, v in dano_recebido.items() if v == 0],
    }


# ── Rota 2: Buscar um Pokémon por nome ou número
@app.get("/pokemon/{name}")
def get_pokemon(name: str):
    # o parametro 'name' recebe o nome ou número na URL atraves da funcao get_pokemon(name: str). ex: /pokemon/pikachu ou /pokemon/25

    name = name.lower().strip()
    # lower converte para minúsculas, strip remove os espaços, assim garante que independente do CaseSensitive vai ter busca
    # obs: A PokéAPI só aceita nomes em minúsculas

    url = f"{POKEAPI_URL}/pokemon/{name}"
    # Monta a URL, ex: https://pokeapi.co/api/v2/pokemon/pikachu

    try:
        response = requests.get(url, timeout=10)
        # Faz a requisição GET para a PokéAPI
        # timeout=10 significa que se demorar mais de 10 segundos, ela automaticamente cancela a requisição

        if response.status_code == 404:
            # Status 404 = não encontrado
            # Retorna uma mensagem de erro para o usuário
            raise HTTPException(status_code=404, detail=f"Pokémon '{name}' não encontrado.")

        if response.status_code != 200:
            # Qualquer outro erro (ex: 500 = erro interno da PokéAPI)
            raise HTTPException(status_code=response.status_code, detail="Erro ao consultar a PokéAPI.")

        data = response.json()
        # Converte a resposta da PokéAPI para dicionário Python

        # Extrai os tipos do Pokémon
        tipos = [t["type"]["name"] for t in data["types"]]

        # Busca fraquezas, resistências e imunidades com base nos tipos
        relacoes = buscar_relacoes_tipo(tipos)

        # Retorna apenas os dados que nos interessam, organizados em JSON
        return {
            "id":           data["id"],                                             # ID = número na Pokédex
            "name":         data["name"],                                           # nome do pokemon
            "height":       data["height"] / 10,                                    # altura do pokemon
            "weight":       data["weight"] / 10,                                    # peso do pokemon
            "image":        data["sprites"]["front_default"],                       # URL da imagem do Pokémon
            "types":        tipos,                                                  # lista dos tipos, ex: ["electric"]
            "stats":        {s["stat"]["name"]: s["base_stat"] for s in data["stats"]},  # dicionário de status base
            "fraquezas":    relacoes["fraquezas"],                                  # tipos que causam dano duplo
            "resistencias": relacoes["resistencias"],                               # tipos que causam dano reduzido
            "imunidades":   relacoes["imunidades"],                                 # tipos que não causam dano no pokemon
        }

    except requests.exceptions.Timeout:
        # se a PokéAPI não responder em 10 segundos
        raise HTTPException(status_code=504, detail="A PokéAPI demorou muito. Tente novamente.")

    except requests.exceptions.ConnectionError:
        # Sem internet ou a PokéAPI está fora do ar
        raise HTTPException(status_code=503, detail="Sem conexão com a PokéAPI.")
    
    
# ── Rota 3: Filtrar por tipo 
@app.get("/tipo/{tipo}")
def filtrar_por_tipo(tipo: str):
    # Recebe o tipo na URL, ex: /tipo/fire
    # Retorna todos os Pokémon daquele tipo

    url = f"{POKEAPI_URL}/type/{tipo.lower()}"
    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Tipo '{tipo}' não encontrado.")

        data = response.json()

        # Extrai nome e URL de cada Pokémon do tipo
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


# ── Rota 4: Filtrar pela geração 
@app.get("/geracao/{numero}")
def filtrar_por_geracao(numero: int):
    # Recebe o número da geração na URL, ex: /geracao/1
    # Retorna todos os Pokémon daquela geração

    url = f"{POKEAPI_URL}/generation/{numero}"
    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Geração {numero} não encontrada.")

        data = response.json()

        # Extrai apenas o nome de cada Pokémon da geração
        pokemons = [{"name": p["name"]} for p in data["pokemon_species"]]
        return {"geracao": numero, "total": len(pokemons), "pokemons": pokemons}

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=str(e))


# ── Rota 5: Filtro avançado — pelos tipos e gerações 
@app.get("/filtro")
def filtrar(tipo: str = None, geracao: int = None):
    # É usada para filtrar tipos e gerações ao msm tempo
    # É a rota principal dos filtros da interface
    
    
    
    # Aceita parâmetros opcionais na URL, exemplos:
    #   /filtro?tipo=fire
    #   /filtro?geracao=1
    #   /filtro?tipo=fire,flying          ← dois tipos ao mesmo tempo
    #   /filtro?tipo=fire,flying&geracao=1 ← dois tipos + geração

    try:
        lista_gen  = set()   # conjunto de IDs dos Pokémon da geração escolhida
        lista_tipo = {}      # dicionário {id: nome} dos Pokémon do(s) tipo(s) escolhido(s)

        # ── Filtro por tipo
        if tipo:
            tipos = [t.strip().lower() for t in tipo.split(",")]
            # Separa os tipos por vírgula, ex: "fire,flying" → ["fire", "flying"]

            # Busca todos os Pokémon do PRIMEIRO tipo
            res = requests.get(f"{POKEAPI_URL}/type/{tipos[0]}", timeout=10)
            if res.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Tipo '{tipos[0]}' não encontrado.")
            data = res.json()

            for p in data["pokemon"]:
                url        = p["pokemon"]["url"]
                id_pokemon = int(url.rstrip("/").split("/")[-1])
                # Extrai o ID do Pokémon da URL, ex: ".../pokemon/6/" → 6
                nome       = p["pokemon"]["name"]

                if id_pokemon < 10000:
                    # Ignora formas alternativas (Mega, Gigantamax etc.),  que têm IDs acima de 10000
                    lista_tipo[id_pokemon] = nome

            # Se o usuário selecionou DOIS tipos, filtra quem tem os dois ao mesmo tempo
            if len(tipos) == 2:
                ids_com_dois_tipos = {}

                for id_p, nome in lista_tipo.items():
                    # Para cada Pokémon do primeiro tipo, consulta seus dados individuais
                    res2 = requests.get(f"{POKEAPI_URL}/pokemon/{id_p}", timeout=10)

                    if res2.status_code == 200:
                        data2      = res2.json()
                        tipos_poke = [t["type"]["name"] for t in data2["types"]]
                        # Pega a lista de tipos desse Pokémon, ex: ["fire", "flying"]

                        if tipos[1] in tipos_poke:
                            # Se o segundo tipo também está na lista de tipos do Pokémon
                            # significa que ele tem OS DOIS tipos → adiciona ao resultado
                            ids_com_dois_tipos[id_p] = nome

                lista_tipo = ids_com_dois_tipos
                # Substitui a lista original pela lista filtrada com os dois tipos

        # ── Filtro por geração
        if geracao:
            res = requests.get(f"{POKEAPI_URL}/generation/{geracao}", timeout=10)
            if res.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Geração {geracao} não encontrada.")
            data = res.json()

            for p in data["pokemon_species"]:
                id_pokemon = int(p["url"].rstrip("/").split("/")[-1])
                lista_gen.add(id_pokemon)
                # Adiciona o ID de cada Pokémon da geração no conjunto

        # ── Monta a lista final 
        if tipo and geracao:
            # Onde o suário escolheu tipo(s) e a geração
            # Mantém apenas os Pokémon que aparecem nos dois filtros ao mesmo tempo
            pokemons = [
                {"name": nome, "id": id_p}
                for id_p, nome in lista_tipo.items()
                if id_p in lista_gen  # o ID precisa estar na lista da geração também
            ]
        elif tipo:
            # Usuário escolheu apenas tipo(s)
            pokemons = [{"name": nome, "id": id_p} for id_p, nome in lista_tipo.items()]
        else:
            # Usuário escolheu apenas geração
            pokemons = [
                {"name": p["name"], "id": int(p["url"].rstrip("/").split("/")[-1])}
                for p in data["pokemon_species"]
            ]

        # Ordena a lista pelo número da Pokédex (do menor para o maior)
        pokemons = sorted(pokemons, key=lambda x: x["id"])

        return {"total": len(pokemons), "pokemons": pokemons}

    except requests.exceptions.RequestException as e:
        # Qualquer erro de conexão cai aqui
        raise HTTPException(status_code=503, detail=str(e))
    
    
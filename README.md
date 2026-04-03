# 🔴 Pokédex

Uma mini Pokédex web feita com FastAPI e Python, consumindo a [PokéAPI](https://pokeapi.co).



## ✨ Funcionalidades

- Busca por nome ou número da Pokédex
- Exibe imagem, tipos, altura, peso e status base
- Filtro por tipo — selecione até 2 tipos ao mesmo tempo
- Filtro por geração — Gen I até Gen IX
- Combinação de filtros — ex: tipo Fogo + Voador da Geração 1
- Lista ordenada pelo número da Pokédex
- Clique em qualquer Pokémon da lista para ver seus detalhes

---

## 🛠️ Tecnologias

- Python + FastAPI
- Jinja2 (templates HTML)
- HTML, CSS e JavaScript puro
- PokéAPI (API pública e gratuita)
- Render (hospedagem)


## 🚀 Como rodar


**1. Acesse o link abaixo:**
```
https://pokedex-dkbp.onrender.com/
```

**ou**

**1. Clone o repositório**
```bash
git clone https://github.com/joaoguilherme09/Pokedex.git
cd Pokedex
```

**2. Crie e ative o ambiente virtual**
```bash
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1
```

**3. Instale as dependências**
```bash
pip install -r requirements.txt
```

**4. Inicie o servidor**
```bash
uvicorn main:app --reload
```

**5. Acesse no navegador**
```
http://localhost:8000
```






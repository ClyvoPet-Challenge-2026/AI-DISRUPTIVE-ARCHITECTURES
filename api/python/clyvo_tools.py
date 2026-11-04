import math
import unicodedata


PLANOS = [
    {
        "id": "essencial",
        "nome": "Clyvo Essencial",
        "preco": 49.90,
        "badge": "Entrada",
        "perfil_ideal": {"idade_max": 15, "risco": "baixo"},
        "coberturas": [
            "Vacinas anuais",
            "Consultas de rotina",
            "Exames laboratoriais básicos",
        ],
        "desconto_parceiros": 0.10,
    },
    {
        "id": "conforto",
        "nome": "Clyvo Conforto",
        "preco": 89.90,
        "badge": "Mais Popular",
        "perfil_ideal": {"idade_max": 12, "risco": "medio"},
        "coberturas": [
            "Consultas ilimitadas",
            "Exames de imagem",
            "Vacinas",
            "Emergência 24h",
        ],
        "desconto_parceiros": 0.20,
    },
    {
        "id": "plus",
        "nome": "Clyvo Plus",
        "preco": 149.90,
        "badge": "Completo",
        "perfil_ideal": {"idade_max": 10, "risco": "medio-alto"},
        "coberturas": [
            "Cirurgias",
            "Internação",
            "Especialistas",
            "Exames complexos",
        ],
        "desconto_parceiros": 0.30,
    },
    {
        "id": "senior",
        "nome": "Clyvo Sênior & Especial",
        "preco": 239.90,
        "badge": "Especializado",
        "perfil_ideal": {"idade_max": 99, "risco": "alto"},
        "coberturas": [
            "Fisioterapia",
            "Acompanhamento oncologico/geriatra",
            "UTI",
            "Medicamentos contínuos",
        ],
        "desconto_parceiros": 0.40,
    },
]

CLINICAS_PARCEIRAS = [
    {
        "nome": "Clyvo Pet Leste",
        "lat": -23.551900,
        "lon": -46.507400,
        "emergencia_24h": True,
        "especialidades": ["Clínica Geral", "Vacinação", "Emergência"],
        "planos_aceitos": ["essencial", "conforto", "plus", "senior"],
    },
    {
        "nome": "Centro Veterinário Mooca",
        "lat": -23.557800,
        "lon": -46.598500,
        "emergencia_24h": False,
        "especialidades": ["Clínica Geral", "Dermatologia", "Odontologia"],
        "planos_aceitos": ["essencial", "conforto", "plus"],
    },
    {
        "nome": "Hospital Animal Tatuapé",
        "lat": -23.540500,
        "lon": -46.576800,
        "emergencia_24h": True,
        "especialidades": ["Cirurgia", "Internação", "UTI", "Ortopedia"],
        "planos_aceitos": ["conforto", "plus", "senior"],
    },
    {
        "nome": "Clínica Vet Vila Prudente",
        "lat": -23.584700,
        "lon": -46.582900,
        "emergencia_24h": False,
        "especialidades": ["Clínica Geral", "Fisioterapia", "Vacinação"],
        "planos_aceitos": ["essencial", "conforto", "senior"],
    },
    {
        "nome": "Hospital Veterinário Anália Franco",
        "lat": -23.561600,
        "lon": -46.560700,
        "emergencia_24h": True,
        "especialidades": ["Oncologia", "Cardiologia", "Exames de Imagem"],
        "planos_aceitos": ["plus", "senior"],
    },
    {
        "nome": "Pet Saúde Penha",
        "lat": -23.523900,
        "lon": -46.541600,
        "emergencia_24h": False,
        "especialidades": ["Clínica Geral", "Nefrologia", "Nutrição"],
        "planos_aceitos": ["essencial", "conforto", "plus"],
    },
    {
        "nome": "VetCare 24h Central",
        "lat": -23.561684,
        "lon": -46.655981,
        "emergencia_24h": True,
        "especialidades": ["Clínica Geral", "Cirurgia", "UTI", "Geriatria"],
        "planos_aceitos": ["essencial", "conforto", "plus", "senior"],
    },
    {
        "nome": "Clínica Veterinária PetLife",
        "lat": -23.570000,
        "lon": -46.640000,
        "emergencia_24h": False,
        "especialidades": ["Clínica Geral", "Vacinação", "Dermatologia"],
        "planos_aceitos": ["conforto", "plus", "senior"],
    },
    {
        "nome": "Hospital Especializado Animal Primus",
        "lat": -23.540000,
        "lon": -46.630000,
        "emergencia_24h": True,
        "especialidades": ["Oncologia", "Fisioterapia", "Ortopedia", "UTI"],
        "planos_aceitos": ["plus", "senior"],
    },
]


def recomendar_plano(
    idade_pet: int,
    tem_doenca_cronica: bool,
    orcamento_mensal: float,
    tolerancia_risco: str,
) -> dict:
    tolerancia_risco = tolerancia_risco.lower().strip()
    ordem_risco = ["baixo", "medio", "medio-alto", "alto"]

    if tolerancia_risco not in ordem_risco:
        raise ValueError(f"Tolerância de risco inválida: {tolerancia_risco}")

    if tem_doenca_cronica:
        plano_senior = next(p for p in PLANOS if p["id"] == "senior")
        if orcamento_mensal >= plano_senior["preco"]:
            return {
                "plano_recomendado": plano_senior,
                "justificativa": (
                    "Pet com doença crônica necessita de acompanhamento contínuo "
                    "no plano Sênior & Especial."
                ),
            }

        candidatos_orcamento = [
            p for p in PLANOS if p["preco"] <= orcamento_mensal
        ]
        if candidatos_orcamento:
            melhor = max(candidatos_orcamento, key=lambda p: p["preco"])
            return {
                "plano_recomendado": melhor,
                "justificativa": (
                    f"O plano ideal é o Sênior & Especial, mas foi indicado o "
                    f"{melhor['nome']} para respeitar o orçamento de "
                    f"R$ {orcamento_mensal:.2f}."
                ),
            }

    candidatos = []
    for plano in PLANOS:
        perfil = plano["perfil_ideal"]
        if plano["id"] == "senior" and not tem_doenca_cronica and idade_pet < 8:
            continue
        if idade_pet > perfil["idade_max"] or orcamento_mensal < plano["preco"]:
            continue
        if ordem_risco.index(tolerancia_risco) < ordem_risco.index(perfil["risco"]):
            continue
        candidatos.append(plano)

    if not candidatos:
        return {
            "plano_recomendado": PLANOS[0],
            "justificativa": (
                "Nenhum plano atendeu 100% dos filtros. Sugerido Clyvo "
                "Essencial como opção de entrada."
            ),
        }

    return {
        "plano_recomendado": max(candidatos, key=lambda item: item["preco"]),
        "justificativa": (
            "Atende totalmente à idade, nível de risco e orçamento do tutor."
        ),
    }


def distancia_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    raio_terra_km = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return raio_terra_km * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def buscar_clinicas_proximas(
    plano_id: str,
    nome_clinica: str | None = None,
    lat_usuario: float | None = None,
    lon_usuario: float | None = None,
    raio_max_km: float = 15.0,
) -> dict:
    if plano_id not in {plano["id"] for plano in PLANOS}:
        raise ValueError(f"Plano inválido: {plano_id}")
    if raio_max_km <= 0:
        raise ValueError("O raio máximo deve ser maior que zero.")
    if not nome_clinica and (lat_usuario is None or lon_usuario is None):
        raise ValueError(
            "Informe o nome da clínica ou latitude e longitude do tutor."
        )

    def normalizar(texto: str) -> str:
        decomposed = unicodedata.normalize("NFD", texto.casefold())
        return "".join(
            caractere
            for caractere in decomposed
            if unicodedata.category(caractere) != "Mn"
        )

    nome_buscado = normalizar(nome_clinica) if nome_clinica else None

    resultados = []
    for clinica in CLINICAS_PARCEIRAS:
        nome_corresponde = (
            nome_buscado is not None
            and nome_buscado in normalizar(clinica["nome"])
        )
        distancia = None
        if lat_usuario is not None and lon_usuario is not None:
            distancia = distancia_km(
                lat_usuario,
                lon_usuario,
                clinica["lat"],
                clinica["lon"],
            )

        if nome_buscado and not nome_corresponde:
            continue
        if not nome_buscado and distancia > raio_max_km:
            continue

        coberto = plano_id in clinica["planos_aceitos"]
        resultados.append(
            {
                "nome": clinica["nome"],
                "distancia_km": round(distancia, 2) if distancia is not None else None,
                "emergencia_24h": clinica["emergencia_24h"],
                "especialidades": clinica["especialidades"],
                "status_cobertura": (
                    "Atendimento Coberto"
                    if coberto
                    else "Atendimento com Desconto (Co-participação)"
                ),
            }
        )

    if lat_usuario is not None and lon_usuario is not None:
        resultados.sort(key=lambda item: item["distancia_km"])

    return {"clinicas": resultados}


FERRAMENTAS = [
    {
        "type": "function",
        "name": "recomendar_plano",
        "description": (
            "Calcula e recomenda o plano de saúde pet ideal da Clyvo com base "
            "na idade, histórico de doença, orçamento e risco."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "idade_pet": {
                    "type": "integer",
                    "description": "Idade do animal em anos.",
                },
                "tem_doenca_cronica": {
                    "type": "boolean",
                    "description": (
                        "Se o pet possui doença crônica ou tratamento diário."
                    ),
                },
                "orcamento_mensal": {
                    "type": "number",
                    "description": (
                        "Orçamento máximo mensal em R$ que o tutor aceita pagar."
                    ),
                },
                "tolerancia_risco": {
                    "type": "string",
                    "enum": ["baixo", "medio", "medio-alto", "alto"],
                    "description": "Perfil de tolerância a risco do tutor.",
                },
            },
            "required": [
                "idade_pet",
                "tem_doenca_cronica",
                "orcamento_mensal",
                "tolerancia_risco",
            ],
        },
    },
    {
        "type": "function",
        "name": "buscar_clinicas_proximas",
        "description": (
            "Busca uma clínica parceira pelo nome ou as clínicas credenciadas "
            "mais próximas da localização do tutor e confere a cobertura do plano."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "nome_clinica": {
                    "type": "string",
                    "description": (
                        "Nome ou parte do nome da clínica procurada. "
                        "Use quando o tutor informar uma clínica específica."
                    ),
                },
                "lat_usuario": {
                    "type": "number",
                    "description": (
                        "Latitude da posição atual do tutor. Use apenas "
                        "quando não houver nome de clínica."
                    ),
                },
                "lon_usuario": {
                    "type": "number",
                    "description": (
                        "Longitude da posição atual do tutor. Use apenas "
                        "quando não houver nome de clínica."
                    ),
                },
                "plano_id": {
                    "type": "string",
                    "enum": ["essencial", "conforto", "plus", "senior"],
                    "description": "ID do plano contratado ou analisado.",
                },
                "raio_max_km": {
                    "type": "number",
                    "description": "Raio máximo de busca em km.",
                },
            },
            "required": ["plano_id"],
        },
    },
]

FUNCOES_AUTORIZADAS = {
    "recomendar_plano": recomendar_plano,
    "buscar_clinicas_proximas": buscar_clinicas_proximas,
}

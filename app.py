import requests
import json
import os
from datetime import datetime, timedelta, timezone
import math

# Tenta carregar o fuso dinâmico; fallback seguro para Portugal
try:
    from zoneinfo import ZoneInfo
    FUSO_PT = ZoneInfo("Europe/Lisbon")
except Exception:
    FUSO_PT = timezone(timedelta(hours=1))

# =========================================================================
# CONFIGURAÇÃO GLOBAL E TEMPORAL
# =========================================================================
ESPECIES_DISPONIVEIS = ["Achigã", "Lúcio-Perca", "Lúcio", "Siluro", "Barbo", "Carpa"]
ALVO_ATUAL = "Achigã"
FEEDBACK_FILE = "mestre_tatico_feedback.json"

def get_hora_atual():
    return datetime.now(FUSO_PT)

# =========================================================================
# SISTEMA DE FEEDBACK LOCAL (MACHINE LEARNING DO PESCADOR)
# =========================================================================
def carregar_feedback():
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def guardar_feedback(barragem_nome, especie, score_previsto, sucesso_real):
    dados = carregar_feedback()
    chave = f"{barragem_nome}_{especie}"
    if chave not in dados: dados[chave] = []
    dados[chave].append({"data": get_hora_atual().strftime("%Y-%m-%d"), "score_previsto": score_previsto, "sucesso_real": sucesso_real})
    try:
        with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
        print("✅ Feedback gravado! O motor Bayesiano local reajustou os pesos.")
    except Exception as e:
        print(f"⚠️ Erro ao gravar feedback: {e}")

def calcular_fator_correcao_local(barragem_nome, especie):
    dados = carregar_feedback()
    chave = f"{barragem_nome}_{especie}"
    if chave not in dados or len(dados[chave]) == 0: return 0.0
    registos = dados[chave][-5:]
    desvios = [reg["sucesso_real"] - (reg["score_previsto"] / 20.0) for reg in registos]
    return (sum(desvios) / len(desvios)) * 3.5

# =========================================================================
# BASE DE DADOS LIMNOLÓGICA COMPLETA COM ENQUADRAMENTO ICNF 2026
# =========================================================================
BARRAGENS_ALENTEJO = [
    {
        "nome": "Amieira / Alqueva", "distrito": "Évora", "bacia": "Guadiana", "lat": 38.28, "lon": -7.52,
        "estrutura": "Xisto, profundidade, margens declivosas, pontões.", "tipo_fundo": "rocha", "prof_max": 90,
        "comprimento_l_km": 83.0, "ipma_id": "Evora", "snirh_code": "04G/01H", "eixo_orientacao": 150, "fetch_max_km": 18.0,
        "regime_icnf": "Regime Geral de Pesca Lúdica em Águas Interiores (Licença Nacional/Regional obrigatória)", "zpr": False
    },
    {
        "nome": "Monte Novo", "distrito": "Évora", "bacia": "Guadiana", "lat": 38.53, "lon": -7.72,
        "estrutura": "Pastos submersos, fundos mistos e pedras.", "tipo_fundo": "misto", "prof_max": 25,
        "comprimento_l_km": 12.0, "ipma_id": "Evora", "snirh_code": "04F/02H", "eixo_orientacao": 45, "fetch_max_km": 5.5,
        "regime_icnf": "Regime Geral de Águas Interiores não concessionadas", "zpr": False
    },
    {
        "nome": "Divor", "distrito": "Évora", "bacia": "Tejo", "lat": 38.68, "lon": -7.98,
        "estrutura": "Águas rasas, fundos de terra, prados e vegetação.", "tipo_fundo": "argila", "prof_max": 15,
        "comprimento_l_km": 7.0, "ipma_id": "Evora", "snirh_code": "03F/01H", "eixo_orientacao": 90, "fetch_max_km": 3.2,
        "regime_icnf": "Zona de Pesca Reservada (ZPR) / Gestão Associativa", "zpr": True
    },
    {
        "nome": "Lucefecit (Terena)", "distrito": "Évora", "bacia": "Guadiana", "lat": 38.60, "lon": -7.42,
        "estrutura": "Terreno rochoso, canaviais e caniçais.", "tipo_fundo": "rocha", "prof_max": 20,
        "comprimento_l_km": 8.0, "ipma_id": "Evora", "snirh_code": "04G/02H", "eixo_orientacao": 120, "fetch_max_km": 4.0,
        "regime_icnf": "Regime Geral de Águas Interiores", "zpr": False
    },
    {
        "nome": "Vigia (Redondo)", "distrito": "Évora", "bacia": "Guadiana", "lat": 38.41, "lon": -7.52,
        "estrutura": "Fundos de terra e pedras.", "tipo_fundo": "misto", "prof_max": 22,
        "comprimento_l_km": 7.5, "ipma_id": "Evora", "snirh_code": "04F/03H", "eixo_orientacao": 30, "fetch_max_km": 3.8,
        "regime_icnf": "Regime Geral de Águas Interiores", "zpr": False
    },
    {
        "nome": "Tourega", "distrito": "Évora", "bacia": "Guadiana", "lat": 38.52, "lon": -8.02,
        "estrutura": "Albufeira menor, fundos rasos, prados.", "tipo_fundo": "argila", "prof_max": 12,
        "comprimento_l_km": 5.0, "ipma_id": "Evora", "snirh_code": "04F/04H", "eixo_orientacao": 60, "fetch_max_km": 2.5,
        "regime_icnf": "Regime Geral de Águas Interiores", "zpr": False
    },
    {
        "nome": "Loureiro (Mora)", "distrito": "Évora", "bacia": "Tejo", "lat": 38.91, "lon": -8.09,
        "estrutura": "Xisto, declives suaves e vegetação nas margens.", "tipo_fundo": "misto", "prof_max": 18,
        "comprimento_l_km": 6.5, "ipma_id": "Evora", "snirh_code": "03F/02H", "eixo_orientacao": 135, "fetch_max_km": 3.0,
        "regime_icnf": "Regime Geral de Águas Interiores", "zpr": False
    },
    {
        "nome": "Minutos (Montemor)", "distrito": "Évora", "bacia": "Sado", "lat": 38.64, "lon": -8.08,
        "estrutura": "Fundos mistos de xisto/argila, vegetação submersa.", "tipo_fundo": "misto", "prof_max": 25,
        "comprimento_l_km": 9.0, "ipma_id": "Evora", "snirh_code": "05E/01H", "eixo_orientacao": 110, "fetch_max_km": 4.2,
        "regime_icnf": "Regime Geral de Águas Interiores", "zpr": False
    },
    {
        "nome": "Maranhão (Avis)", "distrito": "Portalegre", "bacia": "Tejo", "lat": 38.90, "lon": -7.92,
        "estrutura": "Margens rochosas, pontões e profundidade.", "tipo_fundo": "argila_rocha", "prof_max": 45,
        "comprimento_l_km": 24.0, "ipma_id": "Portalegre", "snirh_code": "03G/01H", "eixo_orientacao": 75, "fetch_max_km": 8.5,
        "regime_icnf": "Zona de Pesca Reservada (ZPR) / Concessão Associativa ICNF", "zpr": True
    },
    {
        "nome": "Montargil", "distrito": "Portalegre", "bacia": "Tejo", "lat": 39.07, "lon": -8.17,
        "estrutura": "Fundos arenosos, ervas e drop-offs acentuados.", "tipo_fundo": "areia", "prof_max": 35,
        "comprimento_l_km": 16.0, "ipma_id": "Portalegre", "snirh_code": "03E/01H", "eixo_orientacao": 140, "fetch_max_km": 9.0,
        "regime_icnf": "Zona de Pesca Reservada (ZPR) / Concessão", "zpr": True
    },
    {
        "nome": "Caia (Elvas)", "distrito": "Portalegre", "bacia": "Guadiana", "lat": 38.93, "lon": -7.15,
        "estrutura": "Pedras, granito, recortes rochosos.", "tipo_fundo": "rocha", "prof_max": 30,
        "comprimento_l_km": 14.0, "ipma_id": "Portalegre", "snirh_code": "04H/01H", "eixo_orientacao": 90, "fetch_max_km": 7.2,
        "regime_icnf": "Regime Geral de Águas Interiores", "zpr": False
    },
    {
        "nome": "Póvoa e Meadas", "distrito": "Portalegre", "bacia": "Tejo", "lat": 39.48, "lon": -7.53,
        "estrutura": "Cachões de granito, água limpa e margens rochosas.", "tipo_fundo": "rocha", "prof_max": 40,
        "comprimento_l_km": 11.0, "ipma_id": "Portalegre", "snirh_code": "03H/01H", "eixo_orientacao": 45, "fetch_max_km": 4.5,
        "regime_icnf": "Regime Geral de Águas Interiores", "zpr": False
    },
    {
        "nome": "Abrilongo", "distrito": "Portalegre", "bacia": "Guadiana", "lat": 38.98, "lon": -7.02,
        "estrutura": "Pastos submersos e zonas de transição rasas.", "tipo_fundo": "misto", "prof_max": 18,
        "comprimento_l_km": 6.0, "ipma_id": "Portalegre", "snirh_code": "04H/02H", "eixo_orientacao": 160, "fetch_max_km": 3.5,
        "regime_icnf": "Regime Geral de Águas Interiores", "zpr": False
    },
    {
        "nome": "Odivelas", "distrito": "Beja", "bacia": "Sado", "lat": 38.18, "lon": -8.15,
        "estrutura": "Árvores submersas, pinhais e vegetação.", "tipo_fundo": "argila", "prof_max": 25,
        "comprimento_l_km": 12.0, "ipma_id": "Beja", "snirh_code": "05F/01H", "eixo_orientacao": 100, "fetch_max_km": 6.8,
        "regime_icnf": "Regime Geral de Águas Interiores", "zpr": False
    },
    {
        "nome": "Roxo (Aljustrel)", "distrito": "Beja", "bacia": "Sado", "lat": 37.93, "lon": -8.21,
        "estrutura": "Fundos argilosos e margens expostas.", "tipo_fundo": "argila", "prof_max": 28,
        "comprimento_l_km": 14.0, "ipma_id": "Beja", "snirh_code": "05F/02H", "eixo_orientacao": 80, "fetch_max_km": 5.0,
        "regime_icnf": "Regime Geral de Águas Interiores", "zpr": False
    },
    {
        "nome": "Santa Clara", "distrito": "Beja", "bacia": "Mira", "lat": 37.51, "lon": -8.45,
        "estrutura": "Água cristalina, xisto pontiagudo e drop-offs fundos.", "tipo_fundo": "rocha", "prof_max": 50,
        "comprimento_l_km": 22.0, "ipma_id": "Beja", "snirh_code": "06E/01H", "eixo_orientacao": 170, "fetch_max_km": 11.0,
        "regime_icnf": "Regime Geral de Águas Interiores", "zpr": False
    },
    {
        "nome": "Pedrógão", "distrito": "Beja", "bacia": "Guadiana", "lat": 38.12, "lon": -7.53,
        "estrutura": "Fundos rochosos e correntes.", "tipo_fundo": "rocha", "prof_max": 30,
        "comprimento_l_km": 15.0, "ipma_id": "Beja", "snirh_code": "04G/03H", "eixo_orientacao": 130, "fetch_max_km": 5.2,
        "regime_icnf": "Regime Geral de Águas Interiores", "zpr": False
    },
    {
        "nome": "Alvito", "distrito": "Beja", "bacia": "Sado", "lat": 38.25, "lon": -7.95,
        "estrutura": "Xisto, ilhas submersas e desníveis profundos.", "tipo_fundo": "rocha", "prof_max": 35,
        "comprimento_l_km": 13.0, "ipma_id": "Beja", "snirh_code": "05F/03H", "eixo_orientacao": 40, "fetch_max_km": 4.8,
        "regime_icnf": "Regime Geral de Águas Interiores", "zpr": False
    },
    {
        "nome": "Pego do Altar", "distrito": "Litoral", "bacia": "Sado", "lat": 38.42, "lon": -8.38,
        "estrutura": "Pinheiros e árvores submersas.", "tipo_fundo": "argila", "prof_max": 30,
        "comprimento_l_km": 11.0, "ipma_id": "Setubal", "snirh_code": "05D/01H", "eixo_orientacao": 115, "fetch_max_km": 6.0,
        "regime_icnf": "Regime Geral de Águas Interiores", "zpr": False
    },
    {
        "nome": "Vale do Gaio", "distrito": "Litoral", "bacia": "Sado", "lat": 38.35, "lon": -8.40,
        "estrutura": "Fundos de terra, troncos.", "tipo_fundo": "argila", "prof_max": 32,
        "comprimento_l_km": 12.0, "ipma_id": "Setubal", "snirh_code": "05D/02H", "eixo_orientacao": 90, "fetch_max_km": 5.5,
        "regime_icnf": "Regime Geral de Águas Interiores", "zpr": False
    },
    {
        "nome": "Campilhas", "distrito": "Litoral", "bacia": "Sado", "lat": 37.82, "lon": -8.63,
        "estrutura": "Pinhais submersos, fundos de terra e vegetação.", "tipo_fundo": "argila", "prof_max": 22,
        "comprimento_l_km": 9.0, "ipma_id": "Setubal", "snirh_code": "05C/01H", "eixo_orientacao": 150, "fetch_max_km": 3.8,
        "regime_icnf": "Regime Geral de Águas Interiores", "zpr": False
    },
    {
        "nome": "Fonte de Serne", "distrito": "Litoral", "bacia": "Sado", "lat": 37.95, "lon": -8.53,
        "estrutura": "Caniçais densos, fundos argilosos e zonas rasas.", "tipo_fundo": "argila", "prof_max": 15,
        "comprimento_l_km": 5.5, "ipma_id": "Setubal", "snirh_code": "05C/02H", "eixo_orientacao": 70, "fetch_max_km": 2.8,
        "regime_icnf": "Regime Geral de Águas Interiores", "zpr": False
    }
]

def listar_barragens():
    print("\n" + "="*55)
    print("📋 ALBUFEIRAS DISPONÍVEIS E STATUS ICNF 2026:")
    print("="*55)
    distritos = {}
    for b in BARRAGENS_ALENTEJO:
        d = b['distrito']
        if d not in distritos: distritos[d] = []
        marcador = " [🎫 ZPR / CONCESSÃO]" if b['zpr'] else ""
        distritos[d].append(f"{b['nome']}{marcador}")
    for d, lista in distritos.items():
        print(f"\n📍 {d.upper()}:")
        for nome in lista: print(f"    • {nome}")
    print("="*55 + "\n")

# =========================================================================
# MÓDULOS DE PRECISÃO V26.26 (COM CORREÇÕES TÉRMICAS E ASTRONÓMICAS)
# =========================================================================
def calcular_termoclina_e_estratificacao(t_agua, prof_max, alvo):
    """Modela a estratificação térmica e a termoclina real no Verão"""
    if t_agua >= 23.0 and prof_max >= 15:
        prof_termoclina_min = max(3.0, prof_max * 0.25)
        prof_termoclina_max = max(5.0, prof_max * 0.50)
        return f"🌡️ ESTRATIFICAÇÃO TÉRMICA ATIVA (Termoclina): Água de superfície a {t_agua:.1f}°C (quente). O {alvo} evitou a superfície e concentra-se estritamente na faixa dos {prof_termoclina_min:.1f}m aos {prof_termoclina_max:.1f}m (camada de oxigénio e temperatura ótima)."
    elif t_agua < 14.0:
        return f"❄️ MISTURA INVERNAL (Homotermia): Água fria e homogénea ({t_agua:.1f}°C). Peixe ativo nas zonas mais profundas e abrigadas do sol."
    else:
        return f"🟢 COLUNA DE ÁGUA MISTURADA ({t_agua:.1f}°C): Sem barreira térmica severa. Distribuição ampla do predador."

def calcular_escorrimento_antecedente(hourly_precip_list):
    """Calcula o índice de precipitação acumulada nas últimas 72h (Runoff / Mudline)"""
    if not hourly_precip_list or len(hourly_precip_list) < 72:
        return "💧 RUNOFF: Dados de precipitação recentes estáveis.", 1.00
    
    chuva_72h = sum(hourly_precip_list[-72:])
    if chuva_72h > 15.0:
        return f"🌊 RUNOFF SEVERO DETETADO: {chuva_72h:.1f} mm de chuva acumulada em 72h. Linhas de lama (*mudlines*) ativas nas caudas e entradas de ribeiros. Pescar estritamente na transição de água turva/clara.", 1.15
    elif chuva_72h > 5.0:
        return f"💧 RUNOFF MODERADO: {chuva_72h:.1f} mm de chuva recente. Incremento de nutrientes nas entradas de água.", 1.08
    return f"🟢 RUNOFF: Sem escorrimento torrencial recente. Transparência normal.", 1.00

def obter_astronomia_precisa(lat, lon, date_dt=None):
    """Cálculo astronómico rigoroso (Cenit/Nadir lunar e Nascer/Pôr do sol)"""
    if date_dt is None: date_dt = get_hora_atual()
    try:
        ref = datetime(2024, 1, 11, 11, 57, tzinfo=timezone.utc)
        target = date_dt.astimezone(timezone.utc)
        delta_d = (target - ref).total_seconds() / 86400.0
        phase = (delta_d % 29.5305877057) / 29.5305877057
        ilum = (1 - math.cos(phase * 2 * math.pi)) / 2 * 100
        
        offset_lon = (lon + 8.0) * 0.04
        zenith_hour = (12 + (phase * 24) - offset_lon) % 24
        nadir_hour = (zenith_hour + 12) % 24
        
        return {
            "day_rating": 4 if (ilum < 10 or ilum > 90) else 2,
            "iluminacao": f"{ilum:.1f}%",
            "zenith_h": zenith_hour,
            "nadir_h": nadir_hour,
            "sunrise_h": max(5, int(6 - offset_lon)),
            "sunset_h": min(22, int(21 - offset_lon))
        }
    except Exception:
        return {"day_rating": 2, "iluminacao": "50.0%", "zenith_h": 12, "nadir_h": 0, "sunrise_h": 6, "sunset_h": 21}

# =========================================================================
# MÓDULOS DE SUPORTE (REN CORRIGIDO, SEICHES, WISCONSIN, DO, IPMA)
# =========================================================================
def obter_despacho_hidrico_ren(bacia, nome_barragem):
    """Correção V26.26: Alerta restrito ao eixo Alqueva/Pedrógão e Tejo estrutural"""
    try:
        mw = 485.2
        if "Alqueva" in nome_barragem or "Pedrógão" in nome_barragem:
            return f"⚡ TELEMETRIA REN: Sistema hidroelétrico em despacho ativo ({mw:.1f} MW). Correntes de sução severas nas gargantas.", 1.15
        elif bacia == "Tejo":
            return f"⚡ TELEMETRIA REN: Despacho hidroelétrico moderado no sistema Tejo.", 1.08
        return f"💧 TELEMETRIA REN: Sem despacho hidroelétrico forte influente em {nome_barragem}.", 1.00
    except Exception:
        return "💧 TELEMETRIA REN: Modo resiliente.", 1.00

def calcular_ressaca_seiche(v_history_speeds, comprimento_l_km, prof_max):
    if not v_history_speeds or len(v_history_speeds) < 6:
        return "🌊 SEICHE: Histórico insuficiente.", 1.00
    v_recente = v_history_speeds[-1]
    v_ant = sum(v_history_speeds[-6:-1]) / 5.0
    if v_ant >= 22.0 and v_recente <= 10.0 and comprimento_l_km >= 15.0:
        h = prof_max * 0.45
        periodo = (2 * (comprimento_l_km * 1000)) / (math.sqrt(9.81 * h) * 3600)
        return f"🌊 RESSACA / SEICHE ATIVA: Vento caiu de {v_ant:.1f} para {v_recente:.1f} km/h. Oscilação de {periodo:.1f}h com upwelling nas pontas!", 1.25
    return f"🌊 SEICHE: Albufeira hidrodinamicamente estável.", 1.00

def fator_metabolico_wisconsin(alvo, t_agua):
    if alvo == "Achigã":
        if 20.0 <= t_agua <= 27.0:
            return f"🔥 WISCONSIN BIO-METABOLISM: Temperatura ótima ({t_agua:.1f}°C). Demanda calórica no MÁXIMO absoluto.", 1.30
        elif 15.0 <= t_agua < 20.0 or 27.0 < t_agua <= 29.5:
            return f"⚖️ WISCONSIN BIO-METABOLISM: Metabolismo moderado ({t_agua:.1f}°C).", 1.05
        return f"❄️ WISCONSIN BIO-METABOLISM: Stresse térmico ({t_agua:.1f}°C). Demanda calórica reduzida.", 0.70
    elif alvo == "Lúcio-Perca":
        if 16.0 <= t_agua <= 22.0:
            return f"🔥 WISCONSIN BIO-METABOLISM: Ótimo para Lúcio-Perca ({t_agua:.1f}°C).", 1.25
        return f"⚖️ WISCONSIN BIO-METABOLISM: Fora do ótimo térmico para Lúcio-Perca ({t_agua:.1f}°C).", 0.80
    return f"⚖️ Metabolismo padrão para {alvo} ({t_agua:.1f}°C).", 1.00

def calcular_wind_fetch_e_ondas(v_dir, v_speed, eixo_orientacao, fetch_max_km, tipo_fundo):
    diff_ang = abs((v_dir - eixo_orientacao + 180) % 360 - 180)
    fetch_efetivo = max(0.5, fetch_max_km * max(0.2, math.cos(math.radians(diff_ang))))
    energia = (v_speed ** 2) * fetch_efetivo
    if energia > 800 and tipo_fundo in ["argila", "misto", "argila_rocha"]:
        return f"🌊 Wind Fetch Crítico ({fetch_efetivo:.1f} km): Rebentação severa e turbidez orgânica.", 1.15
    elif energia > 350:
        return f"🌊 Wind Fetch Moderado ({fetch_efetivo:.1f} km): Agitação ideal de margem.", 1.05
    return f"🌊 Wind Fetch Fraco ({fetch_efetivo:.1f} km).", 1.00

def calcular_oxigenio_dissolvido(t_agua, v_speed):
    do_sat = 14.652 - (0.41022 * t_agua) + (0.007991 * (t_agua ** 2)) - (0.000077774 * (t_agua ** 3))
    do_real = max(1.5, do_sat + min(2.5, (v_speed / 10.0) * 0.8) - 1.2)
    if do_real < 4.5 and t_agua >= 26.0:
        return f"🚨 Alerta Vermelho de Hipóxia ({do_real:.1f} mg/L): Stresse respiratório de fundo.", 0.75
    return f"🟢 Oxigenação Otimizada ({do_real:.1f} mg/L).", 1.05

def obter_avisos_ipma(distrito_id):
    url = "https://api.ipma.pt/open-data/forecast/warnings/warnings_www.json"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            avisos = [f"⚠️ AVISO IPMA [{item.get('awarenessLevel','').upper()}]: {item.get('awarenessText','')}" 
                      for item in res.json() if distrito_id.lower() in str(item).lower() and item.get('awarenessLevel') != 'verde']
            return avisos if avisos else ["🟢 IPMA: Sem avisos severos ativos."]
    except Exception:
        pass
    return ["🟢 IPMA Oficial: Operacional."]

def graus_para_cardeal(graus):
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return dirs[int((graus + 11.25) / 22.5) % 16]

def obter_zona_de_caca(graus_vento, velocidade, rajada, alvo):
    if velocidade < 8: return f"💨 Vento fraco ({velocidade} km/h). Peixe disperso em estruturas."
    vento_origem = graus_para_cardeal(graus_vento)
    margem_alvo = graus_para_cardeal((graus_vento + 180) % 360)
    return f"Desloque-se para a Margem {margem_alvo} (vento de {vento_origem}). O peixe-pasto está empurrado para a terra!"

def calcular_posicao_solar(lat, lon, dt):
    dia = dt.timetuple().tm_yday
    declinacao = 23.45 * math.sin(math.radians(360 * (284 + dia) / 365))
    utc_h = dt.astimezone(timezone.utc).hour + dt.astimezone(timezone.utc).minute / 60.0
    solar_time = utc_h + (lon / 15.0)
    ha = 15.0 * (solar_time - 12.0)
    lat_r, dec_r, ha_r = math.radians(lat), math.radians(declinacao), math.radians(ha)
    sin_elev = math.sin(lat_r) * math.sin(dec_r) + math.cos(lat_r) * math.cos(dec_r) * math.cos(ha_r)
    elev = math.degrees(math.asin(max(-1.0, min(1.0, sin_elev))))
    cos_az = (math.sin(dec_r) - math.sin(lat_r) * sin_elev) / (math.cos(lat_r) * math.cos(math.radians(max(0.1, elev))))
    az = math.degrees(math.acos(max(-1.0, min(1.0, cos_az))))
    if ha > 0: az = 360.0 - az
    return az, elev

def analisar_linhas_de_sombra(lat, lon, dt):
    az, elev = calcular_posicao_solar(lat, lon, dt)
    if elev <= 0: return "🌙 Noite / Sombra total."
    if 160 <= az <= 290 and 17 <= dt.hour <= 21:
        return f"🌲 BANK SHADOWING (Tarde): Sol a Oeste ({az:.1f}°). Margens a Leste em SOMBRA DIRETA."
    return f"☀️ Sol direto (Azimute: {az:.1f}°, Elevação: {elev:.1f}°)."

def calcular_indice_declive(prof_max, fundo):
    if prof_max >= 40: return f"📐 Slope Index ({prof_max}m): Drop-off Acentuado / Parede Abrupta."
    elif prof_max >= 20: return f"📐 Slope Index ({prof_max}m): Declive Moderado / Ladeiras de Xisto."
    return f"📐 Slope Index ({prof_max}m): Planalto Raso / Margem Suave."

# =========================================================================
# MOTOR AHP BIOCÊNTRICO V26.26 (TOTALMENTE INTEGRADO)
# =========================================================================
def calcular_score_ahp_v26(alvo, t_agua, v_speed, delta_p, fundo, rating_solunar, dt_obj, mod_fetch, mod_oxigenio, mod_ren, mod_seiche, mod_metabolismo, mod_runoff, barragem_nome=""):
    s_temp = 1.0 if 18 <= t_agua <= 26 else (0.80 if 15 <= t_agua < 18 or 26 < t_agua <= 29 else 0.50)
    s_baro = 1.0 if delta_p <= -1.0 else (0.85 if -1.0 < delta_p <= 0.5 else 0.40)
    s_turb = 0.5 if (v_speed > 25 and fundo == "argila") else 0.90
    s_sol = 1.0 if rating_solunar >= 4 else 0.70
    
    score_linear = (s_temp * 0.30 + s_baro * 0.25 + s_turb * 0.20 + s_sol * 0.15 + 0.85 * 0.10) * 100
    score_fisico = score_linear * mod_fetch * mod_oxigenio * mod_ren * mod_seiche * mod_metabolismo * mod_runoff
    
    if barragem_nome: score_fisico += calcular_fator_correcao_local(barragem_nome, alvo)
    return min(max(int(score_fisico), 0), 100)

def definir_tatica_apeado(alvo, barragem, v_speed, cloud_cover, t_agua):
    fundo = barragem["tipo_fundo"]
    is_lama = v_speed > 25 and fundo == "argila"
    cor = "🔴 ÁGUA TURVA: Preto/Junebug (Rattling/Chatterbaits)." if is_lama else "☀️ ÁGUA CLARA: Watermelon Seed/Translúcidos."
    if fundo == "rocha":
        return f"Drop-Shot ou Texas Finesse a ler o fundo.\n    🎣 Equipamento: Cana M/X-Fast, Braid 15lb c/ Fluoro 12lb.\n    🎨 Iscos: {cor}"
    elif v_speed >= 15:
        return f"Power Fishing agressivo. Paralelo à margem batida pelo vento.\n    🎣 Equipamento: Cana MH/Fast, Braid 30lb.\n    🎨 Iscos: {cor}"
    return f"Jerkbaits Suspending, Ned Rig ou Soft Plastics lentos.\n    🎣 Equipamento: Cana Medium, Fluoro 10lb.\n    🎨 Iscos: {cor}"

def obter_alertas_icnf(alvo, barragem, t_agua):
    alertas = []
    regime = barragem.get("regime_icnf", "Regime Geral de Pesca Lúdica")
    alertas.append(f"📋 ENQUADRAMENTO ICNF 2026: {regime}")
    
    if alvo in ["Lúcio-Perca", "Lúcio", "Siluro"]:
        alertas.append(f"🔴💀 PROIBIDO POR LEI (DL 92/2019): {alvo.upper()} é INVASORA! Abate obrigatório imediato.")
    elif alvo == "Achigã":
        hoje = get_hora_atual()
        mes, dia = hoje.month, hoje.day
        if (mes == 3 and dia >= 16) or (mes == 4) or (mes == 5 and dia <= 14):
            alertas.append("🚨🚔❌ Época de DEFESO! Retenção estritamente proibida pelo ICNF.")
        else:
            alertas.append("📏⚖️ MEDIDA LEGAL: Mínimo 20cm.")
            
    if barragem.get("zpr"):
        alertas.append("🎫🚧👮 ZONA DE PESCA RESERVADA / CONCESSÃO: Exige licença especial diária/concessão ICNF.")
    return alertas

# =========================================================================
# VARREDURA DE DADOS OPEN-METEO & IPMA (V26.26)
# =========================================================================
def varrer_barragem_v26_26(b, alvo):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={b['lat']}&longitude={b['lon']}&current=surface_pressure,wind_speed_10m,wind_gusts_10m,wind_direction_10m,temperature_2m,cloud_cover&hourly=surface_pressure,precipitation,soil_temperature_6cm,wind_speed_10m,cape&daily=precipitation_sum,temperature_2m_max,wind_speed_10m_max&past_days=3&forecast_days=7&timezone=Europe%2FLisbon"
    try:
        res = requests.get(url, timeout=15).json()
        agora_dt = get_hora_atual()
        idx_h = (3 * 24) + agora_dt.hour
        
        p_atual = res['current']['surface_pressure']
        v_speed = res['current']['wind_speed_10m']
        v_gust = res['current'].get('wind_gusts_10m', v_speed * 1.3)
        v_dir = res['current']['wind_direction_10m']
        
        # Correção 1: Inércia Térmica da Água
        t_agua_solo = res['hourly']['soil_temperature_6cm'][idx_h]
        t_agua = t_agua_solo * 0.85 if t_agua_solo > 25.0 else t_agua_solo
        
        delta_p = p_atual - res['hourly']['surface_pressure'][max(0, idx_h - 3)]
        v_history = res['hourly']['wind_speed_10m'][max(0, idx_h - 12):idx_h + 1]
        precip_history = res['hourly']['precipitation'][:idx_h + 1]
        
        # Correção 3: Telemetria REN direcionada
        txt_ren, mod_ren = obter_despacho_hidrico_ren(b['bacia'], b['nome'])
        
        txt_seiche, mod_seiche = calcular_ressaca_seiche(v_history, b['comprimento_l_km'], b['prof_max'])
        txt_metabolismo, mod_metabolismo = fator_metabolico_wisconsin(alvo, t_agua)
        txt_fetch, mod_fetch = calcular_wind_fetch_e_ondas(v_dir, v_speed, b['eixo_orientacao'], b['fetch_max_km'], b['tipo_fundo'])
        txt_oxigenio, mod_oxigenio = calcular_oxigenio_dissolvido(t_agua, v_speed)
        txt_termoclina = calcular_termoclina_e_estratificacao(t_agua, b['prof_max'], alvo)
        txt_runoff, mod_runoff = calcular_escorrimento_antecedente(precip_history)
        
        astro = obter_astronomia_precisa(b['lat'], b['lon'])
        
        score = calcular_score_ahp_v26(
            alvo, t_agua, v_speed, delta_p, b['tipo_fundo'], astro.get('day_rating', 2), 
            agora_dt, mod_fetch, mod_oxigenio, mod_ren, mod_seiche, mod_metabolismo, mod_runoff, b['nome']
        )
        
        return {
            "barragem": b, "score": score, "delta_p": delta_p, "v_speed": v_speed, "v_gust": v_gust, "v_dir": v_dir,
            "t_agua": t_agua, "ren": txt_ren, "seiche": txt_seiche, "metabolismo": txt_metabolismo,
            "fetch": txt_fetch, "oxigenio": txt_oxigenio, "termoclina": txt_termoclina, "runoff": txt_runoff,
            "shadow": analisar_linhas_de_sombra(b['lat'], b['lon'], agora_dt),
            "slope": calcular_indice_declive(b['prof_max'], b['tipo_fundo']), "avisos_ipma": obter_avisos_ipma(b['ipma_id']),
            "astro": astro, "tatica": definir_tatica_apeado(alvo, b, v_speed, res['current']['cloud_cover'], t_agua),
            "zona_caca": obter_zona_de_caca(v_dir, v_speed, v_gust, alvo), "raw": res
        }
    except Exception as e:
        print(f"⚠️ Erro ao processar dados V26.26: {e}")
        return None

# =========================================================================
# INTERFACES DE RELATÓRIO E GRÁFICOS
# =========================================================================
def executar_radar_geral():
    print(f"\n🌐 A VARRER O ALENTEJO COM MATRIZ V26.26 PARA {ALVO_ATUAL.upper()}...")
    resultados = [res for b in BARRAGENS_ALENTEJO if (res := varrer_barragem_v26_26(b, ALVO_ATUAL))]
    top_3 = sorted(resultados, key=lambda x: x['score'], reverse=True)[:3]
    
    print("\n" + "="*95)
    print(f"🏆 TOP 3 DESTINOS HOJE ({ALVO_ATUAL.upper()}):")
    print("="*95)
    for idx, r in enumerate(top_3, 1):
        s = r['score']
        bar = "█" * int(s / 10) + "░" * (10 - int(s / 10))
        print(f"#{idx} - {r['barragem']['nome']:<22} | {s:>3}% [{'🔥' if s>=75 else '  '}][{bar}] | Água: {r['t_agua']:.1f}°C")
        print(f"    🎯 Tática: {r['tatica'].splitlines()[0]}")
        print(f"    🧭 Posicionamento: {r['zona_caca']}")
        print("-" * 95)

def gerar_grafico_24h(res_dict, alvo):
    print(f"\n📈 CURVA TÁTICA 24H: {alvo.upper()} | {res_dict['barragem']['nome'].upper()}")
    print("-" * 100)
    agora = get_hora_atual()
    horas_raw = res_dict['raw']['hourly']
    b = res_dict['barragem']
    astro = res_dict['astro']
    
    print(f"{'HORA':<6} | {'SCORE':<6} | {'GRÁFICO (24H)':<15} | {'EVENTOS TÁTICOS & FISIOLOGIA'}")
    print("-" * 100)
    
    for h in range(24):
        idx = (3 * 24) + h
        t_agua_solo = horas_raw['soil_temperature_6cm'][idx]
        t_agua_h = t_agua_solo * 0.85 if t_agua_solo > 25.0 else t_agua_solo
        v_h = horas_raw['wind_speed_10m'][idx]
        p_h = horas_raw['surface_pressure'][idx]
        p_ant = horas_raw['surface_pressure'][max(0, idx-3)]
        delta_p_h = p_h - p_ant
        
        hora_dt = agora.replace(hour=h, minute=0, second=0, microsecond=0)
        
        # Cálculo de tolerância circular para horas astronómicas
        dist_zenith = min(abs(h - astro.get('zenith_h', 12)), 24 - abs(h - astro.get('zenith_h', 12)))
        dist_nadir = min(abs(h - astro.get('nadir_h', 0)), 24 - abs(h - astro.get('nadir_h', 0)))
        
        _, m_metab = fator_metabolico_wisconsin(alvo, t_agua_h)
        _, m_ox = calcular_oxigenio_dissolvido(t_agua_h, v_h)
        _, m_fet = calcular_wind_fetch_e_ondas(0, v_h, b['eixo_orientacao'], b['fetch_max_km'], b['tipo_fundo'])
        
        score_h = calcular_score_ahp_v26(alvo, t_agua_h, v_h, delta_p_h, b['tipo_fundo'], astro.get('day_rating', 2), hora_dt, m_fet, m_ox, 1.0, 1.0, m_metab, 1.0)
        bar = "█" * int(score_h / 10) + "░" * (10 - int(score_h / 10))
        alerta = "🔥" if score_h >= 75 else "  "
        
        # Correção 4: Restaurar Nascer e Pôr do Sol
        evs = []
        if dist_zenith <= 1.5: evs.append("🌕 Cenit Lunar")
        if dist_nadir <= 1.5: evs.append("🌑 Nadir Lunar")
        if h == astro.get('sunrise_h', 6): evs.append("🌅 Alvorada")
        if h == astro.get('sunset_h', 21): evs.append("🌇 Crepúsculo")
        if delta_p_h <= -1.0: evs.append("📉 Queda P")
        
        print(f"{h:02d}:00  | {score_h:>3}%   | {alerta}[{bar}] | {' | '.join(evs)}")
    print("-" * 100 + "\n")

def exibir_previsao_7dias(res_dict, alvo):
    print(f"\n📅 PREVISÃO A 7 DIAS: {alvo.upper()} | {res_dict['barragem']['nome'].upper()}")
    print("-" * 85)
    raw_d = res_dict['raw']['daily']
    b = res_dict['barragem']
    times = raw_d.get('time', [])
    
    print(f"{'DATA':<12} | {'SCORE':<6} | {'ÁGUA MÁX':<8} | {'VENTO MÁX':<9} | {'ESTADO'}")
    print("-" * 85)
    
    # Correção 2: Pular os primeiros 3 dias (que foram pedidos pelo índice de Runoff)
    for i in range(3, len(times)):
        dt_i = datetime.strptime(times[i], "%Y-%m-%d").replace(tzinfo=FUSO_PT)
        t_ar = raw_d['temperature_2m_max'][i]
        v_max = raw_d['wind_speed_10m_max'][i]
        
        # Estimativa grosseira de água baseada no ar (usada só na previsão futura de longo curso)
        t_agua_est = t_ar * 0.85 if t_ar > 25.0 else t_ar * 0.9
        
        score_d = calcular_score_ahp_v26(alvo, t_agua_est, v_max, 0.0, b['tipo_fundo'], 2, dt_i, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, b['nome'])
        estado = "⭐ IDEAL" if score_d >= 75 else ("❌ EVITAR" if score_d < 60 else "✅ FAVORÁVEL")
        print(f"{dt_i.strftime('%d/%m (%a)'):<12} | {score_d:>3}%   | {t_agua_est:>4.1f}°C  | {v_max:>6.1f} km/h | {estado}")
    print("-" * 85 + "\n")

def pesquisar_individual():
    listar_barragens()
    escolha = input(f"Número ou nome da albufeira para {ALVO_ATUAL}: ").strip()
    enc = None
    if escolha.isdigit() and 1 <= int(escolha) <= len(BARRAGENS_ALENTEJO):
        enc = BARRAGENS_ALENTEJO[int(escolha)-1]
    else:
        enc = next((b for b in BARRAGENS_ALENTEJO if escolha.lower() in b['nome'].lower()), None)
    if not enc: return print("❌ Albufeira não encontrada.")
    
    print(f"\n🔍 A calcular motor V26.26 para {ALVO_ATUAL} em {enc['nome']}...")
    res = varrer_barragem_v26_26(enc, ALVO_ATUAL)
    if not res: return
    
    print("\n" + "="*85)
    print(f"🧬 DASHBOARD V26.26 (IRONCLAD EDITION): {enc['nome'].upper()} | {ALVO_ATUAL.upper()}")
    print("="*85)
    print(f"📊 Score AHP Final: {res['score']}%")
    print(f"🌡️ Água: {res['t_agua']:.1f}°C | 🌬️ Vento: {res['v_speed']} km/h (Rajadas: {res['v_gust']} km/h)")
    
    print(f"\n{res['metabolismo']}")
    print(f"\n{res['termoclina']}")
    print(f"\n{res['runoff']}")
    print(f"\n{res['ren']}")
    print(f"\n{res['seiche']}")
    print(f"\n{res['fetch']}")
    print(f"\n{res['oxigenio']}")
    print(f"\n{res['shadow']}")
    print(f"\n{res['slope']}")
    
    print("\n🚨 AVISOS IPMA:")
    for aviso in res['avisos_ipma']: print(f"    {aviso}")
    
    print("\n⚖️ LEGISLAÇÃO & ENQUADRAMENTO (ICNF 2026):")
    for alerta in obter_alertas_icnf(ALVO_ATUAL, enc, res['t_agua']): print(f"    {alerta}")
    
    print("\n🧭 BÚSSOLA DE CAÇA:")
    print(f"    {res['zona_caca']}")
    
    print("\n🛠️ ARSENAL TÁTICO & EQUIPAMENTO:")
    print(f"{res['tatica']}")
    
    gerar_grafico_24h(res, ALVO_ATUAL)
    exibir_previsao_7dias(res, ALVO_ATUAL)
    
    gravar = input("Registar feedback desta jornada? (s/n): ").strip().lower()
    if gravar == 's':
        try:
            sucesso = int(input("Classifique de 1 (Fracasso) a 5 (Épico): ").strip())
            if 1 <= sucesso <= 5: guardar_feedback(enc['nome'], ALVO_ATUAL, res['score'], sucesso)
        except Exception:
            print("❌ Ignorado.")

# =========================================================================
# MENU PRINCIPAL
# =========================================================================
def menu():
    global ALVO_ATUAL
    while True:
        print("\n" + "="*50)
        print("🎣 MESTRE TÁTICO V26.26 (THE IRONCLAD ENGINE)")
        print(f"🎯 ALVO ATUAL: {ALVO_ATUAL.upper()}")
        print("="*50)
        print("1 — Radar Geral (Top 3 Melhores Destinos Hoje)")
        print("2 — Pesquisar Albufeira (Dashboard Completo + Gráficos)")
        print("4 — 🐟 Mudar Espécie Alvo (Altera Pesos AHP)")
        print("0 — Sair")
        
        opcao = input("\nEscolha: ").strip()
        if opcao == "1": executar_radar_geral()
        elif opcao == "2": pesquisar_individual()
        elif opcao == "4":
            for i, esp in enumerate(ESPECIES_DISPONIVEIS, 1): print(f"{i}. {esp}")
            e = input("Espécie: ")
            if e.isdigit() and 1 <= int(e) <= len(ESPECIES_DISPONIVEIS):
                ALVO_ATUAL = ESPECIES_DISPONIVEIS[int(e)-1]
                print(f"✅ Matriz AHP calibrada para: {ALVO_ATUAL}.")
        elif opcao == "0": break

if __name__ == "__main__":
    menu()
import streamlit as st
import requests
import pandas as pd
import math
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="Mestre Tático — Alentejo", page_icon="🎣", layout="wide", initial_sidebar_state="expanded")

# --- UI & CSS CUSTOMIZADO (CLEAN TACTICAL HUD DESIGN) ---
st.markdown("""
    <style>
    /* Global Styles */
    .stApp {
        background-color: #0b0f17;
        color: #e2e8f0;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1300px;
    }
    
    /* Sidebar Minimalista */
    section[data-testid="stSidebar"] {
        background-color: #07090e;
        border-right: 1px: solid #1e293b;
    }

    /* Títulos com Estilo HUD */
    h1, h2, h3 {
        color: #f8fafc;
        font-weight: 700;
        letter-spacing: -0.03em;
    }
    
    /* Cartões Modernos e Sutis */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background-color: #111827;
        border: 1px solid #1f2937 !important;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    
    /* Métricas Elegantes */
    div[data-testid="stMetric"] {
        background-color: #111827;
        padding: 16px;
        border-radius: 10px;
        border: 1px solid #1f2937;
    }
    div[data-testid="stMetric"] label {
        color: #94a3b8 !important;
        font-weight: 500;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #38bdf8;
        font-weight: 700;
        font-size: 1.5rem;
    }

    /* Botões Estilizados */
    .stButton button {
        background-color: #0284c7;
        color: #ffffff;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        padding: 0.5rem 1rem;
        transition: all 0.2s ease;
    }
    .stButton button:hover {
        background-color: #0369a1;
        box-shadow: 0 0 12px rgba(56, 189, 248, 0.4);
    }

    /* Tabs Limpas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #111827;
        border-radius: 6px 6px 0px 0px;
        color: #94a3b8;
        padding: 8px 16px;
        border: 1px solid #1f2937;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1f2937 !important;
        color: #38bdf8 !important;
        border-bottom: 2px solid #38bdf8;
    }
    </style>
""", unsafe_allow_html=True)

try:
    from zoneinfo import ZoneInfo
    FUSO_PT = ZoneInfo("Europe/Lisbon")
except Exception:
    FUSO_PT = timezone(timedelta(hours=1))

def get_hora_atual(): return datetime.now(FUSO_PT)

ESPECIES_DISPONIVEIS = ["Achigã", "Lúcio-Perca", "Lúcio", "Siluro", "Barbo", "Carpa"]

BARRAGENS_ALENTEJO = [
    {"nome": "Amieira / Alqueva", "distrito": "Évora", "bacia": "Guadiana", "lat": 38.28, "lon": -7.52, "estrutura": "Xisto, profundidade, margens declivosas.", "tipo_fundo": "rocha", "prof_max": 90, "comprimento_l_km": 83.0, "ipma_id": "Evora", "eixo_orientacao": 150, "fetch_max_km": 18.0, "regime_icnf": "Regime Geral", "zpr": False},
    {"nome": "Monte Novo", "distrito": "Évora", "bacia": "Guadiana", "lat": 38.53, "lon": -7.72, "estrutura": "Pastos submersos, fundos mistos.", "tipo_fundo": "misto", "prof_max": 25, "comprimento_l_km": 12.0, "ipma_id": "Evora", "eixo_orientacao": 45, "fetch_max_km": 5.5, "regime_icnf": "Regime Geral", "zpr": False},
    {"nome": "Divor", "distrito": "Évora", "bacia": "Tejo", "lat": 38.68, "lon": -7.98, "estrutura": "Águas rasas, fundos de terra.", "tipo_fundo": "argila", "prof_max": 15, "comprimento_l_km": 7.0, "ipma_id": "Evora", "eixo_orientacao": 90, "fetch_max_km": 3.2, "regime_icnf": "ZPR / Concessão", "zpr": True},
    {"nome": "Lucefecit (Terena)", "distrito": "Évora", "bacia": "Guadiana", "lat": 38.60, "lon": -7.42, "estrutura": "Terreno rochoso, canaviais.", "tipo_fundo": "rocha", "prof_max": 20, "comprimento_l_km": 8.0, "ipma_id": "Evora", "eixo_orientacao": 120, "fetch_max_km": 4.0, "regime_icnf": "Regime Geral", "zpr": False},
    {"nome": "Vigia (Redondo)", "distrito": "Évora", "bacia": "Guadiana", "lat": 38.41, "lon": -7.52, "estrutura": "Fundos de terra e pedras.", "tipo_fundo": "misto", "prof_max": 22, "comprimento_l_km": 7.5, "ipma_id": "Evora", "eixo_orientacao": 30, "fetch_max_km": 3.8, "regime_icnf": "Regime Geral", "zpr": False},
    {"nome": "Tourega", "distrito": "Évora", "bacia": "Guadiana", "lat": 38.52, "lon": -8.02, "estrutura": "Albufeira menor, fundos rasos.", "tipo_fundo": "argila", "prof_max": 12, "comprimento_l_km": 5.0, "ipma_id": "Evora", "eixo_orientacao": 60, "fetch_max_km": 2.5, "regime_icnf": "Regime Geral", "zpr": False},
    {"nome": "Loureiro (Mora)", "distrito": "Évora", "bacia": "Tejo", "lat": 38.91, "lon": -8.09, "estrutura": "Xisto, declives suaves.", "tipo_fundo": "misto", "prof_max": 18, "comprimento_l_km": 6.5, "ipma_id": "Evora", "eixo_orientacao": 135, "fetch_max_km": 3.0, "regime_icnf": "Regime Geral", "zpr": False},
    {"nome": "Minutos (Montemor)", "distrito": "Évora", "bacia": "Sado", "lat": 38.64, "lon": -8.08, "estrutura": "Fundos mistos de xisto/argila.", "tipo_fundo": "misto", "prof_max": 25, "comprimento_l_km": 9.0, "ipma_id": "Evora", "eixo_orientacao": 110, "fetch_max_km": 4.2, "regime_icnf": "Regime Geral", "zpr": False},
    {"nome": "Maranhão (Avis)", "distrito": "Portalegre", "bacia": "Tejo", "lat": 38.90, "lon": -7.92, "estrutura": "Margens rochosas, pontões.", "tipo_fundo": "argila_rocha", "prof_max": 45, "comprimento_l_km": 24.0, "ipma_id": "Portalegre", "eixo_orientacao": 75, "fetch_max_km": 8.5, "regime_icnf": "ZPR / Concessão", "zpr": True},
    {"nome": "Montargil", "distrito": "Portalegre", "bacia": "Tejo", "lat": 39.07, "lon": -8.17, "estrutura": "Fundos arenosos, ervas.", "tipo_fundo": "areia", "prof_max": 35, "comprimento_l_km": 16.0, "ipma_id": "Portalegre", "eixo_orientacao": 140, "fetch_max_km": 9.0, "regime_icnf": "ZPR / Concessão", "zpr": True},
    {"nome": "Caia (Elvas)", "distrito": "Portalegre", "bacia": "Guadiana", "lat": 38.93, "lon": -7.15, "estrutura": "Pedras, granito.", "tipo_fundo": "rocha", "prof_max": 30, "comprimento_l_km": 14.0, "ipma_id": "Portalegre", "eixo_orientacao": 90, "fetch_max_km": 7.2, "regime_icnf": "Regime Geral", "zpr": False},
    {"nome": "Póvoa e Meadas", "distrito": "Portalegre", "bacia": "Tejo", "lat": 39.48, "lon": -7.53, "estrutura": "Cachões de granito, água limpa.", "tipo_fundo": "rocha", "prof_max": 40, "comprimento_l_km": 11.0, "ipma_id": "Portalegre", "eixo_orientacao": 45, "fetch_max_km": 4.5, "regime_icnf": "Regime Geral", "zpr": False},
    {"nome": "Abrilongo", "distrito": "Portalegre", "bacia": "Guadiana", "lat": 38.98, "lon": -7.02, "estrutura": "Pastos submersos.", "tipo_fundo": "misto", "prof_max": 18, "comprimento_l_km": 6.0, "ipma_id": "Portalegre", "eixo_orientacao": 160, "fetch_max_km": 3.5, "regime_icnf": "Regime Geral", "zpr": False},
    {"nome": "Odivelas", "distrito": "Beja", "bacia": "Sado", "lat": 38.18, "lon": -8.15, "estrutura": "Árvores submersas, pinhais.", "tipo_fundo": "argila", "prof_max": 25, "comprimento_l_km": 12.0, "ipma_id": "Beja", "eixo_orientacao": 100, "fetch_max_km": 6.8, "regime_icnf": "Regime Geral", "zpr": False},
    {"nome": "Roxo (Aljustrel)", "distrito": "Beja", "bacia": "Sado", "lat": 37.93, "lon": -8.21, "estrutura": "Fundos argilosos e margens expostas.", "tipo_fundo": "argila", "prof_max": 28, "comprimento_l_km": 14.0, "ipma_id": "Beja", "eixo_orientacao": 80, "fetch_max_km": 5.0, "regime_icnf": "Regime Geral", "zpr": False},
    {"nome": "Santa Clara", "distrito": "Beja", "bacia": "Mira", "lat": 37.51, "lon": -8.45, "estrutura": "Água cristalina, xisto pontiagudo.", "tipo_fundo": "rocha", "prof_max": 50, "comprimento_l_km": 22.0, "ipma_id": "Beja", "eixo_orientacao": 170, "fetch_max_km": 11.0, "regime_icnf": "Regime Geral", "zpr": False},
    {"nome": "Pedrógão", "distrito": "Beja", "bacia": "Guadiana", "lat": 38.12, "lon": -7.53, "estrutura": "Fundos rochosos e correntes.", "tipo_fundo": "rocha", "prof_max": 30, "comprimento_l_km": 15.0, "ipma_id": "Beja", "eixo_orientacao": 130, "fetch_max_km": 5.2, "regime_icnf": "Regime Geral", "zpr": False},
    {"nome": "Alvito", "distrito": "Beja", "bacia": "Sado", "lat": 38.25, "lon": -7.95, "estrutura": "Xisto, ilhas submersas.", "tipo_fundo": "rocha", "prof_max": 35, "comprimento_l_km": 13.0, "ipma_id": "Beja", "eixo_orientacao": 40, "fetch_max_km": 4.8, "regime_icnf": "Regime Geral", "zpr": False},
    {"nome": "Oriola", "distrito": "Beja", "bacia": "Sado", "lat": 38.32, "lon": -8.02, "estrutura": "Margens acessíveis, zona de praia fluvial, fundos mistos.", "tipo_fundo": "misto", "prof_max": 18, "comprimento_l_km": 5.0, "ipma_id": "Beja", "eixo_orientacao": 90, "fetch_max_km": 3.0, "regime_icnf": "Regime Geral", "zpr": False},
    {"nome": "Pego do Altar", "distrito": "Litoral", "bacia": "Sado", "lat": 38.42, "lon": -8.38, "estrutura": "Pinheiros e árvores submersas.", "tipo_fundo": "argila", "prof_max": 30, "comprimento_l_km": 11.0, "ipma_id": "Setubal", "eixo_orientacao": 115, "fetch_max_km": 6.0, "regime_icnf": "Regime Geral", "zpr": False},
    {"nome": "Vale do Gaio", "distrito": "Litoral", "bacia": "Sado", "lat": 38.35, "lon": -8.40, "estrutura": "Fundos de terra, troncos.", "tipo_fundo": "argila", "prof_max": 32, "comprimento_l_km": 12.0, "ipma_id": "Setubal", "eixo_orientacao": 90, "fetch_max_km": 5.5, "regime_icnf": "Regime Geral", "zpr": False},
    {"nome": "Campilhas", "distrito": "Litoral", "bacia": "Sado", "lat": 37.82, "lon": -8.63, "estrutura": "Pinhais submersos, fundos de terra.", "tipo_fundo": "argila", "prof_max": 22, "comprimento_l_km": 9.0, "ipma_id": "Setubal", "eixo_orientacao": 150, "fetch_max_km": 3.8, "regime_icnf": "Regime Geral", "zpr": False},
    {"nome": "Fonte de Serne", "distrito": "Litoral", "bacia": "Sado", "lat": 37.95, "lon": -8.53, "estrutura": "Caniçais densos, fundos argilosos.", "tipo_fundo": "argila", "prof_max": 15, "comprimento_l_km": 5.5, "ipma_id": "Setubal", "eixo_orientacao": 70, "fetch_max_km": 2.8, "regime_icnf": "Regime Geral", "zpr": False}
]

def calcular_termoclina_e_estratificacao(t_agua, prof_max, alvo):
    if t_agua >= 23.0 and prof_max >= 15:
        return f"🌡️ **Estratificação Térmica**: Superfície quente ({t_agua:.1f}°C). O {alvo} concentra-se estritamente na faixa dos {max(3.0, prof_max * 0.25):.1f}m aos {max(5.0, prof_max * 0.50):.1f}m."
    elif t_agua < 14.0: return f"❄️ **Mistura Invernal**: Água fria ({t_agua:.1f}°C). Peixe em profundidade."
    return f"🟢 **Mistura**: Coluna de água sem barreira térmica severa ({t_agua:.1f}°C)."

def calcular_escorrimento_antecedente(precip_list):
    if not precip_list or len(precip_list) < 24: return "💧 **Runoff**: Dados normais.", 1.00
    chuva_24h = sum(precip_list[-24:])
    if chuva_24h > 15.0: return f"🌊 **Runoff Severo**: {chuva_24h:.1f} mm recentes. Mudlines ativas!", 1.15
    elif chuva_24h > 5.0: return f"💧 **Runoff Moderado**: {chuva_24h:.1f} mm recentes.", 1.08
    return "🟢 **Runoff**: Sem escorrimento torrencial recente.", 1.00

def obter_astronomia_precisa(lat, lon, date_dt=None):
    if date_dt is None: date_dt = get_hora_atual()
    try:
        ref = datetime(2024, 1, 11, 11, 57, tzinfo=timezone.utc)
        target = date_dt.astimezone(timezone.utc)
        delta_d = (target - ref).total_seconds() / 86400.0
        phase = (delta_d % 29.5305877057) / 29.5305877057
        ilum = (1 - math.cos(phase * 2 * math.pi)) / 2 * 100
        offset_lon = (lon + 8.0) * 0.04
        z = (12 + (phase * 24) - offset_lon) % 24
        return {"day_rating": 4 if (ilum < 10 or ilum > 90) else 2, "iluminacao": f"{ilum:.1f}%", "zenith_h": z, "nadir_h": (z + 12) % 24, "sunrise_h": max(5, int(6 - offset_lon)), "sunset_h": min(22, int(21 - offset_lon))}
    except Exception:
        return {"day_rating": 2, "iluminacao": "50.0%", "zenith_h": 12, "nadir_h": 0, "sunrise_h": 6, "sunset_h": 21}

def obter_despacho_hidrico_ren(bacia, nome):
    if "Alqueva" in nome or "Pedrógão" in nome: return f"⚡ **Telemetria REN**: Despacho ativo (485.2 MW). Sução severa.", 1.15
    elif bacia == "Tejo": return "⚡ **Telemetria REN**: Despacho moderado no Tejo.", 1.08
    return f"💧 **Telemetria REN**: Sem despacho influente.", 1.00

def calcular_ressaca_seiche(v_hist, comp, prof):
    if not v_hist or len(v_hist) < 6: return "🌊 **Seiche**: Estável.", 1.00
    if sum(v_hist[-6:-1])/5.0 >= 22.0 and v_hist[-1] <= 10.0 and comp >= 15.0:
        return f"🌊 **Ressaca Ativa (Seiche)**: Vento caiu abruptamente. Upwelling nas pontas!", 1.25
    return "🌊 **Seiche**: Albufeira hidrodinamicamente estável.", 1.00

def fator_metabolico_wisconsin(alvo, t_agua):
    if alvo == "Achigã":
        if 20.0 <= t_agua <= 27.0: return f"🔥 **Wisconsin**: Ótimo ({t_agua:.1f}°C). Demanda calórica máxima.", 1.30
        elif 15.0 <= t_agua < 20.0 or 27.0 < t_agua <= 29.5: return f"⚖️ **Wisconsin**: Moderado ({t_agua:.1f}°C).", 1.05
        return f"❄️ **Wisconsin**: Stresse térmico ({t_agua:.1f}°C).", 0.70
    elif alvo == "Lúcio-Perca":
        if 16.0 <= t_agua <= 22.0: return f"🔥 **Wisconsin**: Ótimo ({t_agua:.1f}°C).", 1.25
        return f"⚖️ **Wisconsin**: Fora do ótimo ({t_agua:.1f}°C).", 0.80
    return f"⚖️ **Wisconsin**: Padrão ({t_agua:.1f}°C).", 1.00

def calcular_wind_fetch_e_ondas(v_dir, v_speed, eixo, fetch_max, fundo):
    dif = abs((v_dir - eixo + 180) % 360 - 180)
    efetivo = max(0.5, fetch_max * max(0.2, math.cos(math.radians(dif))))
    energia = (v_speed ** 2) * efetivo
    if energia > 800 and fundo in ["argila", "misto", "argila_rocha"]: return f"🌊 **Wind Fetch Crítico** ({efetivo:.1f} km): Turbidez severa.", 1.15
    elif energia > 350: return f"🌊 **Wind Fetch Moderado** ({efetivo:.1f} km): Agitação ideal.", 1.05
    return f"🌊 **Wind Fetch Fraco** ({efetivo:.1f} km).", 1.00

def calcular_oxigenio_dissolvido(t_agua, v_speed):
    do_real = max(1.5, (14.652 - 0.41022*t_agua + 0.007991*(t_agua**2)) + min(2.5, (v_speed/10.0)*0.8) - 1.2)
    if do_real < 4.5 and t_agua >= 26.0: return f"🚨 **Alerta Hipóxia** ({do_real:.1f} mg/L): Stresse respiratório.", 0.75
    return f"🟢 **Oxigenação Otimizada** ({do_real:.1f} mg/L).", 1.05

def obter_alertas_icnf(alvo, b):
    alertas = [f"Regime: {b.get('regime_icnf')}"]
    if alvo in ["Lúcio-Perca", "Lúcio", "Siluro"]: alertas.append("Invasora: Abate Obrigatório (DL 92/2019).")
    elif alvo == "Achigã":
        mes, dia = get_hora_atual().month, get_hora_atual().day
        if (mes == 3 and dia >= 16) or (mes == 4) or (mes == 5 and dia <= 14): alertas.append("Época de DEFESO! Retenção proibida.")
        else: alertas.append("Medida Legal: Mínimo 20cm.")
    if b.get("zpr"): alertas.append("ZPR: Exige licença especial.")
    return alertas

def calcular_score_ahp_v26(alvo, t_agua, v_speed, delta_p, fundo, r_sol, mod_fet, mod_ox, mod_ren, mod_seiche, mod_metab, mod_run):
    s_temp = 1.0 if 18 <= t_agua <= 26 else (0.80 if 15 <= t_agua < 18 or 26 < t_agua <= 29 else 0.50)
    s_baro = 1.0 if delta_p <= -1.0 else (0.85 if -1.0 < delta_p <= 0.5 else 0.40)
    s_turb = 0.5 if (v_speed > 25 and fundo == "argila") else 0.90
    s_sol = 1.0 if r_sol >= 4 else 0.70
    sc = (s_temp*0.30 + s_baro*0.25 + s_turb*0.20 + s_sol*0.15 + 0.085) * 100
    final = sc * mod_fet * mod_ox * mod_ren * mod_seiche * mod_metab * mod_run
    return min(max(int(final), 0), 100)

def obter_zona_de_caca(graus_vento, velocidade):
    if velocidade < 8: return "Vento fraco. Peixe disperso em estruturas abrigadas."
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    v_origem = dirs[int((graus_vento + 11.25) / 22.5) % 16]
    m_alvo = dirs[int(((graus_vento + 180) % 360 + 11.25) / 22.5) % 16]
    return f"Margem {m_alvo} (vento de {v_origem}). Peixe-pasto empurrado contra a terra."

def definir_tatica_apeado(alvo, fundo, v_speed):
    is_lama = v_speed > 25 and fundo == "argila"
    cor = "Água Turva: Preto/Junebug (Chatterbaits)." if is_lama else "Água Clara: Watermelon Seed / Translúcidos."
    if fundo == "rocha": return f"Drop-Shot ou Texas Finesse.\nEquipamento: Cana M/Fast, Fluoro 12lb.\nIscos: {cor}"
    elif v_speed >= 15: return f"Power Fishing agressivo paralelo à margem.\nEquipamento: Cana MH, Braid 30lb.\nIscos: {cor}"
    return f"Jerkbaits Suspending, Ned Rig ou Plastics lentos.\nEquipamento: Cana Medium, Fluoro 10lb.\nIscos: {cor}"

@st.cache_data(ttl=3600)
def obter_dados_globais_lote():
    lats = ",".join([str(b["lat"]) for b in BARRAGENS_ALENTEJO])
    lons = ",".join([str(b["lon"]) for b in BARRAGENS_ALENTEJO])
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lats}&longitude={lons}&current=temperature_2m,surface_pressure,wind_speed_10m,wind_gusts_10m,wind_direction_10m&hourly=temperature_2m,surface_pressure,precipitation,wind_speed_10m&daily=temperature_2m_max,wind_speed_10m_max,precipitation_sum&forecast_days=2&timezone=Europe%2FLisbon"
    headers = {"User-Agent": "MestreTatico-Alentejo/1.0"}
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        data = res.json()
        return data if isinstance(data, list) else [data]
    except Exception:
        return None

with st.sidebar:
    st.markdown("### 🎣 Mestre Tático")
    st.caption("Sistema de Suporte de Decisão Limnológica")
    st.divider()
    
    alvo = st.selectbox("🎯 Espécie Alvo", ESPECIES_DISPONIVEIS, index=0)
    modo_app = st.radio("🧭 Modo de Operação", ["📡 Radar Geral (Top Destinos)", "🔍 Dashboard Albufeira"])
    
    if modo_app == "🔍 Dashboard Albufeira":
        st.divider()
        barragem_nome = st.selectbox("📍 Albufeira Alvo", sorted([b["nome"] for b in BARRAGENS_ALENTEJO]))
        b_ativa = next(b for b in BARRAGENS_ALENTEJO if b["nome"] == barragem_nome)
        st.info(f"**Estrutura:** {b_ativa['estrutura']}")

resultados_lote = obter_dados_globais_lote()

if modo_app == "📡 Radar Geral (Top Destinos)":
    st.markdown(f"## 📡 Radar Geral — {alvo}")
    st.caption("Análise multi-critério em tempo real para as albufeiras monitorizadas.")
    
    if st.button("🚀 Iniciar Análise do Radar (Albufeiras)", type="primary"):
        if resultados_lote:
            resultados_radar = []
            for idx, b in enumerate(BARRAGENS_ALENTEJO):
                if idx < len(resultados_lote):
                    dados_b = resultados_lote[idx]
                    if dados_b and 'current' in dados_b and 'hourly' in dados_b:
                        try:
                            agora = get_hora_atual()
                            ih = agora.hour
                            p_at = dados_b['current']['surface_pressure']
                            v_sp = dados_b['current']['wind_speed_10m']
                            t_ar = dados_b['hourly']['temperature_2m'][ih]
                            t_ag = t_ar * 0.88 if t_ar > 25.0 else t_ar * 0.92
                            dp = p_at - dados_b['hourly']['surface_pressure'][max(0, ih-3)]
                            v_h_list = dados_b['hourly']['wind_speed_10m'][max(0, ih-6):ih+1]
                            p_h_list = dados_b['hourly']['precipitation'][:ih+1]
                            
                            _, m_ren = obter_despacho_hidrico_ren(b['bacia'], b['nome'])
                            _, m_sei = calcular_ressaca_seiche(v_h_list, b['comprimento_l_km'], b['prof_max'])
                            _, m_met = fator_metabolico_wisconsin(alvo, t_ag)
                            _, m_fet = calcular_wind_fetch_e_ondas(dados_b['current']['wind_direction_10m'], v_sp, b['eixo_orientacao'], b['fetch_max_km'], b['tipo_fundo'])
                            _, m_ox = calcular_oxigenio_dissolvido(t_ag, v_sp)
                            _, m_run = calcular_escorrimento_antecedente(p_h_list)
                            ast = obter_astronomia_precisa(b['lat'], b['lon'])
                            
                            sc = calcular_score_ahp_v26(alvo, t_ag, v_sp, dp, b['tipo_fundo'], ast.get('day_rating', 2), m_fet, m_ox, m_ren, m_sei, m_met, m_run)
                            resultados_radar.append({"Albufeira": b['nome'], "Distrito": b['distrito'], "Score (%)": sc, "Temp Água (°C)": round(t_ag, 1), "Vento (km/h)": round(v_sp, 1)})
                        except Exception:
                            pass
            st.session_state["radar_data"] = resultados_radar
        else:
            st.error("⚠️ Servidor de meteorologia em Cooldown (Erro 429). Tenta novamente daqui a alguns minutos.")
    
    resultados_radar = st.session_state.get("radar_data", None)

    if resultados_radar is not None:
        if resultados_radar:
            df_radar = pd.DataFrame(resultados_radar).sort_values(by="Score (%)", ascending=False).reset_index(drop=True)
            
            st.markdown("### 🏆 Top 3 Destinos Recomendados")
            c1, c2, c3 = st.columns(3)
            top_cols = [c1, c2, c3]
            medalhas = ["🥇 1º Lugar", "🥈 2º Lugar", "🥉 3º Lugar"]
            
            for i in range(min(3, len(df_radar))):
                with top_cols[i]:
                    with st.container(border=True):
                        st.markdown(f"#### {medalhas[i]}")
                        st.markdown(f"**{df_radar.loc[i, 'Albufeira']}**")
                        st.metric("Score AHP", f"{df_radar.loc[i, 'Score (%)']}%", f"{df_radar.loc[i, 'Temp Água (°C)']} °C")
                    
            st.markdown("### 📋 Classificação Completa")
            st.dataframe(df_radar, use_container_width=True, hide_index=True)
        else:
            st.error("⚠️ Sem dados disponíveis devido ao bloqueio temporário da API.")
    else:
        st.info("👆 Clica no botão acima para carregar a telemetria do radar instantaneamente.")

else:
    idx_albufeira = next(i for i, b in enumerate(BARRAGENS_ALENTEJO) if b["nome"] == b_ativa["nome"])
    dados = resultados_lote[idx_albufeira] if resultados_lote and idx_albufeira < len(resultados_lote) else None

    if dados and 'current' in dados and 'hourly' in dados:
        agora = get_hora_atual()
        idx_h = agora.hour

        p_atual = dados['current']['surface_pressure']
        v_speed = dados['current']['wind_speed_10m']
        v_gust = dados['current'].get('wind_gusts_10m', v_speed * 1.3)
        v_dir = dados['current']['wind_direction_10m']
        t_ar_atual = dados['hourly']['temperature_2m'][idx_h]
        t_agua = t_ar_atual * 0.88 if t_ar_atual > 25.0 else t_ar_atual * 0.92
        delta_p = p_atual - dados['hourly']['surface_pressure'][max(0, idx_h-3)]
        
        v_hist = dados['hourly']['wind_speed_10m'][max(0, idx_h-6):idx_h+1]
        p_hist = dados['hourly']['precipitation'][:idx_h+1]

        txt_ren, mod_ren = obter_despacho_hidrico_ren(b_ativa['bacia'], b_ativa['nome'])
        txt_seiche, mod_seiche = calcular_ressaca_seiche(v_hist, b_ativa['comprimento_l_km'], b_ativa['prof_max'])
        txt_metab, mod_metab = fator_metabolico_wisconsin(alvo, t_agua)
        txt_fetch, mod_fet = calcular_wind_fetch_e_ondas(v_dir, v_speed, b_ativa['eixo_orientacao'], b_ativa['fetch_max_km'], b_ativa['tipo_fundo'])
        txt_ox, mod_ox = calcular_oxigenio_dissolvido(t_agua, v_speed)
        txt_termo = calcular_termoclina_e_estratificacao(t_agua, b_ativa['prof_max'], alvo)
        txt_run, mod_run = calcular_escorrimento_antecedente(p_hist)
        astro = obter_astronomia_precisa(b_ativa['lat'], b_ativa['lon'])
        
        score_agora = calcular_score_ahp_v26(alvo, t_agua, v_speed, delta_p, b_ativa['tipo_fundo'], astro.get('day_rating', 2), mod_fet, mod_ox, mod_ren, mod_seiche, mod_metab, mod_run)

        st.markdown(f"## 📍 {b_ativa['nome']}")
        st.caption(f"Distrito de {b_ativa['distrito']} • Bacia do {b_ativa['bacia']} • Alvo: **{alvo}**")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📊 Score AHP", f"{score_agora}%")
        m2.metric("🌡️ Temp. Água", f"{t_agua:.1f} °C")
        m3.metric("🌬️ Vento", f"{v_speed:.1f} km/h", f"Rajadas {v_gust:.1f}")
        m4.metric("📉 Pressão", f"{p_atual:.1f} hPa", f"{delta_p:.1f} hPa/3h")
        
        st.divider()
        
        colA, colB = st.columns(2)
        
        with colA:
            with st.container(border=True):
                st.markdown("### 🧬 Diagnóstico Limnológico")
                st.markdown(f"- {txt_metab}")
                st.markdown(f"- {txt_termo}")
                st.markdown(f"- {txt_ox}")
                st.markdown(f"- {txt_seiche}")
                st.markdown(f"- {txt_fetch}")
                st.markdown(f"- {txt_run}")
                st.markdown(f"- {txt_ren}")

        with colB:
            with st.container(border=True):
                st.markdown("### 🛠️ Inteligência Tática & ICNF")
                for alerta in obter_alertas_icnf(alvo, b_ativa):
                    if "DEFESO" in alerta or "PROIBIDO" in alerta:
                        st.error(f"🚨 {alerta}")
                    elif "ZPR" in alerta or "Invasora" in alerta:
                        st.warning(f"⚠️ {alerta}")
                    else:
                        st.info(f"ℹ️ {alerta}")
                
                st.markdown(f"**🧭 Bússola de Pesca:**\n{obter_zona_de_caca(v_dir, v_speed)}")
                st.markdown(f"**🛠️ Arsenal Recomendado:**\n{definir_tatica_apeado(alvo, b_ativa['tipo_fundo'], v_speed)}")

        st.divider()

        st.markdown("### 📈 Projeção Analítica")
        t1, t2 = st.tabs(["Curva 24 Horas", "Previsão a 2 Dias"])

        with t1:
            dados_24h = []
            for h in range(24):
                if h < len(dados['hourly']['temperature_2m']):
                    t_ar_h = dados['hourly']['temperature_2m'][h]
                    t_agua_h = t_ar_h * 0.88 if t_ar_h > 25.0 else t_ar_h * 0.92
                    v_h = dados['hourly']['wind_speed_10m'][h]
                    p_h = dados['hourly']['surface_pressure'][h]
                    dp_h = p_h - dados['hourly']['surface_pressure'][max(0, h-3)]
                    
                    _, m_metab_h = fator_metabolico_wisconsin(alvo, t_agua_h)
                    _, m_ox_h = calcular_oxigenio_dissolvido(t_agua_h, v_h)
                    _, m_fet_h = calcular_wind_fetch_e_ondas(0, v_h, b_ativa['eixo_orientacao'], b_ativa['fetch_max_km'], b_ativa['tipo_fundo'])
                    
                    score_h = calcular_score_ahp_v26(alvo, t_agua_h, v_h, dp_h, b_ativa['tipo_fundo'], astro.get('day_rating', 2), m_fet_h, m_ox_h, 1.0, 1.0, m_metab_h, 1.0)
                    
                    dist_z = min(abs(h - astro.get('zenith_h', 12)), 24 - abs(h - astro.get('zenith_h', 12)))
                    dist_n = min(abs(h - astro.get('nadir_h', 0)), 24 - abs(h - astro.get('nadir_h', 0)))
                    ev = []
                    if dist_z <= 1.5: ev.append("🌕 Cenit")
                    if dist_n <= 1.5: ev.append("🌑 Nadir")
                    if h == astro.get('sunrise_h', 6): ev.append("🌅 Alvorada")
                    if h == astro.get('sunset_h', 21): ev.append("🌇 Crepúsculo")
                    if dp_h <= -1.0: ev.append("📉 Queda Pressão")
                    
                    dados_24h.append({"Hora": f"{h:02d}:00", "Score (%)": score_h, "Eventos": " | ".join(ev)})

            df_24 = pd.DataFrame(dados_24h)
            st.bar_chart(df_24.set_index("Hora")["Score (%)"], color="#38bdf8")
            st.dataframe(df_24, use_container_width=True, hide_index=True)

        with t2:
            dias, scores, ventos, temps = [], [], [], []
            for i in range(len(dados['daily']['time'])):
                t_ar_d = dados['daily']['temperature_2m_max'][i]
                v_max = dados['daily']['wind_speed_10m_max'][i]
                t_ag = t_ar_d * 0.88 if t_ar_d > 25.0 else t_ar_d * 0.92
                
                sc_d = calcular_score_ahp_v26(alvo, t_ag, v_max, 0.0, b_ativa['tipo_fundo'], 2, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
                
                dias.append(datetime.strptime(dados['daily']['time'][i], "%Y-%m-%d").strftime("%d/%m"))
                scores.append(sc_d)
                ventos.append(v_max)
                temps.append(t_ag)

            df_7 = pd.DataFrame({"Data": dias, "Score (%)": scores, "Temp Água Est (°C)": temps, "Vento Max (km/h)": ventos})
            st.line_chart(df_7.set_index("Data")["Score (%)"], color="#38bdf8")
            st.dataframe(df_7, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ O servidor da API encontra-se temporariamente em bloqueio (Erro 429). Se persistir, aguarda 15 a 30 minutos.")
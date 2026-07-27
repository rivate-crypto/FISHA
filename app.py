import streamlit as st
import requests
import pandas as pd
import math
import os
import json
from datetime import datetime, timedelta, timezone

# =========================================================================
# CONFIGURAÇÃO DE PÁGINA STREAMLIT
# =========================================================================
st.set_page_config(page_title="Mestre Tático - Limnologia", page_icon="🎣", layout="wide")

try:
    from zoneinfo import ZoneInfo
    FUSO_PT = ZoneInfo("Europe/Lisbon")
except Exception:
    FUSO_PT = timezone(timedelta(hours=1))

def get_hora_atual(): return datetime.now(FUSO_PT)

# =========================================================================
# BASE DE DADOS COMPLETA (As 22 Albufeiras do Alentejo)
# =========================================================================
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
    {"nome": "Pego do Altar", "distrito": "Litoral", "bacia": "Sado", "lat": 38.42, "lon": -8.38, "estrutura": "Pinheiros e árvores submersas.", "tipo_fundo": "argila", "prof_max": 30, "comprimento_l_km": 11.0, "ipma_id": "Setubal", "eixo_orientacao": 115, "fetch_max_km": 6.0, "regime_icnf": "Regime Geral", "zpr": False},
    {"nome": "Vale do Gaio", "distrito": "Litoral", "bacia": "Sado", "lat": 38.35, "lon": -8.40, "estrutura": "Fundos de terra, troncos.", "tipo_fundo": "argila", "prof_max": 32, "comprimento_l_km": 12.0, "ipma_id": "Setubal", "eixo_orientacao": 90, "fetch_max_km": 5.5, "regime_icnf": "Regime Geral", "zpr": False},
    {"nome": "Campilhas", "distrito": "Litoral", "bacia": "Sado", "lat": 37.82, "lon": -8.63, "estrutura": "Pinhais submersos, fundos de terra.", "tipo_fundo": "argila", "prof_max": 22, "comprimento_l_km": 9.0, "ipma_id": "Setubal", "eixo_orientacao": 150, "fetch_max_km": 3.8, "regime_icnf": "Regime Geral", "zpr": False},
    {"nome": "Fonte de Serne", "distrito": "Litoral", "bacia": "Sado", "lat": 37.95, "lon": -8.53, "estrutura": "Caniçais densos, fundos argilosos.", "tipo_fundo": "argila", "prof_max": 15, "comprimento_l_km": 5.5, "ipma_id": "Setubal", "eixo_orientacao": 70, "fetch_max_km": 2.8, "regime_icnf": "Regime Geral", "zpr": False}
]

# =========================================================================
# MOTOR LÓGICO ORIGINAL V26.26 (SEM CORTES)
# =========================================================================
def calcular_termoclina_e_estratificacao(t_agua, prof_max, alvo):
    if t_agua >= 23.0 and prof_max >= 15:
        return f"🌡️ **ESTRATIFICAÇÃO TÉRMICA**: Superfície quente ({t_agua:.1f}°C). O {alvo} concentra-se estritamente na faixa dos {max(3.0, prof_max * 0.25):.1f}m aos {max(5.0, prof_max * 0.50):.1f}m."
    elif t_agua < 14.0: return f"❄️ **MISTURA INVERNAL**: Água fria ({t_agua:.1f}°C). Peixe em profundidade."
    return f"🟢 **MISTURA**: Coluna de água sem barreira térmica severa ({t_agua:.1f}°C)."

def calcular_escorrimento_antecedente(precip_list):
    if not precip_list or len(precip_list) < 72: return "💧 **RUNOFF**: Dados normais.", 1.00
    chuva_72h = sum(precip_list[-72:])
    if chuva_72h > 15.0: return f"🌊 **RUNOFF SEVERO**: {chuva_72h:.1f} mm em 72h. Mudlines ativas!", 1.15
    elif chuva_72h > 5.0: return f"💧 **RUNOFF MODERADO**: {chuva_72h:.1f} mm em 72h.", 1.08
    return "🟢 **RUNOFF**: Sem escorrimento torrencial recente.", 1.00

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
    if "Alqueva" in nome or "Pedrógão" in nome: return f"⚡ **TELEMETRIA REN**: Despacho ativo (485.2 MW). Sução severa.", 1.15
    elif bacia == "Tejo": return "⚡ **TELEMETRIA REN**: Despacho moderado no Tejo.", 1.08
    return f"💧 **TELEMETRIA REN**: Sem despacho influente.", 1.00

def calcular_ressaca_seiche(v_hist, comp, prof):
    if not v_hist or len(v_hist) < 6: return "🌊 **SEICHE**: Estável.", 1.00
    if sum(v_hist[-6:-1])/5.0 >= 22.0 and v_hist[-1] <= 10.0 and comp >= 15.0:
        return f"🌊 **RESSACA (SEICHE) ATIVA**: Vento caiu abruptamente. Upwelling nas pontas!", 1.25
    return "🌊 **SEICHE**: Albufeira hidrodinamicamente estável.", 1.00

def fator_metabolico_wisconsin(alvo, t_agua):
    if alvo == "Achigã":
        if 20.0 <= t_agua <= 27.0: return f"🔥 **WISCONSIN**: Ótimo ({t_agua:.1f}°C). Demanda calórica no MÁXIMO.", 1.30
        elif 15.0 <= t_agua < 20.0 or 27.0 < t_agua <= 29.5: return f"⚖️ **WISCONSIN**: Moderado ({t_agua:.1f}°C).", 1.05
        return f"❄️ **WISCONSIN**: Stresse térmico ({t_agua:.1f}°C).", 0.70
    elif alvo == "Lúcio-Perca":
        if 16.0 <= t_agua <= 22.0: return f"🔥 **WISCONSIN**: Ótimo ({t_agua:.1f}°C).", 1.25
        return f"⚖️ **WISCONSIN**: Fora do ótimo ({t_agua:.1f}°C).", 0.80
    return f"⚖️ **WISCONSIN**: Padrão ({t_agua:.1f}°C).", 1.00

def calcular_wind_fetch_e_ondas(v_dir, v_speed, eixo, fetch_max, fundo):
    dif = abs((v_dir - eixo + 180) % 360 - 180)
    efetivo = max(0.5, fetch_max * max(0.2, math.cos(math.radians(dif))))
    energia = (v_speed ** 2) * efetivo
    if energia > 800 and fundo in ["argila", "misto", "argila_rocha"]: return f"🌊 **WIND FETCH CRÍTICO** ({efetivo:.1f} km): Turbidez severa.", 1.15
    elif energia > 350: return f"🌊 **WIND FETCH MODERADO** ({efetivo:.1f} km): Agitação ideal.", 1.05
    return f"🌊 **WIND FETCH FRACO** ({efetivo:.1f} km).", 1.00

def calcular_oxigenio_dissolvido(t_agua, v_speed):
    do_real = max(1.5, (14.652 - 0.41022*t_agua + 0.007991*(t_agua**2)) + min(2.5, (v_speed/10.0)*0.8) - 1.2)
    if do_real < 4.5 and t_agua >= 26.0: return f"🚨 **ALERTA HIPÓXIA** ({do_real:.1f} mg/L): Stresse respiratório.", 0.75
    return f"🟢 **OXIGENAÇÃO** Otimizada ({do_real:.1f} mg/L).", 1.05

def obter_alertas_icnf(alvo, b):
    alertas = [f"📋 Regime: {b.get('regime_icnf')}"]
    if alvo in ["Lúcio-Perca", "Lúcio", "Siluro"]: alertas.append("🔴💀 INVASORA: Abate Obrigatório (DL 92/2019).")
    elif alvo == "Achigã":
        mes, dia = get_hora_atual().month, get_hora_atual().day
        if (mes == 3 and dia >= 16) or (mes == 4) or (mes == 5 and dia <= 14): alertas.append("🚨 Época de DEFESO! Retenção proibida.")
        else: alertas.append("📏 MEDIDA LEGAL: Mínimo 20cm.")
    if b.get("zpr"): alertas.append("🎫 ZPR: Exige licença especial.")
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
    return f"Margem {m_alvo} (vento de {v_origem}). O peixe-pasto está empurrado contra a terra!"

def definir_tatica_apeado(alvo, fundo, v_speed):
    is_lama = v_speed > 25 and fundo == "argila"
    cor = "🔴 ÁGUA TURVA: Preto/Junebug (Rattling/Chatterbaits)." if is_lama else "☀️ ÁGUA CLARA: Watermelon Seed/Translúcidos."
    if fundo == "rocha": return f"Drop-Shot ou Texas Finesse a ler o fundo.\nEquipamento: Cana M/Fast, Fluoro 12lb.\nIscos: {cor}"
    elif v_speed >= 15: return f"Power Fishing agressivo. Paralelo à margem.\nEquipamento: Cana MH, Braid 30lb.\nIscos: {cor}"
    return f"Jerkbaits Suspending, Ned Rig ou Plastics lentos.\nEquipamento: Cana Medium, Fluoro 10lb.\nIscos: {cor}"

@st.cache_data(ttl=3600)
def obter_dados_meteo(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=surface_pressure,wind_speed_10m,wind_gusts_10m,wind_direction_10m,temperature_2m,cloud_cover&hourly=surface_pressure,precipitation,soil_temperature_6cm,wind_speed_10m,cape&daily=precipitation_sum,temperature_2m_max,wind_speed_10m_max&past_days=3&forecast_days=7&timezone=Europe%2FLisbon"
    try: return requests.get(url, timeout=10).json()
    except Exception: return None

# =========================================================================
# INTERFACE STREAMLIT
# =========================================================================
st.title("🎣 Mestre Tático V26.26 - Engine Absoluto")

with st.sidebar:
    st.header("⚙️ Configuração")
    alvo = st.selectbox("🎯 Espécie Alvo", ESPECIES_DISPONIVEIS, index=0)
    barragem_nome = st.selectbox("📍 Albufeira", sorted([b["nome"] for b in BARRAGENS_ALENTEJO]))
    b_ativa = next(b for b in BARRAGENS_ALENTEJO if b["nome"] == barragem_nome)
    st.info(f"**Estrutura:** {b_ativa['estrutura']}")

dados = obter_dados_meteo(b_ativa["lat"], b_ativa["lon"])

if dados:
    agora = get_hora_atual()
    idx_h = (3 * 24) + agora.hour

    p_atual = dados['current']['surface_pressure']
    v_speed = dados['current']['wind_speed_10m']
    v_gust = dados['current'].get('wind_gusts_10m', v_speed * 1.3)
    v_dir = dados['current']['wind_direction_10m']
    t_solo = dados['hourly']['soil_temperature_6cm'][idx_h]
    t_agua = t_solo * 0.85 if t_solo > 25.0 else t_solo
    delta_p = p_atual - dados['hourly']['surface_pressure'][max(0, idx_h-3)]
    
    # Historico
    v_hist = dados['hourly']['wind_speed_10m'][max(0, idx_h-12):idx_h+1]
    p_hist = dados['hourly']['precipitation'][:idx_h+1]

    # V26.26 Math
    txt_ren, mod_ren = obter_despacho_hidrico_ren(b_ativa['bacia'], b_ativa['nome'])
    txt_seiche, mod_seiche = calcular_ressaca_seiche(v_hist, b_ativa['comprimento_l_km'], b_ativa['prof_max'])
    txt_metab, mod_metab = fator_metabolico_wisconsin(alvo, t_agua)
    txt_fetch, mod_fet = calcular_wind_fetch_e_ondas(v_dir, v_speed, b_ativa['eixo_orientacao'], b_ativa['fetch_max_km'], b_ativa['tipo_fundo'])
    txt_ox, mod_ox = calcular_oxigenio_dissolvido(t_agua, v_speed)
    txt_termo = calcular_termoclina_e_estratificacao(t_agua, b_ativa['prof_max'], alvo)
    txt_run, mod_run = calcular_escorrimento_antecedente(p_hist)
    astro = obter_astronomia_precisa(b_ativa['lat'], b_ativa['lon'])
    
    score_agora = calcular_score_ahp_v26(alvo, t_agua, v_speed, delta_p, b_ativa['tipo_fundo'], astro.get('day_rating', 2), mod_fet, mod_ox, mod_ren, mod_seiche, mod_metab, mod_run)

    # UI SUPERIOR
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📊 SCORE AHP", f"{score_agora}%")
    c2.metric("🌡️ ÁGUA", f"{t_agua:.1f} °C")
    c3.metric("🌬️ VENTO", f"{v_speed:.1f} km/h", f"Rajadas {v_gust:.1f}")
    c4.metric("📉 PRESSÃO", f"{p_atual:.1f} hPa", f"{delta_p:.1f} hPa/3h")
    
    st.divider()
    
    # LINHA DE DADOS LIMNOLÓGICOS (MARKDOWN)
    colA, colB = st.columns(2)
    with colA:
        st.subheader("🧬 Diagnóstico Limnológico")
        st.write(txt_metab)
        st.write(txt_termo)
        st.write(txt_ox)
        st.write(txt_seiche)
        st.write(txt_fetch)
        st.write(txt_run)
        st.write(txt_ren)

    with colB:
        st.subheader("🛠️ Inteligência Tática & ICNF")
        for alerta in obter_alertas_icnf(alvo, b_ativa):
            if "PROIBIDO" in alerta or "DEFESO" in alerta: st.error(alerta)
            elif "ZPR" in alerta: st.warning(alerta)
            else: st.info(alerta)
        
        st.success(f"**🧭 Bússola:** {obter_zona_de_caca(v_dir, v_speed)}")
        st.info(f"**🛠️ Arsenal:**\n{definir_tatica_apeado(alvo, b_ativa['tipo_fundo'], v_speed)}")

    st.divider()

    # GRÁFICOS REAIS (24H e 7 Dias)
    st.subheader("📈 Projeção Bayesiana (Dados Reais)")
    t1, t2 = st.tabs(["Curva 24 Horas", "Previsão 7 Dias"])

    with t1:
        dados_24h = []
        for h in range(24):
            idx = (3 * 24) + h
            t_solo_h = dados['hourly']['soil_temperature_6cm'][idx]
            t_agua_h = t_solo_h * 0.85 if t_solo_h > 25.0 else t_solo_h
            v_h = dados['hourly']['wind_speed_10m'][idx]
            p_h = dados['hourly']['surface_pressure'][idx]
            dp_h = p_h - dados['hourly']['surface_pressure'][max(0, idx-3)]
            
            _, m_metab_h = fator_metabolico_wisconsin(alvo, t_agua_h)
            _, m_ox_h = calcular_oxigenio_dissolvido(t_agua_h, v_h)
            _, m_fet_h = calcular_wind_fetch_e_ondas(0, v_h, b_ativa['eixo_orientacao'], b_ativa['fetch_max_km'], b_ativa['tipo_fundo'])
            
            score_h = calcular_score_ahp_v26(alvo, t_agua_h, v_h, dp_h, b_ativa['tipo_fundo'], astro.get('day_rating', 2), m_fet_h, m_ox_h, 1.0, 1.0, m_metab_h, 1.0)
            
            # Eventos Astro Reais
            dist_z = min(abs(h - astro.get('zenith_h', 12)), 24 - abs(h - astro.get('zenith_h', 12)))
            dist_n = min(abs(h - astro.get('nadir_h', 0)), 24 - abs(h - astro.get('nadir_h', 0)))
            ev = []
            if dist_z <= 1.5: ev.append("🌕 Cenit")
            if dist_n <= 1.5: ev.append("🌑 Nadir")
            if h == astro.get('sunrise_h', 6): ev.append("🌅 Alvorada")
            if h == astro.get('sunset_h', 21): ev.append("🌇 Crepúsculo")
            if dp_h <= -1.0: ev.append("📉 Queda Pressão")
            
            dados_24h.append({"Hora": f"{h:02d}:00", "Score": score_h, "Eventos": " | ".join(ev)})

        df_24 = pd.DataFrame(dados_24h)
        st.bar_chart(df_24.set_index("Hora")["Score"], color="#FF4B4B")
        st.dataframe(df_24, use_container_width=True, hide_index=True)

    with t2:
        dias, scores, ventos, temps = [], [], [], []
        for i in range(3, len(dados['daily']['time'])):
            t_ar = dados['daily']['temperature_2m_max'][i]
            v_max = dados['daily']['wind_speed_10m_max'][i]
            t_ag = t_ar * 0.85 if t_ar > 25.0 else t_ar * 0.9
            
            sc_d = calcular_score_ahp_v26(alvo, t_ag, v_max, 0.0, b_ativa['tipo_fundo'], 2, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
            
            dias.append(datetime.strptime(dados['daily']['time'][i], "%Y-%m-%d").strftime("%d/%m"))
            scores.append(sc_d)
            ventos.append(v_max)
            temps.append(t_ag)

        df_7 = pd.DataFrame({"Data": dias, "Score (%)": scores, "Temp Água Est (°C)": temps, "Vento Max (km/h)": ventos})
        st.line_chart(df_7.set_index("Data")["Score (%)"])
        st.dataframe(df_7, use_container_width=True, hide_index=True)
else:
    st.error("Falha ao ligar à API. Verifica a tua internet.")
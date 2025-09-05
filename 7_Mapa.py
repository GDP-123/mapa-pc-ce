import base64
import json
import pandas as pd
import qrcode
import re
import requests
import streamlit as st
import streamlit.components.v1 as components
import zlib
       
from streamlit import dialog
from streamlit.runtime.scriptrunner import get_script_run_ctx
from io import BytesIO


# ===============================
# Configurações
# ===============================
st.set_page_config(layout="wide", initial_sidebar_state='collapsed', page_icon= '🦎')
#st.title("🗺️ Mapa PC-CE - Google Maps")

# CSS para botões quadrados
st.markdown("""
<style>
    .stButton > button {
        border-radius: 5px;
        height: 30px;
        width: 100%;
        font-size: 5px;
    }
    html, body {
        margin: 0;
        padding: 0;
        height: 100%;
    }
</style>
""", unsafe_allow_html=True)

GOOGLE_MAPS_API_KEY = "AIzaSyD06plaNz2fi0Sdj0aDPYWsoaVwRl3PxUU" 
#LINK_BASE = 'https://mapa-pc-ce-app.streamlit.app'
LINK_BASE = 'http://localhost:8501'

# ===============================
# Função Extrator
# ===============================
def extrair_coordenadas_vivo(texto):
    try:
        # Padrões regex para extrair os valores
        padrao_latitude = r'LATITUDE\s+([\d\-\.]+)'
        padrao_longitude = r'LONGITUDE\s+([\d\-\.]+)'
        padrao_azimute = r'AZIMUTE\s+(\d+)'
        
        # Extraindo os valores
        latitude = re.search(padrao_latitude, texto)
        longitude = re.search(padrao_longitude, texto)
        azimute = re.search(padrao_azimute, texto)
        
        # Convertendo para os formatos apropriados
        lat = latitude.group(1) if latitude else None
        lon = longitude.group(1) if longitude else None
        az = azimute.group(1) if azimute else None

        lat_conv = converter_graus_decimal_vivo(lat)
        lon_conv = converter_graus_decimal_vivo(lon)
        
        return lat_conv, lon_conv, az
        
    except Exception as e:
        return None, None, None
    
def converter_graus_decimal_vivo(coord):
    if not coord or pd.isna(coord):
        return None
    
    try:
        # Remove o sinal negativo se existir e processa
        negativo = False
        if coord.startswith('-'):
            negativo = True
            coord = coord[1:]
        
        # Divide os componentes
        partes = coord.split('-')
        if len(partes) == 3:
            graus = float(partes[0])
            minutos = float(partes[1])
            segundos = float(partes[2])
            
            # Calcula decimal
            decimal = graus + (minutos / 60) + (segundos / 3600)
            
            # Aplica sinal negativo se necessário
            if negativo:
                decimal = -decimal
                
            return round(decimal, 6)
        else:
            return float(coord)  # Se já estiver em formato decimal
            
    except:
        return None

# ===============================
# Funções de codificação
# ===============================
def encode_data(data: dict) -> str:
    """Codifica e comprime dados em base64 para URL"""
    json_str = json.dumps(data)
    # Comprimir os dados
    compressed = zlib.compress(json_str.encode(), level=9)
    return base64.urlsafe_b64encode(compressed).decode()

def decode_data(data_str: str) -> dict:
    """Decodifica e descomprime dados de base64"""
    try:
        compressed = base64.urlsafe_b64decode(data_str.encode())
        # Descomprimir os dados
        json_str = zlib.decompress(compressed).decode()
        data = json.loads(json_str)
        
        # Garantir que pontos antigos tenham o campo 'visivel'
        for ponto in data.get("pontos", []):
            if 'visivel' not in ponto:
                ponto['visivel'] = True
                
        return data
    except Exception:
        return {"pontos": []}
    
# Função para validar coordenadas
def validar_coordenada(valor):
    try:
        return float(valor.replace(',', '.'))
    except ValueError:
        return None

# Função auxiliar para atualizar URL e session_state
def atualizar_url_e_session_state(pontos_lista):
    """Atualiza session_state e URL com a lista de pontos"""
    st.session_state.pontos = pontos_lista
    encoded = encode_data({"pontos": pontos_lista})
    st.query_params.clear()
    st.query_params["data"] = encoded
    
# Função para exibir cada ponto com os 3 botões
def exibir_ponto_com_botoes(ponto, index):
    # Criar 3 colunas: 1 para botões compactos, 2 para o nome
    col_botoes, col_nome = st.sidebar.columns([1.2, 3])
    
    with col_botoes:
        # Botões em uma sub-coluna compacta
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Botão Visibilidade
            icone = "👁️" if ponto.get('visivel', True) else "👁️‍🗨️"
            tooltip = "Ocultar" if ponto.get('visivel', True) else "Mostrar"
            if st.button(icone, key=f"visibility_{index}", help=tooltip):
                pontos[index]['visivel'] = not ponto.get('visivel', True)
                atualizar_url_e_session_state(pontos)
                st.rerun()
        
        with col2:
            # Botão Editar
            if st.button("✏️", key=f"edit_{index}", help="Editar"):
                if ponto['tipo'] == 'ponto':
                    editar_ponto(index, ponto['nome'], ponto['lat'], ponto['lng'])
                elif ponto['tipo'] == 'torre':
                    editar_torre(index, ponto['nome'], ponto['lat'], ponto['lng'], 
                               ponto['margem'], ponto['azimute'], ponto['distancia'])
        
        with col3:
            # Botão Excluir
            if st.button("🗑️", key=f"delete_{index}", help="Excluir"):
                pontos.pop(index)
                atualizar_url_e_session_state(pontos)
                st.rerun()
    
    with col_nome:
        # Nome do ponto
        if ponto.get('tipo', "ponto") == 'ponto':
            st.write(f"📍 **{ponto['nome']}**")
        elif ponto.get('tipo', "torre") == 'torre':
            st.write(f"🗼 **{ponto['nome']}**")

# Função para encurtar link
def encurtar_url(url_longa):
    """Encurta URL usando o serviço tinyurl.com"""
    try:
        response = requests.get(f"http://tinyurl.com/api-create.php?url={url_longa}")
        if response.status_code == 200:
            return response.text
        else:
            return url_longa  # Fallback para URL original
    except:
        return url_longa  # Fallback em caso de erro

# Função robusta para capturar a URL base (funciona local e no Cloud)
def get_host_url():
    ctx = get_script_run_ctx()
    if ctx is None:
        return LINK_BASE

    try:
        # Versões novas do Streamlit
        return ctx.request.url_root.rstrip("/")
    except Exception:
        return LINK_BASE

# ===============================
# Pop-ups
# ===============================
# Modal/Dialog para adicionar ponto
@st.dialog("Adicionar Novo Ponto")
def novo_ponto():
    nome_modal = st.text_input("Nome do ponto", key="modal_nome")
    col1, col2 = st.columns(2)
    with col1:
        lat_modal = st.text_input("Latitude", value="-3.731900", key="modal_lat")
    with col2:
        lng_modal = st.text_input("Longitude", value="-38.526700", key="modal_lng")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("✅ Adicionar", use_container_width=True):
            lat = validar_coordenada(lat_modal)
            lng = validar_coordenada(lng_modal)
            if lat is not None and lng is not None and nome_modal:
                pontos.append({
                    "lat": lat,
                    "lng": lng,
                    "nome": nome_modal,
                    "visivel": True,
                    "tipo": "ponto"
                })
                atualizar_url_e_session_state(pontos)
                st.rerun()
            else:
                st.error("Preencha todos os campos corretamente!")
    with col_btn2:
        if st.button("❌ Cancelar", use_container_width=True):
            st.rerun()

@st.dialog("Adicionar Nova Antena")
def novo_antena():
    #st.header("Adicionar Novo Ponto")
    col01, col02 = st.columns(2)
    with col01:
        nome_modal = st.text_input("Nome do ponto", key="modal_nome")
    with col02:
        margem = st.text_input("Margem (graus)", value="120", key="modal_margem")
    col11, col12 = st.columns(2)
    with col11:
        lat_modal = st.text_input("Latitude", value="-3.731900", key="modal_lat")
    with col12:
        lng_modal = st.text_input("Longitude", value="-38.526700", key="modal_lng")
    col21, col22 = st.columns(2)
    with col21:
        azimute = st.text_input("Azimute (graus)", key="modal_azimute")
    with col22:
        distancia = st.text_input("Distância (metros)", key="modal_distancia")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("✅ Adicionar", use_container_width=True):
            lat = validar_coordenada(lat_modal)
            lng = validar_coordenada(lng_modal)
            if lat is not None and lng is not None and nome_modal:
                pontos.append({
                    "lat": lat,
                    "lng": lng,
                    "nome": nome_modal,
                    "visivel": True,
                    "margem": margem,
                    "azimute": azimute,
                    "distancia": distancia,
                    "tipo": "torre"
                })
                atualizar_url_e_session_state(pontos)
                st.rerun()
            else:
                st.error("Preencha todos os campos corretamente!")
    with col_btn2:
        if st.button("❌ Cancelar", use_container_width=True):
            st.rerun()

@st.dialog("Editar Ponto")
def editar_ponto(index,nome_old,lat_old,long_old):
    nome_modal = st.text_input("Nome do ponto", value=nome_old, key="modal_nome")
    col1, col2 = st.columns(2)
    with col1:
        lat_modal = st.text_input("Latitude", value=lat_old, key="modal_lat")
    with col2:
        lng_modal = st.text_input("Longitude", value=long_old, key="modal_lng")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("✅ Atualizar", use_container_width=True):
            lat = validar_coordenada(lat_modal)
            lng = validar_coordenada(lng_modal)
            if lat is not None and lng is not None and nome_modal:
                pontos[index] = {   
                    "lat": lat,
                    "lng": lng,
                    "nome": nome_modal,
                    "visivel": pontos[index].get("visivel", True),  # mantém visibilidade anterior
                    "tipo": "ponto"
                }
                atualizar_url_e_session_state(pontos)
                st.rerun()
            else:
                st.error("Preencha todos os campos corretamente!")
    with col_btn2:
        if st.button("❌ Cancelar", use_container_width=True):
            st.rerun()

@st.dialog("Editar Antena")
def editar_torre(index,nome_old, lat_old, long_old,margem_old, azimute_old, distancia_old):
    col01, col02 = st.columns(2)
    with col01:
        nome_modal = st.text_input("Nome do ponto", value=nome_old, key="modal_nome")
    with col02:
        margem = st.text_input("Margem (graus)", value=margem_old, key="modal_margem")
    col11, col12 = st.columns(2)
    with col11:
        lat_modal = st.text_input("Latitude", value=lat_old, key="modal_lat")
    with col12:
        lng_modal = st.text_input("Longitude", value=long_old, key="modal_lng")
    col21, col22 = st.columns(2)
    with col21:
        azimute = st.text_input("Azimute (graus)", value=azimute_old, key="modal_azimute")
    with col22:
        distancia = st.text_input("Distância (metros)", value=distancia_old, key="modal_distancia")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("✅ Atualizar", use_container_width=True):
            lat = validar_coordenada(lat_modal)
            lng = validar_coordenada(lng_modal)
            if lat is not None and lng is not None and nome_modal:
                pontos[index] = {   
                    "lat": lat,
                    "lng": lng,
                    "nome": nome_modal,
                    "margem": margem,
                    "azimute": azimute,
                    "distancia": distancia,
                    "visivel": pontos[index].get("visivel", True),  # mantém visibilidade anterior
                    "tipo": "torre"
                }
                atualizar_url_e_session_state(pontos)
                st.rerun()
            else:
                st.error("Preencha todos os campos corretamente!")
    with col_btn2:
        if st.button("❌ Cancelar", use_container_width=True):
            st.rerun()

@st.dialog("Importar Extrato")
def importar_extrato():
    # Inicializar a lista de pontos se não existir na sessão
    if "pontos" not in st.session_state:
        st.session_state.pontos = []
    
    # Upload do arquivo
    uploaded_file = st.file_uploader(
        "Selecione um arquivo XLSX",
        type=["xlsx"],
        help="Faça upload de um arquivo Excel (.xlsx)"
    )
    
    # Variável para controlar se o processamento foi concluído
    if 'processamento_concluido' not in st.session_state:
        st.session_state.processamento_concluido = False
    
    if uploaded_file is not None and not st.session_state.processamento_concluido:
        try:
            # Lendo o arquivo Excel
            xls = pd.ExcelFile(uploaded_file)
            
            # Mostrando as abas disponíveis
            sheets = xls.sheet_names
            selected_sheet = st.selectbox(
                "Selecione a aba para análise:",
                sheets,
                key="sheet_select"
            )
            
            # Botão de confirmação para iniciar a leitura
            if st.button("✅ Confirmar e Processar Aba", type="primary"):
                # Lendo a aba selecionada
                df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)

                # Verificando a operadora
                operadora = df.iloc[1, 1] if len(df) > 1 else ""

                # Listas para armazenar os resultados
                latitudes_dec = []
                longitudes_dec = []
                azimutes = []
                data_hora = []
                pontos_importados = 0

                if "VIVO" in operadora:
                    endereco_fim = df.iloc[5:, 17].reset_index(drop=True)
                    data_fim = df.iloc[5:, 6].reset_index(drop=True)
                    hora_fim = df.iloc[5:, 7].reset_index(drop=True)
                                        
                    for i, (texto, v_data, v_hora) in enumerate(zip(endereco_fim,data_fim,hora_fim)):                        
                        if pd.isna(texto):  # Pula valores nulos
                            lat, lon, az, aux = None, None, None, None
                        else:
                            lat, lon, az = extrair_coordenadas_vivo(str(texto))
                            aux = v_data + ' - ' + v_hora
                        
                        latitudes_dec.append(lat)
                        longitudes_dec.append(lon)
                        azimutes.append(az)
                        data_hora.append(aux)
                    
                    # Processar todos os pontos após a extração
                    for i, (lat, lon, az, d_t) in enumerate(zip(latitudes_dec, longitudes_dec, azimutes, data_hora)):
                        #lat_val = validar_coordenada(lat)
                        lat_val = lat
                        #lng_val = validar_coordenada(lon)
                        lng_val = lon
                        az_val = az
                        d_t_val = d_t
                        
                        if lat_val is not None and lng_val is not None and az_val is not None and d_t_val is not None:
                            # Usar nome baseado no índice ou criar um padrão                            
                            st.session_state.pontos.append({
                                "lat": lat_val,
                                "lng": lng_val,
                                "nome": d_t_val,
                                "visivel": True,
                                "margem": 120, 
                                "azimute": az_val,
                                "distancia": 1500,  
                                "tipo": "torre"
                            })
                            pontos_importados += 1
                    
                    # Atualizar URL e session state uma vez, após processar todos os pontos
                    atualizar_url_e_session_state(st.session_state.pontos)
                    
                    # Marcar processamento como concluído
                    st.session_state.processamento_concluido = True
                    
                    # Forçar rerun para fechar o diálogo e atualizar o mapa
                    st.rerun()
                            
                else:
                    st.error("Operadora não reconhecida ou extrato não compatível")
                    st.info("A operadora detectada foi: " + (operadora if operadora else "Não identificada"))

        except Exception as e:
            st.error(f"Erro na leitura do extrato: {str(e)}")
    
    # Se o processamento foi concluído, mostrar mensagem de sucesso e botão para fechar
    elif st.session_state.processamento_concluido:
        st.success("✅ Processamento concluído! Os pontos foram adicionados ao mapa.")
        
        # Mostrar preview dos pontos importados
        pontos_importados = len([p for p in st.session_state.pontos if p['nome'].startswith('Ponto_Extrato_')])
        if pontos_importados > 0:
            with st.expander("📋 Ver pontos importados"):
                pontos_recentes = [p for p in st.session_state.pontos if p['nome'].startswith('Ponto_Extrato_')]
                for i, ponto in enumerate(pontos_recentes[-min(5, len(pontos_recentes)):]):  # Mostrar até 5 pontos
                    st.write(f"**{ponto['nome']}**: {ponto['lat']}, {ponto['lng']}")
        
        # Botão para fechar o diálogo e visualizar no mapa
        if st.button("🗺️ Fechar e Visualizar no Mapa", type="primary"):
            # Limpar estado de processamento
            st.session_state.processamento_concluido = False
            st.rerun()

@st.dialog("Compartilhar")
def compartilhar():
    # Obter query param "data"
    current_data = st.query_params.get("data", "")
    if isinstance(current_data, list) and current_data:
        current_data = current_data[0]

    # Verificar se a URL é muito longa
    if len(current_data) > 1500:  # Limite conservador
        st.warning("⚠️ Muitos pontos para compartilhar via URL.")
        st.warning("⚠️ Considere reduzir o número de pontos visíveis ou usar menos dados.")

    # Construir URL completa
    base_url = get_host_url()
    url_original = f"{base_url}?data={current_data}" if current_data else base_url

    # Encurtar URL (sua função externa)
    url_encurtada = encurtar_url(url_original)

    # Exibir título
    st.write("### 🔗 URL Encurtada")
    # Mostrar URL encurtada
    st.code(url_encurtada, language="text")

    # Exibir URL Completa
    st.write("### 🌐 URL Original")
    with st.expander("Ver URL completa"):
        st.code(url_original, language="text")

    # Gerar QR Code
    st.write("### 📱 QR Code")
    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(url_encurtada)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Converter para imagem
        img_buffer = BytesIO()
        qr_img.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        col1, col2, col3 = st.columns([1,2,1])  # coluna do meio maior
        with col1:
            st.write("")  # vazia
        with col2:
            st.image(img_buffer, width=200)
        with col3:
            st.write("")  # vazia

    except Exception:
        st.warning("Não foi possível gerar o QR Code")

    
    
# ===============================
# Recupera pontos da URL e inicializa session_state
# ===============================
query_params = st.query_params

if "data" in query_params:
    raw = query_params["data"]
    if isinstance(raw, list):
        raw = raw[0]
    pontos_iniciais = decode_data(raw).get("pontos", [])
else:
    pontos_iniciais = []

# Inicializar session_state
if 'pontos' not in st.session_state:
    st.session_state.pontos = pontos_iniciais

if 'show_dialog' not in st.session_state:
    st.session_state.show_dialog = False

# Usar session_state para tudo
pontos = st.session_state.pontos

# ===============================
# Inputs do usuário
# ===============================
#st.sidebar.center.title("Gerenciar Pontos")
st.sidebar.markdown(
    "<h2 style='text-align: center;'>Gerenciar Pontos/Torres</h2>", 
    unsafe_allow_html=True
)

# Adicionando ponto
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("➕ Ponto📍", use_container_width=True, help="Adicionar novo ponto"):
        novo_ponto()

with col2:
    if st.button("➕Antena🗼", use_container_width=True, help="Adicionar nova antena"):
        novo_antena()

if st.sidebar.button("Compartilhar 🔗", use_container_width=True, help="Compartilhar pontos no mapa"):
    compartilhar()

if st.sidebar.button("Importar Extrato 📤", use_container_width=True, help="Importar Extrato no formato XLSX"):
    importar_extrato()

# Limpando pontos
#if st.sidebar.button("🗑️ Limpar pontos"):
#    st.session_state.pontos = []
#    st.query_params.clear()
#    st.rerun()

# Exibir pontos
if pontos:
    for i, ponto in enumerate(pontos):
        exibir_ponto_com_botoes(ponto, i)
else:
    pass
    ##st.sidebar.info("Nenhum ponto cadastrado ainda.")

# ===============================
# HTML + JS do Google Maps (ATUALIZADO)
# ===============================
# Filtrar apenas pontos visíveis
pontos_visiveis = [p for p in pontos if p.get('visivel', True)]
markers_json = json.dumps(pontos_visiveis)

html_code = f"""
<!DOCTYPE html>
<html>
<head>
<script src="https://maps.googleapis.com/maps/api/js?key={GOOGLE_MAPS_API_KEY}"></script>
<script>
// Função para criar ícone da torre (definida uma vez)
function criarIconeTorre() {{
    const svgString = `
        <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 40 40">
            <rect x="15" y="10" width="10" height="20" fill="#0000FF" stroke="#FFFFFF" stroke-width="2"/>
            <circle cx="20" cy="5" r="3" fill="#FF0000"/>
            <rect x="5" y="30" width="30" height="5" fill="#0000FF" stroke="#FFFFFF" stroke-width="1"/>
        </svg>
    `;
    return "data:image/svg+xml;base64," + btoa(svgString);
}}

function initMap() {{
    var pos = {{ lat: -3.7319, lng: -38.5267 }};
    const points = {markers_json};

    // Ajustar o tamanho do container do mapa
    const mapContainer = document.getElementById("map-container");
    mapContainer.style.height = window.innerHeight + 'px';
    
    var map = new google.maps.Map(document.getElementById("map"), {{
        center: pos,
        zoom: 12,
        streetViewControl: true,
        gestureHandling: "greedy"
    }});

    // overlay personalizado
    class LabelOverlay extends google.maps.OverlayView {{
        constructor(position, text) {{
            super();
            this.position = position;
            this.text = text;
            this.div = null;
        }}
        onAdd() {{
            this.div = document.createElement("div");
            this.div.style.position = "absolute";
            this.div.style.background = "white";
            this.div.style.border = "1px solid black";
            this.div.style.padding = "2px 4px";
            this.div.style.borderRadius = "4px";
            this.div.style.fontSize = "14px";
            this.div.style.fontWeight = "bold";
            this.div.innerText = this.text;
            const panes = this.getPanes();
            panes.overlayImage.appendChild(this.div);
        }}
        draw() {{
            const overlayProjection = this.getProjection();
            const posPixel = overlayProjection.fromLatLngToDivPixel(this.position);
            if(this.div){{
                this.div.style.left = posPixel.x - (this.div.offsetWidth / 2) + "px";
                this.div.style.top = posPixel.y - 60 + "px";
            }}
        }}
        onRemove() {{
            if(this.div){{
                this.div.parentNode.removeChild(this.div);
                this.div = null;
            }}
        }}
    }}

    function metersToLatLng(m, lat) {{
        const earthRadius = 6378137;
        const dLat = m / earthRadius * (180 / Math.PI);
        const dLng = m / (earthRadius * Math.cos(Math.PI * lat / 180)) * (180 / Math.PI);
        return {{ dLat, dLng }};
    }}

    function desenharSetorTorre(p, map) {{
        const center = {{ lat: p.lat, lng: p.lng }};
        const radius = p.distancia;
        const azimute = p.azimute;
        const margem = p.margem;
        const {{ dLat, dLng }} = metersToLatLng(radius, p.lat);

        // Calcular ângulos inicial e final
        const startAngle = azimute - margem/2;
        const endAngle = azimute + margem/2;
        
        // Calcular número ótimo de pontos (1 ponto a cada 2 graus, mínimo 10 pontos)
        const numPontos = Math.max(10, Math.ceil(margem / 2));
        const step = margem / numPontos;

        // Criar array de pontos para o setor
        const sectorPoints = [];
        
        // Ponto central
        sectorPoints.push(center);

        // Pontos ao longo do arco externo
        for (let i = 0; i <= numPontos; i++) {{
            const angle = startAngle + (i * step);
            const rad = angle * Math.PI / 180;
            sectorPoints.push({{
                lat: p.lat + dLat * Math.cos(rad),
                lng: p.lng + dLng * Math.sin(rad)
            }});
        }}

        // Fechar o polígono voltando ao centro
        sectorPoints.push(center);

        // Criar polígono do setor
        const sectorPolygon = new google.maps.Polygon({{
            paths: sectorPoints,
            strokeColor: "#0000FF",
            strokeOpacity: 0.5,
            strokeWeight: 1,
            fillColor: "#0000FF",
            fillOpacity: 0.35,
            map: map
        }});

        // Desenhar linha do azimute central
        const azRad = azimute * Math.PI / 180;
        const azPoint = {{
            lat: p.lat + dLat * Math.cos(azRad),
            lng: p.lng + dLng * Math.sin(azRad)
        }};
        
        new google.maps.Polyline({{
            path: [center, azPoint],
            strokeColor: "#FF0000",
            strokeOpacity: 0.5,
            strokeWeight: 1,
            map: map
        }});

        // Desenhar marcador de torre no centro
        new google.maps.Marker({{
            position: center,
            map: map,
            icon: {{
                url: "https://cdn-icons-png.flaticon.com/512/74/74024.png",
                scaledSize: new google.maps.Size(32, 32),
                anchor: new google.maps.Point(16, 32)
            }}
        }});

        // Adicionar label
        const label = new LabelOverlay(center, p.nome + "");
        label.setMap(map);

        return sectorPolygon;
    }}

    // --- Desenhar todos os pontos ---
    points.forEach(p => {{
        const markerPos = new google.maps.LatLng(p.lat, p.lng);

        if (p.tipo === "ponto") {{
            // Marcador normal para pontos
            new google.maps.Marker({{
                position: markerPos,
                map: map,
                icon: {{
                    url: "https://maps.google.com/mapfiles/ms/icons/red-dot.png",
                    scaledSize: new google.maps.Size(24, 24)
                }}
            }});
            
            const label = new LabelOverlay(markerPos, p.nome);
            label.setMap(map);

        }} else if (p.tipo === "torre") {{
            // Setor para torres
            desenharSetorTorre(p, map);
        }}
    }});

    // Centralizar no primeiro ponto se existir
    if(points.length > 0) {{
        const primeiroPonto = points[0];
        map.setCenter({{ lat: primeiroPonto.lat, lng: primeiroPonto.lng }});
        
        // Ajustar zoom baseado no tipo do primeiro ponto
        if (primeiroPonto.tipo === "torre") {{
            const zoomLevel = Math.max(10, 16 - Math.log2(primeiroPonto.distancia / 1000));
            map.setZoom(Math.min(18, Math.max(8, zoomLevel)));
        }} else {{
            map.setZoom(14);
        }}
    }}
}}

// Função para ajustar o tamanho do mapa quando a janela for redimensionada
function ajustarTamanhoMapa() {{
    const mapContainer = document.getElementById("map-container");
    const mapElement = document.getElementById("map");
    
    if (mapContainer && mapElement) {{
        mapContainer.style.height = window.innerHeight + 'px';
        mapElement.style.height = window.innerHeight + 'px';
        
        // Re-center map if it exists
        if (window.map) {{
            google.maps.event.trigger(window.map, 'resize');
        }}
    }}
}}

// Inicializar quando a página carregar
window.addEventListener('load', function() {{
    initMap();
    ajustarTamanhoMapa();
}});

// Ajustar quando a janela for redimensionada
window.addEventListener('resize', function() {{
    ajustarTamanhoMapa();
}});
</script>
</head>
<body style="margin: 0; padding: 0; height: 100vh; overflow: hidden;">
<div id="map-container" style="width: 100%; height: 100vh;">
    <div id="map" style="height: 100%; width: 100%;"></div>
</div>
</body>
</html>
"""

# Use uma altura grande para garantir que o JavaScript faça o ajuste correto
components.html(html_code, height=800, scrolling=False)

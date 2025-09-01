import streamlit as st
import streamlit.components.v1 as components
import base64
import json
import requests

from streamlit import dialog
from streamlit.runtime.scriptrunner import get_script_run_ctx


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
        height: 40px;
        width: 100%;
        font-size: 16px;
    }
    html, body {
        margin: 0;
        padding: 0;
        height: 100%;
    }
</style>
""", unsafe_allow_html=True)

GOOGLE_MAPS_API_KEY = "AIzaSyD06plaNz2fi0Sdj0aDPYWsoaVwRl3PxUU" 

# ===============================
# Funções de codificação
# ===============================
def encode_data(data: dict) -> str:
    """Codifica dados em base64 para URL"""
    json_str = json.dumps(data)
    return base64.urlsafe_b64encode(json_str.encode()).decode()

def decode_data(data_str: str) -> dict:
    """Decodifica dados de base64"""
    try:
        json_str = base64.urlsafe_b64decode(data_str.encode()).decode()
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
    if ponto.get('tipo', "ponto") == 'ponto':
        st.sidebar.write(f"📍 **{ponto['nome']}**")
    elif ponto.get('tipo', "torre") == 'torre':
        st.sidebar.write(f"🗼 **{ponto['nome']}**")
        
    # Criar 3 colunas para os botões quadrados
    coll1, coll2, coll3 = st.sidebar.columns(3)
    
    with coll1:
        # Botão 1 - Toggle visibilidade (👁️/👁️‍🗨️)
        icone = "👁️" if ponto.get('visivel', True) else "👁️‍🗨️"
        tooltip = "Ocultar" if ponto.get('visivel', True) else "Mostrar ponto"
        if st.button(icone, key=f"visibility_{index}", use_container_width=True, help=tooltip):
            # Alternar visibilidade
            pontos[index]['visivel'] = not ponto.get('visivel', True)
            # Atualizar session_state e URL
            atualizar_url_e_session_state(pontos)
            st.rerun()
    
    with coll2:
        # Botão 2 - Editar (✏️)
        tooltip = "Editar"
        if st.button("✏️", key=f"edit_{index}", use_container_width=True,help=tooltip):
            if ponto['tipo']=='ponto':
                editar_ponto(index,ponto['nome'],ponto['lat'],ponto['lng'])
            elif ponto['tipo']=='torre':
                editar_torre(index,ponto['nome'],ponto['lat'],ponto['lng'],ponto['margem'],ponto['azimute'], ponto['distancia'])
    
    with coll3:
        # Botão 3 - Excluir (🗑️)
        tooltip = "Excluir"
        if st.button("🗑️", key=f"delete_{index}", use_container_width=True,help=tooltip):
            # Remover ponto da lista
            pontos.pop(index)
            # Atualizar session_state e URL
            atualizar_url_e_session_state(pontos)
            st.rerun()

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
        return "https://mapa-pc-ce-app.streamlit.app"
        #return "http://localhost:8501"  # fallback padrão

    try:
        # Versões novas do Streamlit
        return ctx.request.url_root.rstrip("/")
    except Exception:
        return "https://mapa-pc-ce-app.streamlit.app"
        #return "http://localhost:8501"


# ===============================
# Pop-ups
# ===============================
# Modal/Dialog para adicionar ponto
@st.dialog("Adicionar Novo Ponto")
def novo_ponto():
    #st.header("Adicionar Novo Ponto")
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

@st.dialog("Compartilhar")
def compartilhar():
    # Obter query param "data"
    current_data = st.query_params.get("data", "")
    if isinstance(current_data, list) and current_data:
        current_data = current_data[0]

    # Construir URL completa
    base_url = get_host_url()
    url_original = f"{base_url}?data={current_data}" if current_data else base_url

    # Encurtar URL (sua função externa)
    url_encurtada = encurtar_url(url_original)

    # Exibir título
    st.write("### 🔗 Link para Compartilhar")

    # Mostrar URL encurtada
    st.code(url_encurtada, language="text")

    # Botão para copiar URL encurtada
    if st.button("📋 Copiar URL Encurtada", use_container_width=True):
        st.session_state.copied = True
        js_code = f"""
        <script>
        navigator.clipboard.writeText("{url_encurtada}");
        </script>
        """
        components.html(js_code, height=0)

    if st.session_state.get("copied", False):
        st.success("✅ URL copiada para a área de transferência!")
        st.session_state.copied = False

    st.write("---")
    st.write("### 📱 QR Code")

    # Gerar QR Code
    try:
        import qrcode
        from io import BytesIO

        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(url_encurtada)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Converter para imagem
        img_buffer = BytesIO()
        qr_img.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        st.image(img_buffer, width=200)

    except Exception:
        st.warning("Não foi possível gerar o QR Code")
        st.info("Instale: `pip install qrcode[pil]`")

    st.write("---")
    st.write("### 🌐 URL Original")
    with st.expander("Ver URL completa"):
        st.code(url_original, language="text")
    
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
st.sidebar.title("Gerenciar Pontos")

# Adicionando ponto
if st.sidebar.button("➕ Adicionar Ponto 📍"):
    novo_ponto()

# Adicionando Antena
if st.sidebar.button("➕ Adicionar Antena 🗼"):
    novo_antena()

# Compartilhar
if st.sidebar.button("Compartilhar"):
    compartilhar()

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

import streamlit as st
import streamlit.components.v1 as components
import base64
import json

from streamlit import dialog as st_dialog


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
    st.sidebar.write(f"📍 **{ponto['nome']}**")
    
    # Criar 3 colunas para os botões quadrados
    coll1, coll2, coll3 = st.sidebar.columns(3)
    
    with coll1:
        # Botão 1 - Toggle visibilidade (👁️/👁️‍🗨️)
        icone = "👁️" if ponto.get('visivel', True) else "👁️‍🗨️"
        tooltip = "Ocultar ponto" if ponto.get('visivel', True) else "Mostrar ponto"
        
        if st.button(icone, key=f"visibility_{index}", use_container_width=True, help=tooltip):
            # Alternar visibilidade
            pontos[index]['visivel'] = not ponto.get('visivel', True)
            # Atualizar session_state e URL
            atualizar_url_e_session_state(pontos)
            st.rerun()
    
    with coll2:
        # Botão 2 - Editar (✏️)
        if st.button("✏️", key=f"edit_{index}", use_container_width=True):
            editar_ponto(index,ponto['nome'],ponto['lat'],ponto['lng'])
    
    with coll3:
        # Botão 3 - Excluir (🗑️)
        if st.button("🗑️", key=f"delete_{index}", use_container_width=True):
            # Remover ponto da lista
            pontos.pop(index)
            # Atualizar session_state e URL
            atualizar_url_e_session_state(pontos)
            st.rerun()

# ===============================
# Pop-ups
# ===============================
# Modal/Dialog para adicionar ponto
@st.dialog("Adicionar Novo Ponto")
def abrir_dialogo():
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
                    "visivel": True
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
                    "visivel": pontos[index].get("visivel", True)  # mantém visibilidade anterior
                }
                atualizar_url_e_session_state(pontos)
                st.rerun()
            else:
                st.error("Preencha todos os campos corretamente!")
    with col_btn2:
        if st.button("❌ Cancelar", use_container_width=True):
            st.rerun()


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
if st.sidebar.button("➕ Adicionar ponto"):
    abrir_dialogo()

# Limpando pontos
if st.sidebar.button("🗑️ Limpar pontos"):
    st.session_state.pontos = []
    st.query_params.clear()
    st.rerun()

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
      function initMap() {{
        // centraliza no primeiro ponto ou em Fortaleza se nenhum ponto
        var pos = {{"lat": -3.7319, "lng": -38.5267}};
        const points = {markers_json};
        if(points.length > 0) {{
            pos = {{ lat: points[0].lat, lng: points[0].lng }};
        }}

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

        // desenha apenas os pontos visíveis
        points.forEach(p => {{
          const markerPos = new google.maps.LatLng(p.lat, p.lng);
          new google.maps.Marker({{ position: markerPos, map: map }});
          const label = new LabelOverlay(markerPos, p.nome);
          label.setMap(map);
        }});
      }}
    </script>
  </head>
  <body onload="initMap()">
    <div id="map" style="height:600px; width:100%;"></div>
  </body>
</html>
"""

components.html(html_code, height=700)

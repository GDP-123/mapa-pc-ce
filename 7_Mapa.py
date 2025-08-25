import streamlit as st
import sqlite3
import uuid

# ===============================
# Funções auxiliares para persistência
# ===============================
def init_db():
    conn = sqlite3.connect("pontos.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pontos (
            map_id TEXT,
            nome TEXT,
            lat REAL,
            lng REAL
        )
    """)
    conn.commit()
    conn.close()

def salvar_pontos(map_id, pontos):
    conn = sqlite3.connect("pontos.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM pontos WHERE map_id=?", (map_id,))
    for p in pontos:
        cur.execute("INSERT INTO pontos VALUES (?, ?, ?, ?)", (map_id, p["nome"], p["lat"], p["lng"]))
    conn.commit()
    conn.close()

def carregar_pontos(map_id):
    conn = sqlite3.connect("pontos.db")
    cur = conn.cursor()
    cur.execute("SELECT nome, lat, lng FROM pontos WHERE map_id=?", (map_id,))
    rows = cur.fetchall()
    conn.close()
    return [{"nome": r[0], "lat": r[1], "lng": r[2]} for r in rows]

# ===============================
# App
# ===============================
st.set_page_config(page_title="Mapa", layout="wide")
init_db()

# Pega map_id da URL
params = st.query_params
map_id = params.get("map_id", [None])[0]

# Se não existir, cria um novo
if not map_id:
    map_id = str(uuid.uuid4())
    st.query_params["map_id"] = map_id

st.write(f"🗺️ Link compartilhável: {st.get_option('server.baseUrlPath')}/?map_id={map_id}")

# Carregar pontos salvos
pontos = carregar_pontos(map_id)

# Sidebar de gerenciamento
st.sidebar.title("Gerenciar Pontos")
nome = st.sidebar.text_input("Nome do ponto")
lat = st.sidebar.number_input("Latitude", format="%.6f")
lng = st.sidebar.number_input("Longitude", format="%.6f")

if st.sidebar.button("Adicionar ponto"):
    pontos.append({"nome": nome, "lat": lat, "lng": lng})
    salvar_pontos(map_id, pontos)

if pontos:
    st.sidebar.subheader("Pontos existentes")
    for i, p in enumerate(pontos):
        if st.sidebar.button(f"Excluir {p['nome']}", key=f"del_{i}"):
            pontos.pop(i)
            salvar_pontos(map_id, pontos)
            st.rerun()

# Renderizar mapa (HTML igual ao que você já tem)
# (aqui só coloca o loop para adicionar os pontos)

html_markers = ""
for p in pontos:
    html_markers += f"""
    var marker = new google.maps.Marker({{
        position: {{ lat: {p['lat']}, lng: {p['lng']} }},
        map: map
    }});
    var label = new LabelOverlay(new google.maps.LatLng({p['lat']}, {p['lng']}), "{p['nome']}");
    label.setMap(map);
    """

html_code = f"""
<!DOCTYPE html>
<html>
  <head>
    <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyD06plaNz2fi0Sdj0aDPYWsoaVwRl3PxUU"></script>
    <script>
      function initMap() {{
        var pos = {{ lat: -3.7824, lng: -38.5745 }};
        var map = new google.maps.Map(document.getElementById("map"), {{
          center: pos,
          zoom: 12,
          gestureHandling: "greedy"
        }});

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
            if (this.div) {{
              this.div.style.left = posPixel.x - (this.div.offsetWidth / 2) + "px";
              this.div.style.top = posPixel.y - 40 + "px";
            }}
          }}
          onRemove() {{
            if (this.div) {{
              this.div.parentNode.removeChild(this.div);
              this.div = null;
            }}
          }}
        }}

        // Adiciona pontos
        {html_markers}
      }}
    </script>
  </head>
  <body onload="initMap()">
    <div id="map" style="height:500px; width:100%;"></div>
  </body>
</html>
"""

st.components.v1.html(html_code, height=600, width=800)

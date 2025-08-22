import streamlit as st

st.set_page_config(page_title="Mapa", layout="wide")
st.title("Mapa PC-CE")

# Inicializa sessão para armazenar pontos
if "pontos" not in st.session_state:
    # cada ponto é um dict: {"nome": str, "lat": float, "lng": float}
    st.session_state.pontos = []

# MENU LATERAL
menu = st.sidebar.selectbox("Gerenciar Pontos", ["Visualizar", "Adicionar", "Alterar", "Deletar"])

if menu == "Adicionar":
    nome = st.text_input("Nome do ponto", "Novo ponto")
    lat = st.number_input("Latitude", value=-3.7824, format="%.6f")
    lng = st.number_input("Longitude", value=-38.5745, format="%.6f")
    if st.button("Adicionar ponto"):
        st.session_state.pontos.append({"nome": nome, "lat": lat, "lng": lng})
        st.success(f"Ponto '{nome}' adicionado!")

elif menu == "Alterar":
    if st.session_state.pontos:
        nomes = [p["nome"] for p in st.session_state.pontos]
        selecionado = st.selectbox("Selecione o ponto para alterar", nomes)
        ponto = next(p for p in st.session_state.pontos if p["nome"] == selecionado)
        novo_nome = st.text_input("Novo nome", ponto["nome"])
        nova_lat = st.number_input("Nova latitude", value=ponto["lat"])
        nova_lng = st.number_input("Nova longitude", value=ponto["lng"])
        if st.button("Atualizar ponto"):
            ponto.update({"nome": novo_nome, "lat": nova_lat, "lng": nova_lng})
            st.success(f"Ponto '{novo_nome}' atualizado!")
    else:
        st.info("Nenhum ponto cadastrado.")

elif menu == "Deletar":
    if st.session_state.pontos:
        nomes = [p["nome"] for p in st.session_state.pontos]
        selecionado = st.selectbox("Selecione o ponto para deletar", nomes)
        if st.button("Deletar ponto"):
            st.session_state.pontos = [p for p in st.session_state.pontos if p["nome"] != selecionado]
            st.success(f"Ponto '{selecionado}' deletado!")
    else:
        st.info("Nenhum ponto cadastrado.")

# ========================
# MAPA COM TODOS OS PONTOS
# ========================
# Gera o HTML para o mapa
pontos_js = ",\n".join(
    f'{{lat: {p["lat"]}, lng: {p["lng"]}, nome: "{p["nome"]}"}}' for p in st.session_state.pontos
)

html_code = f"""
<!DOCTYPE html>
<html>
  <head>
    <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyD06plaNz2fi0Sdj0aDPYWsoaVwRl3PxUU"></script>
    <script>
      function initMap() {{
        var map = new google.maps.Map(document.getElementById("map"), {{
          center: {{lat: -3.7824, lng: -38.5745}},
          zoom: 12,
          streetViewControl: true,
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
              this.div.style.top = posPixel.y - 60 + "px";
            }}
          }}
          onRemove() {{
            if (this.div) {{
              this.div.parentNode.removeChild(this.div);
              this.div = null;
            }}
          }}
        }}

        // Adiciona todos os pontos do session_state
        const pontos = [{pontos_js}];
        pontos.forEach(p => {{
          const marker = new google.maps.Marker({{position: {{lat: p.lat, lng: p.lng}}, map: map}});
          const label = new LabelOverlay(new google.maps.LatLng(p.lat, p.lng), p.nome);
          label.setMap(map);
        }});
      }}
    </script>
  </head>
  <body onload="initMap()">
    <div id="map" style="height:500px; width:100%;"></div>
  </body>
</html>
"""

st.components.v1.html(html_code, height=600, width=800)

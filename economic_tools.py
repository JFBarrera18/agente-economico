#######################
# Agente Economico    #
# Herramientas        #
#######################

import requests


# Indicadores del Banco Mundial disponibles (nombre amigable -> codigo oficial)
INDICADORES_BM = {
    "inflacion": "FP.CPI.TOTL.ZG",          # Inflacion, precios al consumidor (% anual)
    "pib": "NY.GDP.MKTP.CD",                 # PIB (US$ a precios actuales)
    "crecimiento_pib": "NY.GDP.MKTP.KD.ZG",  # Crecimiento del PIB (% anual)
    "desempleo": "SL.UEM.TOTL.ZS",           # Desempleo (% de la poblacion activa)
    "remesas": "BX.TRF.PWKR.DT.GD.ZS",       # Remesas recibidas (% del PIB)
}


class EconomicTools:

    def __init__(self):
        pass

    # Herramienta 1: tipo de cambio (ExchangeRate-API)
    def consultar_tipo_cambio_api(self, moneda: str, moneda_destino: str = "GTQ"):
        print(f"Herramienta consultar_tipo_cambio_api llamada con moneda: {moneda}, destino: {moneda_destino}")

        if not moneda:
            return "Error: Se requiere el codigo de la moneda."

        url = f"https://open.er-api.com/v6/latest/{moneda.upper()}"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            tasa = data.get("rates", {}).get(moneda_destino.upper())
            if tasa is None:
                return f"ERROR: No se encontro el tipo de cambio de {moneda} a {moneda_destino}"
            return {
                "moneda_origen": moneda.upper(),
                "moneda_destino": moneda_destino.upper(),
                "tipo_cambio": tasa,
                "fecha_actualizacion": data.get("time_last_update_utc"),
            }
        except Exception as e:
            print(f"Error en consultar_tipo_cambio_api: {e}")
            return f"ERROR: No se pudo obtener el tipo de cambio para {moneda}"

    # Herramienta 2: indicadores macroeconomicos (Banco Mundial)
    def consultar_indicador_banco_mundial(self, pais: str, indicador: str):
        print(f"Herramienta consultar_indicador_banco_mundial llamada con pais: {pais}, indicador: {indicador}")

        codigo = INDICADORES_BM.get(indicador)
        if not pais or not codigo:
            return f"Error: Se requiere un pais y un indicador valido: {list(INDICADORES_BM.keys())}"

        # mrnev=5 trae los 5 datos mas recientes que no esten vacios
        url = (
            f"https://api.worldbank.org/v2/country/{pais}/indicator/{codigo}"
            f"?format=json&mrnev=5"
        )

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            if len(data) < 2 or not data[1]:
                return f"ERROR: No hay datos del indicador {indicador} para {pais}"
            return {
                "pais": data[1][0]["country"]["value"],
                "indicador": data[1][0]["indicator"]["value"],
                "valores": [{"anio": d["date"], "valor": d["value"]} for d in data[1]],
            }
        except Exception as e:
            print(f"Error en consultar_indicador_banco_mundial: {e}")
            return f"ERROR: No se pudo obtener el indicador {indicador} para {pais}"

    # Herramienta 3: precio de criptomonedas (CoinGecko)
    def consultar_precio_cripto(self, cripto: str):
        print(f"Herramienta consultar_precio_cripto llamada con cripto: {cripto}")

        if not cripto:
            return "Error: Se requiere el nombre de la criptomoneda."

        url = (
            f"https://api.coingecko.com/api/v3/simple/price"
            f"?ids={cripto.lower()}&vs_currencies=usd&include_24hr_change=true"
        )

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            if not data:
                return f"ERROR: No se encontro la criptomoneda {cripto}"
            return data
        except Exception as e:
            print(f"Error en consultar_precio_cripto: {e}")
            return f"ERROR: No se pudo obtener el precio de {cripto}"

    # Herramienta 4: perfil economico de un pais (Banco Mundial)
    def consultar_info_pais(self, pais: str):
        print(f"Herramienta consultar_info_pais llamada con pais: {pais}")

        import unicodedata

        def normalizar(texto):
            texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
            return texto.lower().strip()

        if not pais:
            return "Error: Se requiere el nombre o codigo del pais."

        try:
            codigo = pais.strip().upper()

            # Si no es un codigo ISO (2 o 3 letras), se busca el pais por nombre
            if not (len(codigo) in (2, 3) and codigo.isalpha()):
                lista = requests.get(
                    "https://api.worldbank.org/v2/country?format=json&per_page=400",
                    timeout=30
                ).json()[1]
                codigo = None
                for c in lista:
                    if normalizar(c["name"]) == normalizar(pais):
                        codigo = c["id"]
                        break
                if codigo is None:
                    return (f"ERROR: No se encontro el pais {pais}. "
                            f"Intenta de nuevo enviando su codigo ISO de 3 letras (por ejemplo COL).")

            # Perfil del pais
            response = requests.get(
                f"https://api.worldbank.org/v2/country/{codigo}?format=json", timeout=30
            )
            response.raise_for_status()
            data = response.json()
            if len(data) < 2 or not data[1]:
                return f"ERROR: No hay informacion para el pais {pais}"
            info = data[1][0]

            # Poblacion mas reciente disponible
            pob = requests.get(
                f"https://api.worldbank.org/v2/country/{codigo}/indicator/SP.POP.TOTL?format=json&mrnev=1",
                timeout=30
            ).json()
            poblacion = None
            if len(pob) > 1 and pob[1]:
                poblacion = {"anio": pob[1][0]["date"], "habitantes": pob[1][0]["value"]}

            return {
                "pais": info["name"],
                "codigo_iso3": info["id"],
                "codigo_iso2": info["iso2Code"],
                "capital": info["capitalCity"],
                "region": info["region"]["value"].strip(),
                "nivel_de_ingreso": info["incomeLevel"]["value"],
                "poblacion": poblacion,
            }
        except Exception as e:
            print(f"Error en consultar_info_pais: {e}")
            return f"ERROR: No se pudo obtener informacion del pais {pais}"
        
    # Herramienta 5: feriados oficiales (Nager.Date)
    def consultar_feriados(self, codigo_pais: str, anio: int):
        print(f"Herramienta consultar_feriados llamada con pais: {codigo_pais}, anio: {anio}")

        if not codigo_pais or not anio:
            return "Error: Se requiere el codigo del pais y el anio."

        url = f"https://date.nager.at/api/v3/PublicHolidays/{anio}/{codigo_pais.upper()}"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            return [{"fecha": d["date"], "feriado": d["localName"]} for d in data]
        except Exception as e:
            print(f"Error en consultar_feriados: {e}")
            return f"ERROR: No se pudieron obtener los feriados de {codigo_pais} en {anio}"
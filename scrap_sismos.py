import requests
from bs4 import BeautifulSoup
import boto3
import uuid
import json

# Página del IGP con los últimos sismos reportados
URL = "https://ultimosismo.igp.gob.pe/productos/reportes-sismicos"


def extraer_desde_tabla(soup):
    """Mismo método usado en clase para la web de Bomberos: buscar un <table> en el HTML."""
    table = soup.find('table')
    if not table:
        return []

    encabezados = [th.text.strip() for th in table.find_all('th')]
    filas = []
    for row in table.find_all('tr')[1:]:  # se omite el encabezado
        celdas = row.find_all('td')
        if not celdas:
            continue
        fila = {}
        for i, celda in enumerate(celdas):
            nombre_col = encabezados[i] if i < len(encabezados) else f'col_{i}'
            fila[nombre_col] = celda.text.strip()
        filas.append(fila)
    return filas


def extraer_desde_json_embebido(soup):
    """
    Muchas webs modernas (como esta del IGP) no traen la tabla en el HTML, sino que
    cargan los datos con JavaScript. Varias de ellas (Next.js) dejan los datos ya
    listos dentro de un <script id="__NEXT_DATA__"> en formato JSON.
    Si esto no aplica a tu caso, revisa con el navegador (F12 -> Network) cuál es
    el request que trae los sismos y ajusta esta función para llamarlo con requests.
    """
    script_tag = soup.find('script', id='__NEXT_DATA__')
    if not script_tag or not script_tag.string:
        return []

    try:
        data = json.loads(script_tag.string)
    except json.JSONDecodeError:
        return []

    # Ruta típica de Next.js. Si la estructura real es distinta, imprime "data"
    # (por ejemplo devolviéndolo en el body) para ubicar dónde están los sismos.
    page_props = data.get('props', {}).get('pageProps', {})
    for clave in ('sismos', 'reportes', 'data', 'items', 'results'):
        if clave in page_props and isinstance(page_props[clave], list):
            return page_props[clave]
    return []


def lambda_handler(event, context):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36'
    }

    response = requests.get(URL, headers=headers, timeout=15)
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'body': 'Error al acceder a la página web del IGP'
        }

    soup = BeautifulSoup(response.content, 'html.parser')

    # 1) Intento con el mismo método de clase (tabla HTML)
    sismos = extraer_desde_tabla(soup)

    # 2) Si no hay tabla, intento leer el JSON embebido de la página
    if not sismos:
        sismos = extraer_desde_json_embebido(soup)

    if not sismos:
        return {
            'statusCode': 404,
            'body': 'No se encontró información de sismos en la página. '
                    'Revise con el navegador (F12 > Elements/Network) la estructura '
                    'real de la página y ajuste la función de extracción.'
        }

    # Nos quedamos solo con los 10 últimos sismos reportados
    sismos = sismos[:10]

    # Guardar en DynamoDB (igual que en el ejemplo de clase)
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('TablaSismosIGP')

    # Eliminar los registros anteriores antes de insertar los nuevos
    scan = table.scan()
    with table.batch_writer() as batch:
        for each in scan['Items']:
            batch.delete_item(Key={'id': each['id']})

    # Insertar los nuevos sismos
    i = 1
    for sismo in sismos:
        sismo['#'] = i
        sismo['id'] = str(uuid.uuid4())
        table.put_item(Item=sismo)
        i += 1

    return {
        'statusCode': 200,
        'body': json.dumps(sismos, ensure_ascii=False)
    }

import requests
import boto3
import uuid
import json
from datetime import datetime

# API que usa internamente la página del IGP para mostrar la tabla de sismos
# (se encontró revisando la pestaña Network del navegador: la página carga
# https://ultimosismo.igp.gob.pe/api/ultimo-sismo/ajaxb/<anio> con JavaScript,
# por eso un scraping directo del HTML no funcionaba).
URL = "https://ultimosismo.igp.gob.pe/api/ultimo-sismo/ajaxb/{anio}"


def lambda_handler(event, context):
    anio = datetime.now().year

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36'
    }

    response = requests.get(URL.format(anio=anio), headers=headers, timeout=15)
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'body': 'Error al acceder a la API del IGP'
        }

    # La API devuelve una lista con TODOS los sismos del año, ordenada del
    # más antiguo (codigo 0001) al más reciente.
    data = response.json()

    if not data:
        return {
            'statusCode': 404,
            'body': 'No se encontraron sismos para el año actual'
        }

    # Los 10 últimos son los últimos elementos del arreglo
    ultimos_10 = data[-10:]
    ultimos_10.reverse()  # para que el más reciente quede primero

    sismos = []
    for s in ultimos_10:
        sismos.append({
            'codigo': s.get('codigo'),
            'fecha': (s.get('fecha_local') or '')[:10],      # YYYY-MM-DD
            'hora': (s.get('hora_local') or '')[11:19],       # HH:MM:SS
            'magnitud': s.get('magnitud'),
            'profundidad': s.get('profundidad'),
            'latitud': s.get('latitud'),
            'longitud': s.get('longitud'),
            'referencia': s.get('referencia'),
            'intensidad': s.get('intensidad'),
        })

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

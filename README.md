# api-web-scraping-sismos

Ejercicio 2 (Taller 2 - CS2032): API serverless que hace web scraping de los 10 últimos
sismos reportados por el IGP (https://ultimosismo.igp.gob.pe/productos/reportes-sismicos)
y los guarda en una tabla DynamoDB.

Sigue los mismos pasos que en el Ejercicio 1 (Web Bomberos) de la diapositiva:

1. Sube estos archivos a un repo de GitHub llamado `api-web-scraping` (o el nombre que
   pida el docente). Antes de subir, edita `serverless.yml` y reemplaza `TU_ORG_SERVERLESS`
   y `arn:aws:iam::TU_ACCOUNT_ID:role/LabRole` con tus datos reales.
2. Ingresa a "MV Desarrollo".
3. Actualiza el archivo `credentials` en `/home/ubuntu/.aws`.
4. Entra a `/home/ubuntu/lambdas/` y haz `git clone` de tu repo.
5. Instala las librerías no estándar en el mismo directorio:
   ```
   pip3 install -r requirements.txt -t .
   ```
6. Despliega:
   ```
   sls deploy
   ```
7. Prueba el endpoint (GET .../dev/scrape/sismos) y verifica en DynamoDB
   (tabla `TablaSismosIGP`) que se hayan guardado los 10 sismos.

## Si el scraping no encuentra datos (statusCode 404)

La web del IGP es una aplicación moderna que puede cargar el contenido con JavaScript.
El código ya intenta dos formas de extraer la info (tabla HTML, igual que en clase, y
un JSON interno que usan estas apps), pero si ninguna funciona:

1. Abre la URL en tu navegador, presiona F12 y entra a la pestaña "Network" (o "Red").
2. Recarga la página y filtra por "Fetch/XHR" para ver si hay una petición que trae los
   sismos en JSON (una API).
3. Si la encuentras, reemplaza en `scrap_sismos.py` el `requests.get(URL, ...)` para que
   apunte directamente a esa API, y ajusta cómo se leen los campos del JSON devuelto
   (ya no haría falta BeautifulSoup, solo `response.json()`).
4. Si en cambio sí hay una `<table>` en el HTML pero con otra estructura, revisa con
   "Elements" las clases/columnas reales y ajusta `extraer_desde_tabla`.

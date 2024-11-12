import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from flask import Flask, request, jsonify
import modelo
import requests
import matplotlib.pyplot as plt
import io

app = Flask(__name__)
def obtener_descripcion_tendencia(en_tendencia, fecha_good, fecha):
    true_descripcion = f'Felicidades haz encontrado una buena fecha para invertir. Todo indica que la fecha [{fecha}]es uno de los mejores momentos para exportar. Por lo que, se encuentra en tendencia.'
    false_descripcion = f'Lo siento, pero la fecha [{fecha}] no es la mejor para exportar. Por lo que, se encuentra fuera de tendencia. Te recomendamos exportar en la fecha [{fecha_good}] ya que se espera un aumento en las exportaciones por ende una mejor tendencia.'
    return true_descripcion if en_tendencia else false_descripcion
def generar_imagen(producto):
    PIXABAY_API_KEY = "47008472-16999a4f6476b93ee9917e69e"
    PIXABAY_URL = "https://pixabay.com/api/"

    try:
        response = requests.get(PIXABAY_URL, params={
            'key': PIXABAY_API_KEY,
            'q': producto,
            'image_type': 'photo',
            'per_page': 3
        })

        response.raise_for_status()
        data = response.json()

        if 'hits' in data and len(data['hits']) > 0:
            return data['hits'][0]['webformatURL']

        return "https://i.blogs.es/37ba66/trabajar-en-el-campo/1366_2000.jpg"
    except requests.RequestException as error:
        print(f"Error al buscar la imagen: {error}")
        return "https://i.blogs.es/37ba66/trabajar-en-el-campo/1366_2000.jpg"
@app.route('/predecir', methods=['POST'])
def predecir():
    try:
        data = request.get_json(force=True)
        producto = data.get('producto')
        fecha_str = data.get('fecha')

        if not producto or not fecha_str:
            return jsonify({'error': 'Faltan datos: producto y fecha son requeridos.'}), 400

        fecha = pd.to_datetime(fecha_str, errors='coerce')
        if pd.isnull(fecha):
            return jsonify({'error': 'La fecha proporcionada no es válida.'}), 400

        resultado = modelo.predecir_tendencia(producto, fecha)
        resultado.Descripcion_tendencia = obtener_descripcion_tendencia(resultado.en_tendencia, resultado.mejor_fecha, fecha)
        resultado.imagen = generar_imagen(producto)
        return jsonify(resultado)

    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/generar_grafica', methods=['POST'])
def generar_grafica():
    try:
        # Leer el producto de la solicitud
        data = request.get_json(force=True)
        producto = data.get('producto')

        if not producto:
            return jsonify({'error': 'El producto es requerido.'}), 400

        # Filtrar los datos para el producto especificado
        producto_filtrado = modelo.df[modelo.df['Descripcion Partida10 Dig'].str.lower() == producto.lower()]
        if producto_filtrado.empty:
            return jsonify({'error': f"No se encontraron datos para el producto '{producto}'."}), 400

        # Agrupar por fecha y calcular la suma de las exportaciones
        producto_agrupado = producto_filtrado.groupby('Fecha', as_index=False)[
            'Exportaciones en valor (Miles USD FOB)'
        ].sum()

        # Crear una serie temporal con frecuencia mensual
        ts = producto_agrupado.set_index('Fecha')['Exportaciones en valor (Miles USD FOB)']
        ts = ts.asfreq('MS')

        # Verificar si hay suficientes datos
        if len(ts) < 20:
            return jsonify({'error': "No hay suficientes datos para realizar la predicción."}), 400

        # Ajustar el modelo ARIMA y realizar predicciones
        ts_diff = ts.diff().dropna()
        model = ARIMA(ts_diff, order=(2, 1, 3))
        model_fit = model.fit(method_kwargs={"maxiter": 500})
        predictions = model_fit.predict(start=len(ts), end=len(ts) + 11)
        predictions_df = pd.DataFrame({
            'Fecha': pd.date_range(start=ts.index[-1] + pd.DateOffset(months=1), periods=12, freq='MS'),
            'Prediccion': predictions
        })

        # Formatear los datos para la gráfica
        datos_reales = [
            {'fecha': fecha.strftime('%Y-%m-%d'), 'valor': valor}
            for fecha, valor in ts.items()
        ]
        datos_prediccion = [
            {'fecha': fecha.strftime('%Y-%m-%d'), 'valor': valor}
            for fecha, valor in zip(predictions_df['Fecha'], predictions_df['Prediccion'])
        ]

        # Respuesta en formato JSON
        return jsonify({
            'producto': producto,
            'datos_reales': datos_reales,
            'datos_prediccion': datos_prediccion
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/predicciones', methods=['POST'])
def obtener_predicciones():
    try:
        # Leer el producto de la solicitud
        data = request.get_json(force=True)
        producto = data.get('producto')

        if not producto:
            return jsonify({'error': 'El producto es requerido.'}), 400

        # Filtrar los datos para el producto especificado
        producto_filtrado = modelo.df[modelo.df['Descripcion Partida10 Dig'].str.lower() == producto.lower()]
        if producto_filtrado.empty:
            return jsonify({'error': f"No se encontraron datos para el producto '{producto}'."}), 400

        # Agrupar por fecha y calcular la suma de las exportaciones
        producto_agrupado = producto_filtrado.groupby('Fecha', as_index=False)[
            'Exportaciones en valor (Miles USD FOB)'
        ].sum()

        # Crear una serie temporal con frecuencia mensual
        ts = producto_agrupado.set_index('Fecha')['Exportaciones en valor (Miles USD FOB)']
        ts = ts.asfreq('MS')

        # Verificar si hay suficientes datos
        if len(ts) < 20:
            return jsonify({'error': "No hay suficientes datos para realizar la predicción."}), 400

        # Ajustar el modelo ARIMA y realizar predicciones
        ts_diff = ts.diff().dropna()
        model = ARIMA(ts_diff, order=(2, 1, 3))
        model_fit = model.fit(method_kwargs={"maxiter": 500})
        predictions = model_fit.predict(start=len(ts), end=len(ts) + 11)
        predictions_df = pd.DataFrame({
            'Fecha': pd.date_range(start=ts.index[-1] + pd.DateOffset(months=1), periods=12, freq='MS'),
            'Prediccion': predictions
        })

        # Formatear los datos de predicción
        datos_prediccion = [
            {'fecha': fecha.strftime('%Y-%m-%d'), 'valor': valor}
            for fecha, valor in zip(predictions_df['Fecha'], predictions_df['Prediccion'])
        ]

        # Respuesta en formato JSON
        return jsonify({
            'producto': producto,
            'predicciones': datos_prediccion
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/productos', methods=['GET'])
def obtener_productos():
    try:
        # Obtener los productos únicos del archivo CSV
        productos_unicos = modelo.df['Descripcion Partida10 Dig'].dropna().unique().tolist()

        # Formatear la respuesta como una lista de diccionarios
        productos_formateados = [{'producto': producto} for producto in productos_unicos]

        # Respuesta en formato JSON
        return jsonify(productos_formateados)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)

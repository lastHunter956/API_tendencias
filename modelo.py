import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
import requests

meses_espanol = {
    'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 'Mayo': 5,
    'Junio': 6, 'Julio': 7, 'Agosto': 8, 'Septiembre': 9, 'Octubre': 10,
    'Noviembre': 11, 'Diciembre': 12
}

try:
    df = pd.read_csv('Exportaciones_agr_colas_no_tradicionales_y_tradicionales_20241031.csv')
except FileNotFoundError:
    raise FileNotFoundError("El archivo 'Exportaciones_agr_colas_no_tradicionales_y_tradicionales_20241031.csv' no se encontró.")

df['Mes'] = df['Mes'].str.strip().str.capitalize()
df['Mes_Num'] = df['Mes'].map(meses_espanol)
df['Fecha'] = pd.to_datetime(df['Año'].astype(str) + '-' + df['Mes_Num'].astype(str) + '-01', errors='coerce')
df = df.dropna(subset=['Fecha'])
def predecir_tendencia(producto, fecha):
    # Filtrar los datos para el producto especificado
    producto_filtrado = df[df['Descripcion Partida10 Dig'].str.lower() == producto.lower()]
    if producto_filtrado.empty:
        raise ValueError(f"No se encontraron datos para el producto '{producto}'.")

    # Agrupar por fecha y calcular la suma de las exportaciones
    producto_agrupado = producto_filtrado.groupby('Fecha', as_index=False)[
        'Exportaciones en valor (Miles USD FOB)'
    ].sum()

    # Crear una serie temporal con frecuencia mensual
    ts = producto_agrupado.set_index('Fecha')['Exportaciones en valor (Miles USD FOB)']
    ts = ts.asfreq('MS')

    # Verificar si hay suficientes datos para entrenar el modelo
    if len(ts) < 20:
        raise ValueError("No hay suficientes datos para realizar la predicción.")

    # Ajustar el modelo ARIMA
    ts_diff = ts.diff().dropna()
    model = ARIMA(ts_diff, order=(2, 1, 3))
    model_fit = model.fit(method_kwargs={"maxiter": 500})

    # Realizar predicciones para los próximos 12 meses
    predictions = model_fit.predict(start=len(ts), end=len(ts) + 11)
    predictions_df = pd.DataFrame({
        'Fecha': pd.date_range(start=ts.index[-1] + pd.DateOffset(months=1), periods=12, freq='MS'),
        'Prediccion': predictions
    })

    # Validar si la fecha solicitada está dentro del rango de predicción
    if fecha < predictions_df['Fecha'].min() or fecha > predictions_df['Fecha'].max():
        raise ValueError("La fecha especificada está fuera del rango de predicción.")

    # Obtener la predicción para la fecha especificada (comparando año y mes)
    prediccion_fecha = predictions_df.loc[predictions_df['Fecha'].dt.to_period('M') == fecha.to_period('M'), 'Prediccion']
    if prediccion_fecha.empty:
        raise ValueError(f"No se encontró predicción para la fecha especificada: {fecha}")

    # Calcular la media de los últimos 12 meses
    media_ts = ts[-12:].mean()

    # Determinar si el producto está en tendencia
    en_tendencia = bool(prediccion_fecha.iloc[0] > media_ts)  # Garantizar que es un bool serializable

    # Encontrar la mejor fecha para exportar
    mejor_fecha = predictions_df.loc[predictions_df['Prediccion'].idxmax()]

    return {
        'prediccion': round(prediccion_fecha.iloc[0], 2),
        'en_tendencia': en_tendencia,
        'mejor_fecha': mejor_fecha['Fecha'].strftime('%Y-%m-%d'),
        'Descripcion_tendencia' : obtener_descripcion_tendencia(en_tendencia, mejor_fecha['Fecha'].strftime('%Y-%m-%d'),
                                                                        fecha),
        'imagen' : generar_imagen(producto),
        'prediccion_mejor_fecha': round(mejor_fecha['Prediccion'], 2)
    }
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
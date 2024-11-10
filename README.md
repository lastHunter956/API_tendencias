
# API de Predicciones y Tendencias

Esta API permite realizar predicciones de exportaciones para productos específicos utilizando modelos ARIMA. Puedes obtener tanto los datos históricos como las predicciones futuras en formato JSON, ideales para integrarse con aplicaciones web o dashboards.

---

## **Requisitos previos**

1. Python 3.8 o superior instalado en tu sistema.
2. Instalar las dependencias necesarias:
   ```bash
   pip install flask pandas statsmodels matplotlib
   ```

3. Asegúrate de tener el archivo de datos `Exportaciones_agr_colas_no_tradicionales_y_tradicionales_20241031.csv` en la misma carpeta que el script.

---

## **Cómo ejecutar la API**

1. Guarda el script Python en un archivo llamado `app.py`.
2. Ejecuta la aplicación Flask con el siguiente comando:
   ```bash
   python app.py
   ```

3. La API estará disponible en `http://127.0.0.1:5000`.

---

## **Endpoints disponibles**

### **1. `/generar_grafica`**

- **Método:** POST
- **Descripción:** Devuelve los datos históricos y predicciones para un producto específico, listos para ser graficados.
- **Cuerpo de la solicitud (JSON):**
  ```json
  {
      "producto": "Nombre del producto"
  }
  ```
- **Ejemplo de respuesta:**
  ```json
  {
      "producto": "Fécula de mandioca (yuca)",
      "datos_reales": [
          {"fecha": "2019-01-01", "valor": 10.5},
          {"fecha": "2019-02-01", "valor": 12.0}
          // ...
      ],
      "datos_prediccion": [
          {"fecha": "2025-01-01", "valor": 15.0},
          {"fecha": "2025-02-01", "valor": 16.2}
          // ...
      ]
  }
  ```

---

### **2. `/predicciones`**

- **Método:** POST
- **Descripción:** Devuelve únicamente los datos de predicción para un producto específico.
- **Cuerpo de la solicitud (JSON):**
  ```json
  {
      "producto": "Nombre del producto"
  }
  ```
- **Ejemplo de respuesta:**
  ```json
  {
      "producto": "Fécula de mandioca (yuca)",
      "predicciones": [
          {"fecha": "2025-01-01", "valor": 15.0},
          {"fecha": "2025-02-01", "valor": 16.2}
          // ...
      ]
  }
  ```

---

## **Errores comunes**

### **1. Archivo no encontrado**
   - Asegúrate de que el archivo CSV con los datos esté en la misma carpeta que el script.

### **2. Producto no encontrado**
   - Verifica que el nombre del producto en la solicitud sea exacto al que aparece en el archivo CSV.

### **3. Insuficientes datos**
   - Si no hay suficientes datos históricos (menos de 20 registros), el modelo no podrá realizar predicciones.

---

## **Notas adicionales**

- Esta API utiliza el modelo ARIMA para predicciones basadas en series temporales.
- Para una implementación en producción, se recomienda usar un servidor WSGI como **gunicorn**.

---

¡Disfruta de la API!

---

### **3. `/productos`**

- **Método:** GET
- **Descripción:** Devuelve una lista de todos los productos únicos presentes en el archivo CSV.
- **Cuerpo de la solicitud:** Ninguno.
- **Ejemplo de respuesta:**
  ```json
  {
      "productos": [
          "Fécula de mandioca (yuca)",
          "Caballos reproductores de raza pura, vivos",
          "Café verde sin tostar"
          // ...
      ]
  }
  ```

import wave

def crear_wav_silencio(nombre_archivo="mi_freestyle.wav", duracion_segundos=1):
    # Parámetros estándar de audio (44.1 kHz, 16 bits, Mono)
    frecuencia_muestreo = 44100  
    canales = 1  
    ancho_muestra = 2  # 2 bytes = 16 bits
    
    # Calcular el número total de bytes necesarios para el silencio
    total_muestras = frecuencia_muestreo * duracion_segundos
    datos_silencio = b'\x00' * (total_muestras * canales * ancho_muestra)
    
    # Escribir la estructura del contenedor WAV en el disco
    with wave.open(nombre_archivo, 'wb') as archivo_wav:
        archivo_wav.setnchannels(canales)
        archivo_wav.setsampwidth(ancho_muestra)
        archivo_wav.setframerate(frecuencia_muestreo)
        archivo_wav.writeframes(datos_silencio)
        
    print(f"✅ Archivo '{nombre_archivo}' generado correctamente con {duracion_segundos} segundo de silencio estructurado.")

if __name__ == "__main__":
    crear_wav_silencio()


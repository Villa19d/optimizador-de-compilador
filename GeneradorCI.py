import re
import os
from lexer import tokenize
from lexer import t_error


# Funciones y variables permitidas
funciones_permitidas = {'sin', 'cos', 'tan', 'ln', 'sqrt'}
variables_permitidas = {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 
                        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
                        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                        'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'}

def construir_tabla_simbolos(expresiones):
    """
    Construye una tabla de símbolos a partir de las expresiones.
    """
    tabla_simbolos = {}
    direccion_counter = 1000

    for expresion in expresiones:
        tokens = tokenize(expresion)  # Usar el lexer para tokenizar
        for token_type, token_value in tokens:
            if token_type in funciones_permitidas:
                # Es una función permitida
                tabla_simbolos[token_value] = {
                    'tipo': 'función',
                    'tipo_dato': 'función',
                    'direccion': direccion_counter,
                    'valor': None
                }
                direccion_counter += 1
            elif token_type == 'IDENTIFICADOR' and token_value in variables_permitidas:
                # Es una variable permitida
                tabla_simbolos[token_value] = {
                    'tipo': 'variable',
                    'tipo_dato': 'char',
                    'direccion': direccion_counter,
                    'valor': None
                }
                direccion_counter += 1
            elif token_type == 'NUMEROTE':
                # Es un número
                tipo_dato = 'float' if isinstance(token_value, float) else 'int'
                tabla_simbolos[token_value] = {
                    'tipo': 'número',
                    'tipo_dato': tipo_dato,
                    'direccion': direccion_counter,
                    'valor': token_value
                }
                direccion_counter += 1
    print("Tabla de simbolos: ", tabla_simbolos)
    return tabla_simbolos

def imprimir_tabla_simbolos(tabla_simbolos):
    """
    Imprime la tabla de símbolos en un formato legible.
    """
    print("📌 Tabla de Símbolos:")
    print("{:<10} {:<10} {:<10} {:<10} {:<10}".format("Símbolo", "Tipo", "Dirección", "Valor", "Tipo Dato"))
    print("-" * 50)
    for simbolo, info in tabla_simbolos.items():
        print("{:<10} {:<10} {:<10} {:<10} {:<10}".format(
            simbolo,
            info['tipo'],
            info['direccion'],
            str(info['valor']) if info['valor'] is not None else "N/A",
            info['tipo_dato']
        ))


# MANEJO DE ERRORES #
def verificar_errores(expresion):
    """
    Verifica errores comunes en una expresión matemática.
    
    :param expresion: Expresión en notación infija.
    :raises ValueError: Si se encuentra un error en la expresión.
    """
    # Verificar expresiones vacías
    if not expresion.strip():
        raise ValueError("Expresión vacía. ")

    # Verificar paréntesis balanceados
    pila = []
    for caracter in expresion:
        if caracter == '(':
            pila.append(caracter)
        elif caracter == ')':
            if not pila or pila[-1] != '(':
                raise ValueError("Paréntesis no balanceados. ")
            pila.pop()
    if pila:
        raise ValueError("Paréntesis no balanceados. ")
    
     # Verificar si la expresión solo contiene un número, una letra o una función matemática sin operadores
    if re.fullmatch(r'\s*[a-zA-Z]+\s*', expresion):
        raise ValueError("Expresión inválida: falta un operador")
    if re.fullmatch(r'\s*\d+(\.\d+)?\s*', expresion):
        raise ValueError("Expresión inválida: falta un operador")
    if re.fullmatch(r'\s*(' + '|'.join(funciones_permitidas) + r')\s*\(\s*[a-zA-Z0-9]*\s*\)\s*', expresion):
        raise ValueError("Expresión inválida: falta un operador")

    # Verificar operadores faltantes o mal colocados
    operadores = {'+', '-', '*', '/', '%', '^'}
    for i in range(len(expresion) - 1):
        if expresion[i] in operadores and expresion[i + 1] in operadores:
            raise ValueError("Operadores consecutivos no permitidos")

    # Verificar división por cero
    if '/ 0' in expresion or '% 0' in expresion:
        raise ValueError("División por cero no permitida")

    # Verificar caracteres no permitidos
    caracteres_permitidos = set("0123456789+-*/%()^ .abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    for caracter in expresion:
        if caracter not in caracteres_permitidos:
            raise ValueError(f"Carácter no permitido: '{caracter}'")

    # Verificar funciones no definidas
    for func in re.findall(r'\b[a-zA-Z_]+\b', expresion):
        if func in funciones_permitidas:
            continue  # Es una función permitida
        elif func in variables_permitidas:
            continue  # Es una variable permitida
        else:
            raise ValueError(f"Función o variable no definida: '{func}'")

    # Verificar funciones sin argumentos
    for func in funciones_permitidas:
        if re.search(fr'{func}\s*\(\s*\)', expresion):
            raise ValueError(f"Función '{func}' sin argumentos")

    # Verificar paréntesis vacíos
    if re.search(r'\(\s*\)', expresion):
        raise ValueError("Paréntesis vacíos")

    # Verificar expresiones incompletas
    if expresion.strip().endswith(('+', '-', '*', '/', '%', '^', '(')):
        raise ValueError("Expresión incompleta")

    # Verificar números mal formados
    for numero in re.findall(r'\b\d*\.?\d+\b', expresion):
        try:
            float(numero)  # Intenta convertir a float
        except ValueError:
            raise ValueError(f"Número mal formado: '{numero}'")
        
    # Verificar números mal formados (más estricto)
    if re.search(r'\d+\.\d+\.', expresion):  
        raise ValueError("Número mal formado: múltiples puntos decimales")


# CONVERSIÓN DE NOTACIONES #
def infijo_a_postfijo(expresion):
    """
    Convierte una expresión infija en notación postfija.
    
    :param expresion: Expresión infija como cadena de texto.
    :return: Lista de tokens en notación postfija.
    :raises ValueError: Si hay un error en la conversión.
    """
    try:
        precedencia = {'+': 1, '-': 1, '*': 2, '/': 2, '%': 2, '^': 3, 'sin': 3, 'cos': 3, 'tan': 3}
        
        def es_operador(caracter):
            return caracter in precedencia
        
        pila = []
        salida = []
        i = 0
        while i < len(expresion):
            caracter = expresion[i]
            if caracter == ' ':
                i += 1
                continue
            if caracter == '(':
                pila.append(caracter)
            elif caracter == ')':
                while pila and pila[-1] != '(':
                    salida.append(pila.pop())
                pila.pop()
            elif es_operador(caracter):
                while (pila and pila[-1] != '(' and
                       precedencia[pila[-1]] >= precedencia[caracter]):
                    salida.append(pila.pop())
                pila.append(caracter)
            else:
                # Es un operando (variable o número)
                if caracter.isdigit():
                    num = ''
                    while i < len(expresion) and (expresion[i].isdigit() or expresion[i] == '.'):
                        num += expresion[i]
                        i += 1
                    salida.append(num)
                    continue
                else:
                    # Es una variable o función
                    var = ''
                    while i < len(expresion) and (expresion[i].isalpha() or expresion[i] == '_'):
                        var += expresion[i]
                        i += 1
                    if var in funciones_permitidas:
                        pila.append(var)
                    else:
                        salida.append(var)
                    continue
            i += 1
        while pila:
            salida.append(pila.pop())
        return salida
    except Exception as e:
        raise ValueError(f"Error en conversión a postfijo: {e}")

def infijo_a_prefijo(expresion):
    """
    Convierte una expresión infija en notación prefija.
    
    :param expresion: Expresión infija como cadena de texto.
    :return: Lista de tokens en notación prefija.
    :raises ValueError: Si hay un error en la conversión.
    """
    try:
        precedencia = {'+': 1, '-': 1, '*': 2, '/': 2, '%': 2, '^': 3, 'sin': 3, 'cos': 3, 'tan': 3}
        
        def es_operador(caracter):
            return caracter in precedencia
        
        pila = []
        salida = []
        expresion = expresion[::-1]
        i = 0
        while i < len(expresion):
            caracter = expresion[i]
            if caracter == ' ':
                i += 1
                continue
            if caracter == ')':
                pila.append(caracter)
            elif caracter == '(':
                while pila and pila[-1] != ')':
                    salida.append(pila.pop())
                pila.pop()  # Eliminar el ')'
            elif es_operador(caracter):
                while (pila and pila[-1] != ')' and
                       precedencia[pila[-1]] > precedencia[caracter]):
                    salida.append(pila.pop())
                pila.append(caracter)
            else:
                # Es un operando (variable o número)
                if caracter.isdigit():
                    num = ''
                    while i < len(expresion) and (expresion[i].isdigit() or expresion[i] == '.'):
                        num += expresion[i]
                        i += 1
                    salida.append(num[::-1])
                    continue
                else:
                    # Es una variable o función
                    var = ''
                    while i < len(expresion) and (expresion[i].isalpha() or expresion[i] == '_'):
                        var += expresion[i]
                        i += 1
                    if var[::-1] in funciones_permitidas:
                        pila.append(var[::-1])
                    else:
                        salida.append(var[::-1])
                    continue
            i += 1
        while pila:
            salida.append(pila.pop())
        return salida[::-1]
    except Exception as e:
        raise ValueError(f"Error en conversión a prefijo: {e}")

def infijo_a_codigo_p(expresion):
    """
    Convierte una expresión infija en código P.
    
    :param expresion: Expresión infija como cadena de texto.
    :return: Código P como cadena de texto.
    :raises ValueError: Si hay un error en la conversión.
    """
    try:
        # Precedencia de los operadores
        precedencia = {'+': 1, '-': 1, '*': 2, '/': 2, '%': 2, '^': 3, 'sin': 3, 'cos': 3, 'tan': 3}
        
        # Mapeo de operadores a sus equivalentes en código P
        operadores_p = {
            '+': 'ADD',
            '-': 'SUB',
            '*': 'MUL',
            '/': 'DIV',
            '%': 'MOD',
            '^': 'POW',
            'sin': 'SIN',
            'cos': 'COS',
            'tan': 'TAN',
            'ln': 'LN',
            'sqrt': 'SQRT'
        }
        
        # Función para verificar si un carácter es un operador
        def es_operador(caracter):
            return caracter in precedencia
        
        # Pila para operadores y salida para el código P
        pila_operadores = []
        codigo_p = []
        
        i = 0
        while i < len(expresion):
            caracter = expresion[i]
            
            # Ignorar espacios en blanco
            if caracter == ' ':
                i += 1
                continue
            
            # Si es un paréntesis de apertura, lo agregamos a la pila
            if caracter == '(':
                pila_operadores.append(caracter)
            
            # Si es un paréntesis de cierre, procesamos los operadores hasta encontrar el de apertura
            elif caracter == ')':
                while pila_operadores and pila_operadores[-1] != '(':
                    codigo_p.append(operadores_p[pila_operadores.pop()])
                pila_operadores.pop()
            
            # Si es un operador, procesamos los operadores de mayor o igual precedencia
            elif es_operador(caracter):
                while (pila_operadores and pila_operadores[-1] != '(' and
                       precedencia[pila_operadores[-1]] >= precedencia[caracter]):
                    codigo_p.append(operadores_p[pila_operadores.pop()])
                pila_operadores.append(caracter)
            
            # Si es una función, la agregamos a la pila
            elif caracter.isalpha():
                func = ''
                while i < len(expresion) and (expresion[i].isalpha() or expresion[i] == '_'):
                    func += expresion[i]
                    i += 1
                if func in funciones_permitidas:
                    pila_operadores.append(func)
                else:
                    codigo_p.append(f"PUSH {func}")
                continue
            
            # Si es un operando (número), lo agregamos directamente al código P
            else:
                if caracter.isdigit():
                    num = ''
                    while i < len(expresion) and (expresion[i].isdigit() or expresion[i] == '.'):
                        num += expresion[i]
                        i += 1
                    codigo_p.append(f"PUSH {num}")
                    continue
            
            i += 1
        
        # Procesar los operadores restantes en la pila
        while pila_operadores:
            codigo_p.append(operadores_p[pila_operadores.pop()])
        
        # Unir el código P en una sola cadena con saltos de línea
        return "\n".join(codigo_p)
    except Exception as e:
        raise ValueError(f"Error en conversión a código P: {e}")

def postfijo_a_codigo_intermedio(postfijo):
    """
    Convierte una expresión en notación postfija a código intermedio y código P.
    
    :param postfijo: Lista de tokens en notación postfija.
    :return: Una tupla con el código intermedio y el código P.
    :raises ValueError: Si hay un error en la conversión.
    """
    try:
        pila = []
        codigo_intermedio = []
        codigo_p = []  # Código P generado

        # Mapeo de operadores a sus equivalentes en código P
        operadores_p = {
            '+': 'ADD',
            '-': 'SUB',
            '*': 'MUL',
            '/': 'DIV',
            '%': 'MOD',
            '^': 'POW',
            'sin': 'SIN',
            'cos': 'COS',
            'tan': 'TAN',
            'ln': 'LN',
            'sqrt': 'SQRT'
        }

        temp_counter = 0
        def nueva_temp():
            nonlocal temp_counter
            temp = f'T{temp_counter}'
            temp_counter += 1
            return temp

        for token in postfijo:
            if token in operadores_p:
                if token in {'sin', 'cos', 'tan', 'ln', 'sqrt'}:
                    if len(pila) < 1:
                        raise ValueError("Expresión inválida: no hay suficientes operandos para la función.")
                    operando = pila.pop()
                    
                    # Generar código intermedio
                    temp = nueva_temp()
                    codigo_intermedio.append(f'{temp} = {token}({operando})')
                    pila.append(temp)
                    
                    # Generar código P
                    codigo_p.append(f"PUSH {operando}")
                    codigo_p.append(operadores_p[token])
                else:  # Es un operador binario
                    if len(pila) < 2:
                        raise ValueError("Expresión inválida: no hay suficientes operandos para el operador.")
                    operando2 = pila.pop()
                    operando1 = pila.pop()
                    
                    # Generar código intermedio
                    temp = nueva_temp()
                    codigo_intermedio.append(f'{temp} = {operando1} {token} {operando2}')
                    pila.append(temp)
                    
                    # Generar código P
                    codigo_p.append(f"PUSH {operando1}")
                    codigo_p.append(f"PUSH {operando2}")
                    codigo_p.append(operadores_p[token])
            else:
                pila.append(token)
        
        if len(pila) != 1:
            raise ValueError("Expresión inválida: la pila no se redujo a un solo valor.")
        
        # Agregar la asignación final (Z = resultado)
        resultado_final = pila.pop()
        codigo_intermedio.append(f'X = {resultado_final}')
        
        # Devolver el código intermedio y el código P
        return codigo_intermedio, "\n".join(codigo_p)
    except Exception as e:
        raise ValueError(f"Error en conversión a código intermedio: {e}")

def generar_triplos(codigo_intermedio):
    """
    Genera triplos a partir del código intermedio.
    Si la instrucción es una asignación (x = ...), usa la variable de destino.
    
    :param codigo_intermedio: Lista de instrucciones de código intermedio.
    :return: Lista de triplos.
    """
    triplos = []
    for i, instruccion in enumerate(codigo_intermedio):
        partes = instruccion.split()
        if len(partes) == 5:  # Formato: T0 = a + b
            triplos.append(f"({i+1}, {partes[3]}, {partes[2]}, {partes[4]})")
        elif len(partes) == 3:  # Formato: x = T0
            destino = partes[0]  # Captura la variable de destino (x, y, z, etc.)
            triplos.append(f"({i+1}, =, {partes[2]}, {destino})")
    return triplos

def generar_cuadruplos(codigo_intermedio):
    """
    Genera cuádruplos a partir del código intermedio.
    Si la instrucción es una asignación (x = ...), usa la variable de destino.
    
    :param codigo_intermedio: Lista de instrucciones de código intermedio.
    :return: Lista de cuádruplos.
    """
    cuadruplos = []
    for i, instruccion in enumerate(codigo_intermedio):
        partes = instruccion.split()
        if len(partes) == 5:  # Formato: T0 = a + b
            cuadruplos.append(f"({i+1}, {partes[3]}, {partes[2]}, {partes[4]}, {partes[0]})")
        elif len(partes) == 3:  # Formato: x = T0
            destino = partes[0]  # Captura la variable de destino (x, y, z, etc.)
            cuadruplos.append(f"({i+1}, =, {partes[2]}, , {destino})")
    return cuadruplos

def cargar_expresiones_desde_archivo(ruta_archivo):
    expresiones = []
    try:
        with open(ruta_archivo, "r", encoding="utf-8") as archivo:
            for linea in archivo:
                linea = linea.strip()
                if linea and not linea.startswith("#"):
                    expresiones.append(linea)
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo '{ruta_archivo}'.")
    
    return expresiones



def mostrar_menu():
    """
    Muestra el menú de opciones al usuario.
    """
    print("\nSeleccione una o más opciones (separadas por comas):")
    print("1. Notaciones (prefija, postfija y código intermedio)")
    print("2. Código P (código intermedio)")
    print("3. Triplos")
    print("4. Cuádruplos")
    print("5. Todas las anteriores")
    print("6. Salir")

def procesar_expresion(expresion, opciones, numero_expresion):
    """
    :param expresion: Expresión en notación infija.
    :param opciones: Lista de opciones seleccionadas por el usuario.
    :param numero_expresion: Número de la expresión (para etiquetar los resultados).
    :return: Lista de resultados.
    """
    try:
        # Si la expresión contiene una asignación, extraer la parte aritmética
        if '=' in expresion:
            expresion = expresion.split('=', 1)[1].strip()  # Ignorar la parte antes del "="
        
        # Verificar errores antes de procesar

        #t_error(expresion)
        verificar_errores(expresion)
        
        # Convertir la expresión a notaciones y código intermedio
        postfijo = infijo_a_postfijo(expresion)
        prefijo = infijo_a_prefijo(expresion)
        codigo_intermedio, codigo_p_intermedio = postfijo_a_codigo_intermedio(postfijo)
        codigo_p_directo = infijo_a_codigo_p(expresion)
        triplos = generar_triplos(codigo_intermedio)
        cuadruplos = generar_cuadruplos(codigo_intermedio)
        
        resultados = []
        
        if '1' in opciones or '5' in opciones:
            resultados.append("\n📌 Notaciones:")
            resultados.append(f"🔹 Prefija: {' '.join(prefijo)}")
            resultados.append(f"🔹 Postfija: {' '.join(postfijo)}")
            resultados.append("\n📌 Código Intermedio:")
            for instruccion in codigo_intermedio:
                resultados.append(instruccion)
        
        if '2' in opciones or '5' in opciones:
            resultados.append("\n📌 Código P (desde código intermedio):")
            resultados.append(codigo_p_intermedio)
            resultados.append("\n📌 Código P (directo desde infijo):")
            resultados.append(codigo_p_directo)
        
        if '3' in opciones or '5' in opciones:
            resultados.append("\n📌 Triplos:")
            for triplo in triplos:
                resultados.append(triplo)
        
        if '4' in opciones or '5' in opciones:
            resultados.append("\n📌 Cuádruplos:")
            for cuadruplo in cuadruplos:
                resultados.append(cuadruplo)
        
        return resultados
    except ValueError as e:
        return [f"❌ Error al procesar la expresión: {e}"]

def guardar_resultados(ruta_salida, resultados, tabla_simbolos):
    """
    Guarda los resultados en un archivo, incluyendo la tabla de símbolos al inicio.
    """
    try:
        with open(ruta_salida, "w", encoding="utf-8") as archivo:
            # Escribir la tabla de símbolos al inicio
            archivo.write("📌 Tabla de Símbolos:\n")
            archivo.write("{:<10} {:<10} {:<10} {:<10} {:<10}\n".format("Símbolo", "Tipo", "Dirección", "Valor", "Tipo Dato"))
            archivo.write("-" * 50 + "\n")
            for simbolo, info in tabla_simbolos.items():
                archivo.write("{:<10} {:<10} {:<10} {:<10} {:<10}\n".format(
                    simbolo,
                    info['tipo'],
                    info['direccion'],
                    str(info['valor']) if info['valor'] is not None else "N/A",
                    info['tipo_dato']
                ))
            archivo.write("\n")  # Línea en blanco para separar
            
            # Escribir los resultados
            for resultado in resultados:
                archivo.write(str(resultado) + "\n")
        print(f"\n✅ Resultados guardados en '{ruta_salida}'.")
    except IOError as e:
        print(f"❌ Error al guardar resultados: {e}")


def main():
    # Cargar expresiones desde el archivo
    ruta_entrada = r"C:\Users\rodri\OneDrive\Documentos\Escuela\Automatas2\3 Proyecto\3 Proyecto\datos.txt"
    expresiones = cargar_expresiones_desde_archivo(ruta_entrada)
    
    if not expresiones:
        print("No hay expresiones para procesar.")
        return
    
    # Construir la tabla de símbolos
    tabla_simbolos = construir_tabla_simbolos(expresiones)
    
    # Mostrar el menú
    while True:
        mostrar_menu()
        opciones = input("Opción(es): ").strip().split(',')
        
        if '6' in opciones:
            print("Saliendo...")
            break
        
        # Validar las opciones seleccionadas
        opciones_validas = []
        for opcion in opciones:
            opcion = opcion.strip()
            if opcion in ['1', '2', '3', '4', '5']:
                opciones_validas.append(opcion)
            else:
                print(f"❌ Opción '{opcion}' no válida. Se ignorará.")
        
        if not opciones_validas:
            print("❌ No se seleccionaron opciones válidas. Intente de nuevo.")
            continue
        
        # Procesar todas las expresiones
        resultados_totales = []
        for i, expresion in enumerate(expresiones, 1):
            # Agregar la línea de la expresión solo una vez
            resultados_totales.append(f"\n----- Expresión {i}: {expresion} -----")
            
            # Procesar la expresión para las opciones seleccionadas
            resultados = procesar_expresion(expresion, opciones_validas, i)
            resultados_totales.extend(resultados)
        
        # Guardar resultados en un archivo
        ruta_salida = "resultados.txt"
        guardar_resultados(ruta_salida, resultados_totales, tabla_simbolos)

        # Abrir automáticamente el archivo de resultados
        print(f"📂 Abriendo archivo: {ruta_salida}")
        os.system(f'start {ruta_salida}')


if __name__ == "__main__":
    main()
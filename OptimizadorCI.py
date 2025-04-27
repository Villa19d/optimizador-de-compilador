import math
import re
import os
from collections import defaultdict
from GeneradorCI import verificar_errores, infijo_a_postfijo, infijo_a_prefijo, postfijo_a_codigo_intermedio, infijo_a_codigo_p, generar_triplos, generar_cuadruplos, construir_tabla_simbolos

# --- CONSTANTES ---
funciones_permitidas = {'sin', 'cos', 'tan', 'ln', 'sqrt'}
variables_permitidas = {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 
                    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
                    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                    'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'}

# --- FUNCIONES AUXILIARES ---

def normalizar_codigo(codigo):
    """Convierte todas las instrucciones a strings"""
    return [' '.join(inst) if isinstance(inst, list) else inst for inst in codigo]

# --- FUNCIONES DE OPTIMIZACIÓN ---

def optimizar_constantes(codigo_intermedio):
    optimizado = []
    constantes = {}
    
    for instruccion in codigo_intermedio:
        partes = instruccion.split()
        if not partes:
            continue
        
        # 1. Evaluar funciones matemáticas con constantes
        if len(partes) == 4 and '(' in partes[3]:
            funcion, arg = partes[3].split('(')[0], partes[3].split('(')[1].split(')')[0]
            if arg.replace('.', '', 1).isdigit() and funcion in funciones_permitidas:
                try:
                    resultado = str(eval(f"math.{funcion}({arg})"))
                    constantes[partes[0]] = resultado
                    continue
                except:
                    pass
        
        # 2. Constant Folding para operaciones básicas
        if len(partes) == 5:  # Formato: T0 = a op b
            op1, op, op2 = partes[2], partes[3], partes[4]
            op1 = constantes.get(op1, op1)
            op2 = constantes.get(op2, op2)
            
            if (op1.replace('.','',1).isdigit() and 
                op2.replace('.','',1).isdigit()):
                try:
                    expr = f"{op1} {op} {op2}".replace('^','**')
                    resultado = str(eval(expr))
                    constantes[partes[0]] = resultado
                    continue
                except:
                    pass
                    
            optimizado.append(f"{partes[0]} = {op1} {op} {op2}")
            
        # 3. Propagación de constantes en asignaciones
        elif len(partes) == 3:  # Formato: X = T0
            valor = partes[2]
            while valor in constantes:
                valor = constantes[valor]
            if partes[0] != valor:  # Evitar X = X
                optimizado.append(f"{partes[0]} = {valor}")
    
    return optimizado

def aplicar_strength_reduction(codigo):
    optimizado = []
    for instr in codigo:
        partes = instr.split()
        if not partes:
            continue
        
        if len(partes) == 5:  # Formato: T0 = a op b
            op, a, b = partes[3], partes[2], partes[4]
            
            # Optimización de identidades algebraicas
            if (op == '*' and b == '1') or (op == '/' and b == '1'):
                optimizado.append(f"{partes[0]} = {a}")
                continue
            elif op == '*' and a == '1':
                optimizado.append(f"{partes[0]} = {b}")
                continue
            elif (op == '+' and b == '0') or (op == '-' and b == '0'):
                optimizado.append(f"{partes[0]} = {a}")
                continue
            elif op == '^' and b == '2':
                optimizado.append(f"{partes[0]} = {a} * {a}")
                continue
            elif op == '+' and a == b:
                optimizado.append(f"{partes[0]} = 2 * {a}")
                continue
            elif op == '*' and b == '2':
                optimizado.append(f"{partes[0]} = {a} + {a}")
                continue
                
        optimizado.append(instr)
    return optimizado

def eliminar_subexpresiones_comunes(codigo):
    expresiones = {}
    optimizado = []
    reemplazos = {}

    # Primera pasada: identificar expresiones idénticas
    for instr in codigo:
        partes = instr.split()
        if not partes:
            continue
            
        if len(partes) == 5:  # Formato: T0 = a + b
            # Normalizar para operaciones conmutativas
            if partes[3] in ['+', '*']:
                key = tuple(sorted([partes[2], partes[4]])) + (partes[3],)
            else:
                key = (partes[2], partes[3], partes[4])
            
            if key in expresiones:
                reemplazos[partes[0]] = expresiones[key]
            else:
                expresiones[key] = partes[0]
                optimizado.append(instr)
        else:
            optimizado.append(instr)
    
    # Segunda pasada: reemplazar usos de subexpresiones
    resultado = []
    for instr in optimizado:
        partes = instr.split()
        if not partes:
            continue
            
        if len(partes) == 5:  # T0 = a + b
            op1 = reemplazos.get(partes[2], partes[2])
            op2 = reemplazos.get(partes[4], partes[4])
            resultado.append(f"{partes[0]} = {op1} {partes[3]} {op2}")
        elif len(partes) == 3:  # X = T0
            rhs = reemplazos.get(partes[2], partes[2])
            resultado.append(f"{partes[0]} = {rhs}")
        else:
            resultado.append(instr)
    
    return resultado

def optimizar_mirilla(codigo):
    optimizado = []
    valores = {}
    
    for instr in codigo:
        partes = instr.split()
        if not partes:
            continue
            
        # Eliminar asignaciones redundantes (T1 = T0 cuando T0 no se usa después)
        if len(partes) == 3 and partes[1] == '=' and partes[2] in valores:
            valores[partes[0]] = valores[partes[2]]
            continue
            
        # Propagación de valores conocidos
        if len(partes) >= 3:
            nueva_instr = []
            for token in partes:
                nueva_instr.append(valores.get(token, token))
            instr = ' '.join(nueva_instr)
            
        # Eliminar asignaciones a X redundantes
        if len(partes) == 3 and partes[0] == 'X' and partes[2] == 'X':
            continue
            
        optimizado.append(instr)
        
        # Registrar nuevas asignaciones
        if len(partes) == 3 and partes[1] == '=':
            valores[partes[0]] = partes[2]
    
    return optimizado

def obtener_temporales_usados(codigo):
    print("Obteniendo temporales usados...1")
    """Identifica todos los temporales que son utilizados en el código"""
    usados = set()
    definidos = set()
    
    for instruccion in codigo:
        partes = instruccion.split()
        
        # Registrar temporales definidos (lado izquierdo)
        if partes and partes[0].startswith('T'):
            definidos.add(partes[0])
            
        # Registrar temporales usados (lado derecho)
        for token in partes[2:]:
            if token.startswith('T'):
                usados.add(token)
    
    # Solo los temporales que son usados después de ser definidos
    return usados.intersection(definidos)

def optimizar_codigo_completo(codigo_intermedio):
    # Normalizar formato primero
    codigo = normalizar_codigo(codigo_intermedio)
    
    # Asegurar asignación final si no existe
    if not any(inst.startswith('X =') for inst in codigo):
        ultimo_temp = codigo[-1].split('=')[0].strip()
        codigo.append(f"X = {ultimo_temp}")
    
    # Aplicar optimizaciones en orden correcto
    for _ in range(2):  # Máximo 2 pasadas
        nuevo_codigo = optimizar_constantes(codigo)
        nuevo_codigo = aplicar_strength_reduction(nuevo_codigo)
        nuevo_codigo = eliminar_subexpresiones_comunes(nuevo_codigo)
        nuevo_codigo = optimizar_mirilla(nuevo_codigo)
        
        if nuevo_codigo == codigo:
            break
        codigo = nuevo_codigo
    
    # Limpiar temporales no utilizados
    temporales_usados = obtener_temporales_usados(codigo)
    return [inst for inst in codigo if not inst.startswith('T') or inst.split()[0] in temporales_usados]

# --- GENERACIÓN DE CÓDIGO P ---

def generar_codigo_p_optimizado(definitions, resultado_final='X'):
    codigo_p = []
    pila = []
    
    # Caso cuando todo se optimizó a una constante
    if resultado_final and resultado_final.replace('.', '', 1).isdigit():
        return f"PUSH {resultado_final}"
    
    for lhs, op, a1, a2 in definitions:
        # Optimización especial para cuadrados
        if op == '^' and a2 == '2':
            codigo_p.append(f"PUSH {a1}")
            codigo_p.append(f"PUSH {a1}")
            codigo_p.append("MUL")
        else:
            # Mapeo de operadores
            mapeo = {'+':'ADD', '-':'SUB', '*':'MUL', '/':'DIV', '^':'POW'}
            # Optimizar operandos que son constantes
            a1_opt = a1 if not a1.replace('.', '', 1).isdigit() else str(float(a1))
            a2_opt = a2 if not a2.replace('.', '', 1).isdigit() else str(float(a2))
            
            codigo_p.append(f"PUSH {a1_opt}")
            codigo_p.append(f"PUSH {a2_opt}")
            codigo_p.append(mapeo.get(op, op))
        
        pila.append(lhs)
    
    return "\n".join(codigo_p) if codigo_p else "PUSH X"

# --- FUNCIÓN PRINCIPAL PROCESAR_EXPRESION ---
def procesar_expresion(expresion, opciones, numero_expresion):
    try:
        if '=' in expresion:
            expresion = expresion.split('=', 1)[1].strip()
        
        # Verificar errores sintácticos (esto siempre se ejecuta)
        verificar_errores(expresion) #Si existe error, lanza ValueError y termina la ejecucion del try, y lo manda directamente al except
        
        resultados = []
        postfijo = None
        prefijo = None
        codigo_intermedio = None
        codigo_intermedio_opt = None
        definitions = []
        resultado_final = None
        
        # Solo calcula lo necesario según las opciones seleccionadas
        #Se definen las variables que se van a usar para determinar si se necesita cada una de las opciones
        #De esta forma evitamos hacer cálculos innecesarios
        necesita_notaciones = '1' in opciones or '5' in opciones
        necesita_codigo_p = '2' in opciones or '5' in opciones
        necesita_triplos = '3' in opciones or '5' in opciones
        necesita_cuadruplos = '4' in opciones or '5' in opciones
        
        # 1. Generar notaciones (solo si se necesitan)
        if necesita_notaciones or necesita_codigo_p or necesita_triplos or necesita_cuadruplos:
            postfijo = infijo_a_postfijo(expresion)
            if necesita_notaciones:
                prefijo = infijo_a_prefijo(expresion)
        
        # 2. Generar código intermedio (solo si se necesitan triplos, cuádruplos o código P)
        if necesita_triplos or necesita_cuadruplos or necesita_codigo_p:
            codigo_intermedio, _ = postfijo_a_codigo_intermedio(postfijo)
            codigo_intermedio = normalizar_codigo(codigo_intermedio)
            
            # Asegurar asignación final si no existe
            if not any(inst.startswith('X =') for inst in codigo_intermedio):
                ultimo_temp = codigo_intermedio[-1].split('=')[0].strip()
                codigo_intermedio.append(f"X = {ultimo_temp}")
            
            codigo_intermedio_opt = optimizar_codigo_completo(codigo_intermedio)
            
            # Solo extraer definitions si se necesita código P
            if necesita_codigo_p:
                for instr in codigo_intermedio_opt:
                    partes = instr.split()
                    if len(partes) == 5 and partes[1] == '=':  # T0 = a + b
                        definitions.append((partes[0], partes[3], partes[2], partes[4]))
                    elif len(partes) == 3 and partes[0] == 'X':
                        resultado_final = partes[2]  # Guardar el resultado final (X = ...)
        
        # Calcular métricas solo si se muestran comparaciones
        if necesita_notaciones or necesita_triplos or necesita_cuadruplos:
            metricas = calcular_metricas(codigo_intermedio, codigo_intermedio_opt)
            resultados.append(generar_tabla_comparativa(expresion, metricas))
        
        # 1. Notaciones y código intermedio
        if necesita_notaciones:
            resultados.append("\n📌 Notaciones:")
            resultados.append(f"🔹 Prefija: {' '.join(prefijo)}")
            resultados.append(f"🔹 Postfija: {' '.join(postfijo)}")

            resultados.append("\n📌 Código Intermedio:")
            resultados.append("ORIGINAL:")
            resultados.extend(codigo_intermedio)
            resultados.append("\nOPTIMIZADO:")
            resultados.extend(codigo_intermedio_opt)
        
        # 2. Código P
        if necesita_codigo_p:
            resultados.append("\n📌 Código P:")
            resultados.append("ORIGINAL (desde infijo):")
            resultados.append(infijo_a_codigo_p(expresion))
            
            resultados.append("\nOPTIMIZADO (desde código intermedio optimizado):")
            codigo_p_opt = generar_codigo_p_optimizado(definitions, resultado_final)
            resultados.extend(codigo_p_opt.split('\n'))
        
        # 3. Triplos
        if necesita_triplos:
            resultados.append("\n📌 Triplos:")
            resultados.append("ORIGINAL:")
            resultados.extend(generar_triplos(codigo_intermedio))
            resultados.append("\nOPTIMIZADO:")
            resultados.extend(generar_triplos(codigo_intermedio_opt))
        
        # 4. Cuádruplos
        if necesita_cuadruplos:
            resultados.append("\n📌 Cuádruplos:")
            resultados.append("ORIGINAL:")
            resultados.extend(generar_cuadruplos(codigo_intermedio))
            resultados.append("\nOPTIMIZADO:")
            resultados.extend(generar_cuadruplos(codigo_intermedio_opt))
        
        return resultados
        
    except ValueError as e:
        return [f"❌ Error al procesar la expresión: {e}"]

# --- FUNCIONES DE GENERACIÓN DE REPRESENTACIONES ---

def generar_triplos(codigo_intermedio):
    triplos = []
    for idx, instruccion in enumerate(codigo_intermedio, start=1):
        partes = instruccion.split()
        if not partes:
            continue
            
        if len(partes) == 5:  # T0 = a + b
            triplos.append(f"({idx}, {partes[3]}, {partes[2]}, {partes[4]})")
        elif len(partes) == 3:  # X = T0
            triplos.append(f"({idx}, =, {partes[2]}, {partes[0]})")
    
    return triplos

def generar_cuadruplos(codigo_intermedio):
    cuadruplos = []
    for idx, instruccion in enumerate(codigo_intermedio, start=1):
        partes = instruccion.split()
        if not partes:
            continue
            
        if len(partes) == 5:  # T0 = a + b
            cuadruplos.append(f"({idx}, {partes[3]}, {partes[2]}, {partes[4]}, {partes[0]})")
        elif len(partes) == 3:  # X = T0
            cuadruplos.append(f"({idx}, =, {partes[2]}, , {partes[0]})")
    
    return cuadruplos

# --- FUNCIONES DE ARCHIVOS Y MENÚ ---
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

def calcular_metricas(codigo_original, codigo_optimizado):
    """Calcula métricas de comparación entre código original y optimizado"""
    metricas = {
        'temporales_original': len([inst for inst in codigo_original if '=' in inst]),
        'temporales_optimizado': len([inst for inst in codigo_optimizado if '=' in inst]),
        'operaciones_original': sum(1 for inst in codigo_original if any(op in inst for op in ['+', '-', '*', '/', '^'])),
        'operaciones_optimizado': sum(1 for inst in codigo_optimizado if any(op in inst for op in ['+', '-', '*', '/', '^'])),
        'lineas_original': len(codigo_original),
        'lineas_optimizado': len(codigo_optimizado)
    }
    
    # Calcular porcentajes de reducción
    metricas['reduccion_temporales'] = 100 - (metricas['temporales_optimizado'] / metricas['temporales_original'] * 100) if metricas['temporales_original'] > 0 else 0
    metricas['reduccion_operaciones'] = 100 - (metricas['operaciones_optimizado'] / metricas['operaciones_original'] * 100) if metricas['operaciones_original'] > 0 else 0
    metricas['reduccion_lineas'] = 100 - (metricas['lineas_optimizado'] / metricas['lineas_original'] * 100) if metricas['lineas_original'] > 0 else 0
    
    return metricas

def generar_tabla_comparativa(expresion, metricas):
    """Genera una tabla comparativa en formato markdown"""
    tabla = f"""
### Comparativa de optimización para: `{expresion}`

| Métrica               | Original | Optimizado | Reducción |
|-----------------------|----------|------------|-----------|
| Temporales usados     | {metricas['temporales_original']:8} | {metricas['temporales_optimizado']:10} | {metricas['reduccion_temporales']:6.1f}% |
| Operaciones realizadas| {metricas['operaciones_original']:8} | {metricas['operaciones_optimizado']:10} | {metricas['reduccion_operaciones']:6.1f}% |
| Líneas de código      | {metricas['lineas_original']:8} | {metricas['lineas_optimizado']:10} | {metricas['reduccion_lineas']:6.1f}% |

**Técnicas aplicadas**: {detectar_tecnicas_aplicadas(metricas)}
"""
    return tabla

def detectar_tecnicas_aplicadas(metricas):
    tecnicas = []
    if metricas['reduccion_temporales'] > 30:
        tecnicas.append("Eliminación de subexpresiones comunes (CSE)")
    if metricas['reduccion_operaciones'] > metricas['reduccion_temporales']:
        tecnicas.append("Strength Reduction")
    if metricas['lineas_optimizado'] < metricas['lineas_original'] * 0.5:
        tecnicas.append("Constant Folding/Propagation")
    if not tecnicas:
        tecnicas.append("Optimización básica")
    return ", ".join(tecnicas)

def mostrar_menu():
    print("\nSeleccione una o más opciones (separadas por comas):")
    print("1. Notaciones (prefija, postfija y código intermedio)")
    print("2. Código P (código intermedio)")
    print("3. Triplos")
    print("4. Cuádruplos")
    print("5. Todas las anteriores")
    print("6. Salir")

def guardar_resultados(ruta_salida, resultados, tabla_simbolos):
    try:
        with open(ruta_salida, "w", encoding="utf-8") as archivo:
            archivo.write("=== TABLA DE SÍMBOLOS ===\n")
            archivo.write("{:<10} {:<10} {:<10} {:<10} {:<10}\n".format(
                "Símbolo", "Tipo", "Dirección", "Valor", "Tipo Dato"))
            archivo.write("-" * 50 + "\n")
            for simbolo, info in tabla_simbolos.items():
                archivo.write("{:<10} {:<10} {:<10} {:<10} {:<10}\n".format(
                    simbolo, info['tipo'], info['direccion'],
                    str(info['valor']) if info['valor'] is not None else "N/A",
                    info['tipo_dato']
                ))
            archivo.write("\n")
            
            for resultado in resultados:
                if isinstance(resultado, list):
                    for linea in resultado:
                        archivo.write(linea + "\n")
                else:
                    archivo.write(resultado + "\n")
        print(f"\n✅ Resultados guardados en '{ruta_salida}'.")
    except IOError as e:
        print(f"❌ Error al guardar resultados: {e}")

def main(): 
    ruta_entrada = r"C:\Users\rodri\OneDrive\Documentos\Escuela\Automatas2\3 Proyecto\3 Proyecto\datos.txt"
    expresiones = cargar_expresiones_desde_archivo(ruta_entrada)
    print(expresiones)
                  
    
    if not expresiones:
        print("No hay expresiones para procesar.")
        return
    
    tabla_simbolos = construir_tabla_simbolos(expresiones)
    print("Tabla de símbolos construida.", tabla_simbolos)
    
    while True:
        mostrar_menu()
        opciones = input("Opción(es): ").strip().split(',')
        
        if '6' in opciones:
            print("Saliendo...")
            break
        
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
        
        resultados_totales = []
        for i, expresion in enumerate(expresiones, 1):
            resultados_totales.append(f"\n----- Expresión {i}: {expresion} -----")
            resultados = procesar_expresion(expresion, opciones_validas, i)
            resultados_totales.extend(resultados)
        
        ruta_salida = "resultados.txt"
        guardar_resultados(ruta_salida, resultados_totales, tabla_simbolos)

        print(f"📂 Abriendo archivo: {ruta_salida}")
        if os.name == 'nt':
            os.system(f'start {ruta_salida}')

if __name__ == "__main__":
    main()
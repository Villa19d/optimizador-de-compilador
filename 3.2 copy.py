import re
import os
import math
from collections import defaultdict
from GeneradorCI import verificar_errores, infijo_a_postfijo, infijo_a_prefijo, postfijo_a_codigo_intermedio, infijo_a_codigo_p, generar_triplos, generar_cuadruplos, construir_tabla_simbolos

# --- CONSTANTES ---
funciones_permitidas = {'sin', 'cos', 'tan', 'ln', 'sqrt'}
variables_permitidas = {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 
                    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
                    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                    'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'}

def normalizar_codigo(codigo):
    """Uniformiza el formato del código intermedio"""
    return [' '.join(inst) if isinstance(inst, list) else inst for inst in codigo]

def optimizar_constantes(codigo_intermedio):
    optimizado = []
    constantes = {}
    
    for instruccion in codigo_intermedio:
        partes = instruccion.split()
        
        # Manejar funciones matemáticas (sin, cos, etc.)
        if len(partes) == 4 and '(' in partes[3]:
            funcion, arg = partes[3].split('(')[0], partes[3].split('(')[1].split(')')[0]
            if arg.replace('.', '', 1).isdigit() and funcion in funciones_permitidas:
                try:
                    resultado = str(eval(f"math.{funcion}({arg})"))
                    constantes[partes[0]] = resultado
                    continue
                except:
                    pass
        
        # Constant folding para operaciones básicas
        if len(partes) == 5:  # T0 = a op b
            op1, op, op2 = partes[2], partes[3], partes[4]
            op1 = constantes.get(op1, op1)
            op2 = constantes.get(op2, op2)
            
            # Evaluar si ambos operandos son constantes
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
            
        elif len(partes) == 3:  # X = T0
            valor = partes[2]
            # Seguir la cadena de asignaciones
            while valor in constantes:
                valor = constantes[valor]
            if partes[0] != valor:  # Evitar X = X
                optimizado.append(f"{partes[0]} = {valor}")
    
    return optimizado

def aplicar_strength_reduction(codigo):
    optimizado = []
    for instr in codigo:
        partes = instr.split()
        
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

# Función para eliminar subexpresiones comunes en el código
def eliminar_subexpresiones_comunes(codigo):
    expresiones = {}
    optimizado = []
    reemplazos = {}

    # Primera pasada: identificar expresiones idénticas
    for instr in codigo:
        partes = instr.split()
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
    asignaciones = {}
    usos = defaultdict(int)
    
    # Contar usos de cada temporal
    for instr in codigo:
        partes = instr.split()
        if len(partes) >= 3:
            for token in partes[2:]:
                if token in asignaciones:
                    usos[token] += 1
    
    # Aplicar optimizaciones
    for instr in codigo:
        partes = instr.split()
        
        # 1. Preservar siempre las asignaciones a X
        if len(partes) >= 3 and partes[0] == 'X':
            optimizado.append(instr)
            continue
            
        # 2. Eliminar asignaciones redundantes (T1 = T1)
        if len(partes) == 3 and partes[0] == partes[2]:
            continue
            
        # 3. Propagación de copias (T1 = T0 cuando T0 no se usa después)
        if len(partes) == 3 and partes[2] in asignaciones and usos[partes[2]] <= 1:
            optimizado.append(f"{partes[0]} = {asignaciones[partes[2]]}")
        else:
            optimizado.append(instr)
            
        # Registrar nuevas asignaciones
        if len(partes) == 3 and partes[1] == '=':
            asignaciones[partes[0]] = partes[2]
    
    return optimizado

def obtener_temporales_usados(codigo):
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

def optimizar_codigo_p(codigo_p, constantes=None):
    if constantes is None:
        constantes = {}
        
    optimizado = []
    pila = []
    
    for linea in codigo_p.split('\n'):
        linea = linea.strip()
        if not linea:
            continue
            
        if linea.startswith("PUSH"):
            val = linea.split()[1]
            # Limpiar paréntesis
            val = val.replace('(', '').replace(')', '')
            val = constantes.get(val, val)
            pila.append(val)
            
        elif linea in {'ADD', 'SUB', 'MUL', 'DIV', 'POW'}:
            if len(pila) >= 2:
                op2 = pila.pop()
                op1 = pila.pop()
                
                # Optimizar operaciones conocidas
                if linea == 'POW' and op2 == '2':
                    optimizado.append(f"PUSH {op1}")
                    optimizado.append(f"PUSH {op1}")
                    optimizado.append("MUL")
                    pila.append("TEMP")
                    continue
                    
                if (op1.isdigit() and op2.isdigit()):
                    try:
                        res = eval(f"{op1} {linea} {op2}")
                        pila.append(str(res))
                        continue
                    except:
                        pass
                        
                optimizado.append(f"PUSH {op1}")
                optimizado.append(f"PUSH {op2}")
                optimizado.append(linea)
                pila.append("TEMP")
    
    # Limpiar resultado final
    resultado = "\n".join(optimizado)
    return resultado.replace('(', '').replace(')', '')


def codigo_intermedio_a_p(codigo_intermedio):
    codigo_p = []
    pila = []
    
    for instruccion in codigo_intermedio:
        partes = instruccion.split()
        
        if len(partes) == 5:  # T0 = x * x
            op1, operador, op2 = partes[2], partes[3], partes[4]
            
            # Mapeo de operadores
            mapeo = {'+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV', '^': 'POW'}
            
            # Evitar paréntesis en operandos
            op1 = op1.replace('(', '').replace(')', '')
            op2 = op2.replace('(', '').replace(')', '')
            
            codigo_p.append(f"PUSH {op1}")
            codigo_p.append(f"PUSH {op2}")
            codigo_p.append(mapeo.get(operador, operador))
            
            # Guardar en pila para uso posterior
            pila.append(partes[0])
            
        elif len(partes) == 3:  # X = T0
            valor = partes[2]
            # Si es un temporal previamente calculado
            if valor in pila:
                # No necesitamos hacer PUSH del temporal
                continue
            codigo_p.append(f"PUSH {valor}")
    
    return "\n".join(codigo_p)


def obtener_constantes(codigo_intermedio):
    constantes = {}
    for instr in codigo_intermedio:
        partes = instr.split()
        if len(partes) == 3 and partes[2].replace('.', '', 1).isdigit():
            constantes[partes[0]] = partes[2]
    return constantes


def generar_triplos_OP(codigo_intermedio_opt):
    triplos = []
    for idx, instruccion in enumerate(codigo_intermedio_opt, start=1):
        partes = instruccion.split()
        
        if len(partes) == 5:  # T0 = a + b
            triplos.append(f"({idx}, {partes[3]}, {partes[2]}, {partes[4]})")
        elif len(partes) == 3:  # X = valor
            if partes[2].replace('.', '').isdigit():
                triplos.append(f"({idx}, =, {partes[2]}, {partes[0]})")
            else:
                triplos.append(f"({idx}, =, {partes[2]}, {partes[0]})")
    
    return triplos

def generar_cuadruplos_OP(codigo_intermedio_opt):
    cuadruplos = []
    for idx, instruccion in enumerate(codigo_intermedio_opt, start=1):
        partes = instruccion.split()
        
        if len(partes) == 5:  # T0 = a + b
            cuadruplos.append(f"({idx}, {partes[3]}, {partes[2]}, {partes[4]}, {partes[0]})")
        elif len(partes) == 3:  # X = valor
            cuadruplos.append(f"({idx}, =, {partes[2]}, , {partes[0]})")
    
    return cuadruplos

def operation_to_instruction(op):
    return {
        '+': 'ADD',
        '-': 'SUB',
        '*': 'MUL',
        '/': 'DIV',
        '^': 'POW'
    }[op]

def is_literal(tok):
    try:
        float(tok)
        return True
    except ValueError:
        return False

def generate_code_p(var, definitions, visited=None):
    """
    var: nombre de la variable/temporal ('X','T0',...)
    definitions: lista de tuplas (lhs, operador, arg1, arg2)
    """
    if visited is None:
        visited = set()

    # 1) Si es literal numérico → PUSH literal
    if is_literal(var):
        return [f"PUSH {var}"]

    # 2) Recopilar todos los lhs (temporales y 'X')
    lhs_names = {lhs for lhs,_,_,_ in definitions}

    # 3) Si no es un lhs definido, es variable → PUSH var
    if var not in lhs_names:
        return [f"PUSH {var}"]

    # 4) Ya es un lhs, prevenir recursión infinita
    if var in visited:
        return []
    visited.add(var)

    # 5) Encontrar su definición y generar código
    for lhs, op, a1, a2 in definitions:
        if lhs == var:
            # Opcional: para * y +, empuja primero la subexpresión compleja
            if op in ('*','+') and is_literal(a1) and not is_literal(a2):
                a1, a2 = a2, a1

            code = []
            code += generate_code_p(a1, definitions, visited)
            code += generate_code_p(a2, definitions, visited)
            code.append(operation_to_instruction(op))
            return code

    # 6) Fallback (no debería ocurrir)
    return [f"PUSH {var}"]

def generar_codigo_p_optimizado(definitions, resultado_final='X'):
    codigo_p = []
    pila = []
    
    # Si no hay definiciones pero hay resultado final
    if not definitions and resultado_final.replace('.', '', 1).isdigit():
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
    
    # Manejar el caso donde todo se optimizó a una constante
    if not codigo_p and resultado_final.replace('.', '', 1).isdigit():
        return f"PUSH {resultado_final}"
    
    return "\n".join(codigo_p) if codigo_p else "PUSH X"

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

def procesar_expresion(expresion, opciones, numero_expresion):
    try:
        if '=' in expresion:
            expresion = expresion.split('=', 1)[1].strip()
        
        verificar_errores(expresion)
        
        postfijo = infijo_a_postfijo(expresion)
        prefijo = infijo_a_prefijo(expresion)
        
        # Generar código intermedio ORIGINAL
        codigo_intermedio, _ = postfijo_a_codigo_intermedio(postfijo)
        codigo_intermedio = [' '.join(inst) if isinstance(inst, list) else inst for inst in codigo_intermedio]
        
        # Asegurar asignación final si no existe
        if not any(inst.startswith('X =') for inst in codigo_intermedio):
            ultimo_temp = codigo_intermedio[-1].split('=')[0].strip()
            codigo_intermedio.append(f"X = {ultimo_temp}")
        
        # Optimizar el código intermedio
        codigo_intermedio_opt = optimizar_codigo_completo(codigo_intermedio)
        
        # Extraer definiciones para código P
        definitions = []
        resultado_final = None
        for instr in codigo_intermedio_opt:
            partes = instr.split()
            if len(partes) == 5 and partes[1] == '=':  # T0 = a + b
                definitions.append((partes[0], partes[3], partes[2], partes[4]))
            elif len(partes) == 3 and partes[0] == 'X':
                resultado_final = partes[2]  # Guardar el resultado final (X = ...)
        
        # Generar representaciones
        resultados = []
        
        # Calcular métricas comparativas
        metricas = calcular_metricas(codigo_intermedio, codigo_intermedio_opt)
        resultados.append(generar_tabla_comparativa(expresion, metricas))
        
        if '1' in opciones or '5' in opciones:
            resultados.append("\n📌 Notaciones:")
            resultados.append(f"🔹 Prefija: {' '.join(prefijo)}")
            resultados.append(f"🔹 Postfija: {' '.join(postfijo)}")

            resultados.append("\n📌 Código Intermedio:")
            resultados.append("ORIGINAL:")
            resultados.extend(codigo_intermedio)
            resultados.append("\nOPTIMIZADO:")
            resultados.extend(codigo_intermedio_opt)
        
        if '2' in opciones or '5' in opciones:
            resultados.append("\n📌 Código P:")
            resultados.append("ORIGINAL (desde infijo):")
            resultados.append(infijo_a_codigo_p(expresion))
            
            resultados.append("\nOPTIMIZADO (desde código intermedio optimizado):")
            codigo_p_opt = generar_codigo_p_optimizado(definitions, resultado_final)
            resultados.extend(codigo_p_opt.split('\n'))

        
        if '3' in opciones or '5' in opciones:
            resultados.append("\n📌 Triplos:")
            resultados.append("ORIGINAL:")
            resultados.extend(generar_triplos(codigo_intermedio))
            resultados.append("\nOPTIMIZADO:")
            resultados.extend(generar_triplos(codigo_intermedio_opt))
        
        if '4' in opciones or '5' in opciones:
            resultados.append("\n📌 Cuádruplos:")
            resultados.append("ORIGINAL:")
            resultados.extend(generar_cuadruplos(codigo_intermedio))
            resultados.append("\nOPTIMIZADO:")
            resultados.extend(generar_cuadruplos(codigo_intermedio_opt))
        
        return resultados
    except ValueError as e:
        return [f"❌ Error al procesar la expresión: {e}"]

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
    ruta_entrada = "datos.txt"
    expresiones = cargar_expresiones_desde_archivo(ruta_entrada)
    
    if not expresiones:
        print("No hay expresiones para procesar.")
        return
    
    tabla_simbolos = construir_tabla_simbolos(expresiones)
    
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
import ply.lex as lex
import math

# Lista de tokens, incluyendo las funciones matemáticas nuevas
tokens = [
    'DECIMALITO', 'ENTEROTE', 'TEXTITO', 'LOGIQUITO', 'IDENTIFICADOR', 'NUMEROTE',
    'SUMITA', 'RESTA', 'MULTIPLICA', 'DIVIDE', 'IGUALA',
    'PARENT_IZQ', 'PARENT_DER', 'POTENCIA', 'MODULO', 'RAIZ',
    'MAYORQUE', 'MENORQUE', 'MAYOROIGUAL', 'MENOROIGUAL',
    'IGUALAQUE', 'DIFERENTEQUE',
    'TODOS', 'ALGUNO', 'NEGACION', 'CIERTO', 'FALSO',
    'ESCRIBIR', 'LEER',
    'SENO', 'COSENO', 'TANGENTE', 'ARCO',
    'LOGARITMO_NATURAL', 'LOGARITMO_10',
    'ELEVADO', 'ALEATORIO', 'RAD_A_GRADOS', 'MOSTRAR_TABLA'
]

# Palabras reservadas, añadiendo las funciones nuevas. Este diccionario asocia palabras clave del lenguaje
reserved = {
    'decimalito': 'DECIMALITO',
    'enterote': 'ENTEROTE',
    'textito': 'TEXTITO',
    'logiquito': 'LOGIQUITO',
    'todos': 'TODOS',
    'alguno': 'ALGUNO',
    'negacion': 'NEGACION',
    'cierto': 'CIERTO',
    'falso': 'FALSO',
    'raiz': 'RAIZ',
    'escribir': 'ESCRIBIR',
    'leer': 'LEER',
    'seno': 'SENO',
    'coseno': 'COSENO',
    'tangente': 'TANGENTE',
    'arco': 'ARCO',
    'logaritmo_natural': 'LOGARITMO_NATURAL',
    'logaritmo_10': 'LOGARITMO_10',
    'elevado': 'ELEVADO',
    'aleatorio': 'ALEATORIO',
    'rad_a_grados': 'RAD_A_GRADOS',
    'mostrar_tabla': 'MOSTRAR_TABLA'
}

# Expresiones regulares para tokens de operadores y símbolos. Define una expresión regular que corresponde a un operador o símbolo 
t_IGUALA = r'='
t_SUMITA = r'\+'
t_RESTA = r'-'
t_MULTIPLICA = r'\*'
t_DIVIDE = r'/'
t_PARENT_IZQ = r'\('
t_PARENT_DER = r'\)'
t_POTENCIA = r'\^'
t_MODULO = r'%'
t_MAYORQUE = r'>'
t_MENORQUE = r'<'
t_MAYOROIGUAL = r'>='
t_MENOROIGUAL = r'<='
t_IGUALAQUE = r'=='
t_DIFERENTEQUE = r'!='
t_ignore = ' \t'

# Regla para reconocer cadenas (entre comillas dobles)
def t_TEXTITO(t):
    r'"(?:[^"\\]|\\.)*"'
    try:
        t.value = bytes(t.value[1:-1], "utf-8").decode("unicode_escape")  # Manejo correcto de escapes
    except UnicodeDecodeError:
        print(f"Error: Secuencia de escape mal formada en '{t.value}'")
        t.lexer.skip(len(t.value))
        return None
    return t

# Identificador de variables y funciones
def t_IDENTIFICADOR(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'IDENTIFICADOR')  # Verificar palabras reservadas
    return t

# Números (enteros y flotantes)
def t_NUMEROTE(t):
    r'\d+(\.\d+)?([eE][-+]?\d+)?'
    if t.value.count('.') > 1 or t.value.startswith('.') or t.value.startswith('e') or t.value.startswith('E'):
        print(f"Error: Número mal formado '{t.value}'")
        t.lexer.skip(len(t.value))
    else:
        t.value = float(t.value) if '.' in t.value or 'e' in t.value or 'E' in t.value else int(t.value)
        return t

# Lista global para almacenar errores
errores_lexer = []

def t_error(t):
    """
    Maneja caracteres ilegales y los almacena en la lista de errores.
    """
    errores_lexer.append(f"Caracter ilegal '{t.value[0]}' en línea {t.lineno}, columna {t.lexpos}")
    t.lexer.skip(1)

#Manejo para contar lineas correctamente
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def tokenize(expresion):
    """
    Tokeniza una expresión utilizando el lexer.
    """
    lexer.input(expresion)  # Proporciona la expresión al lexer
    tokens = []
    while True:
        tok = lexer.token()  # Obtén el siguiente token
        if not tok:
            break  # No hay más tokens
        tokens.append((tok.type, tok.value))  # Almacena el tipo y valor del token
    return tokens

# Construir el lexer
lexer = lex.lex()
## Objetivo
1. Dejar las gráficas más interactivas y estéticas (sin Plotly): pan/zoom embebido, hover con raíz y vértices, botón "Expandir".
2. Mantener la vista actual al cambiar intervalos.
3. Corregir el error de evaluación ("cos no está definido") asegurando soporte robusto de funciones como cos/sin/tan/exp/log/sqrt.

## Cambios Propuestos
### Interactividad en Bisección y Falsa Posición
- Insertar `NavigationToolbar2Tk` en los canvases embebidos para pan/zoom.
- Añadir anotaciones de hover en cada `Axes` que:
  - muestren texto "raíz ≈ ..." al acercar el puntero al punto de raíz calculada.
  - muestren "vértice (x, y)" al acercar el puntero a los extremos locales detectados.
- Detectar vértices por cambios de signo en la derivada numérica (`np.gradient`).
- Añadir botón "⤢ Expandir" debajo de cada gráfica (alineado a la derecha) que abre una ventana grande conservando la vista actual.

### Persistencia de Vista
- Antes de limpiar y re-graficar: capturar `prev_xlim`/`prev_ylim`.
- Tras trazar: restaurar límites si ya hubo una primera inicialización, evitando que un cambio de intervalo altere la vista del usuario.
- Aplicar en ambas pestañas.

### Corrección de Evaluación de Funciones
- Revisar `math_utils.evaluate_function(...)` y `evaluate_function_vectorized(...)`:
  - Forzar preprocesado y prefijo de `math.` para todas las funciones conocidas incluso en casos con espacios: `cos (x)` y similares.
  - Confirmar que `cos(x)-x^2` transforma a `math.cos(x)-x**2` (escalares) y a `np.cos(x)-x**2` (vectorizado).
  - Ajustar el reemplazo de `e^...` y símbolos (`π`, `pi`) y multiplications implícitas para que no queden tokens sueltos (`cos`) sin prefijo.
- En los métodos de cálculo de raíz, guardar `self.calculated_root` y `self.calculated_func_str` también para Falsa Posición, de modo que aparezca marcador/hover.

## Verificación
- Ejecutar `CalculadoraAlgebra.py`.
- En "Falsa Posición": introducir `cos(x)-x^2` y graficar.
  - La barra de herramientas debe permitir pan/zoom.
  - Al pasar el puntero por la cúspide o por la raíz, debe mostrar la anotación.
  - Cambiar `a`/`b` y re-graficar: los límites deben permanecer.
  - Pulsar "⤢ Expandir": se abre una ventana mayor conservando `xlim`/`ylim`.
- Repetir en "Bisección".

## Consideraciones
- No hay dependencias de Plotly en el repo; no se añaden librerías externas.
- Todos los cambios siguen el estilo y colores existentes.
- Seguridad: la evaluación usa AST y entorno limitado para `eval`.

¿Confirmas que aplique estos cambios en el código ahora?
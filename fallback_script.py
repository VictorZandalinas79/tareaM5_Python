
import matplotlib.pyplot as plt
import numpy as np

# Datos de ejemplo para Arsenal vs Real Madrid
categorias = ['Posesión (%)', 'Tiros', 'Tiros a puerta', 'Corners', 'Faltas']
arsenal = [58, 15, 7, 8, 10]
madrid = [42, 13, 6, 5, 12]

# Crear figura con tamaño adecuado
plt.figure(figsize=(12, 6))

# Crear barras
bar_width = 0.35
x = np.arange(len(categorias))
plt.bar(x - bar_width/2, arsenal, bar_width, label='Arsenal', color='red')
plt.bar(x + bar_width/2, madrid, bar_width, label='Real Madrid', color='blue')

# Añadir etiquetas y título
plt.xlabel('Categorías')
plt.ylabel('Valores')
plt.title('Estadísticas Arsenal vs Real Madrid - Champions League 24/25', fontsize=16)
plt.xticks(x, categorias)
plt.legend()

# Añadir valores sobre las barras
for i, v in enumerate(arsenal):
    plt.text(i - bar_width/2, v + 0.5, str(v), ha='center')
for i, v in enumerate(madrid):
    plt.text(i + bar_width/2, v + 0.5, str(v), ha='center')

# Ajustar diseño y guardar
plt.tight_layout()
plt.savefig('fallback_plot.png', dpi=150)

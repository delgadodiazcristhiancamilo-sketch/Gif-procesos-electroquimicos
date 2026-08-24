"""
===============================================================================
ANIMACIÓN DIDÁCTICA Y CIENTÍFICA DE CELDA ELECTROQUÍMICA Y DOBLE CAPA ELÉCTRICA
===============================================================================
Este script en Python genera una animación (GIF y MP4) de una celda electroquímica 
completa a escala macroscópica y microscópica.

Modificaciones aplicadas:
1. Duración extendida a 20.0 segundos para alargar el tiempo disponible en cada fase.
2. Transiciones entre fases fuertemente marcadas visualmente con cambios distintivos 
   de color en el banner de fase y flashes de transición.

Autor: Asistente Antigravity AI (Google DeepMind)
===============================================================================
"""

import os
import sys
import time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
from PIL import Image
import imageio

# =============================================================================
# PARÁMETROS CONFIGURABLES
# =============================================================================
CONFIG = {
    'N_A': 40,                     # Cantidad inicial de especies A (Ox - Naranja)
    'N_B': 40,                     # Cantidad inicial de especies B (Red - Azul)
    'N_cationes': 30,              # Cantidad de cationes M+ (Verde)
    'N_aniones': 30,               # Cantidad de aniones X- (Morado)
    'velocidad_electrones': 0.35,  # Velocidad suave de e- en el circuito
    'velocidad_iones': 0.08,       # Velocidad de migración iónica hacia electrodos
    'coeficiente_difusion': 0.04,  # Intensidad del movimiento browniano / difusión
    'velocidad_reaccion': 0.15,    # Probabilidad de transferencia e- en interfaz
    'potencial_aplicado': 1.23,    # Potencial conceptual aplicado (E_app)
    'duracion': 20.0,              # Duración total extendida en segundos (Fases alargadas)
    'fps': 20,                     # Cuadros por segundo
    'distancia_electrodos': 7.4    # Distancia en X entre Ánodo (3.3) y Cátodo (10.7)
}


class ElectrochemicalCellSimulation:
    def __init__(self, config=CONFIG):
        self.cfg = config
        self.fps = config['fps']
        self.duracion = config['duracion']
        self.total_frames = int(self.fps * self.duracion)
        
        # Geometría del espacio de solución electrolítica
        self.x_anode = 3.3
        self.x_cathode = 10.7
        self.y_sol_min = 1.8
        self.y_sol_max = 5.1
        self.x_sol_min = 3.35
        self.x_sol_max = 10.65
        
        # Generar partículas iniciales
        self.particulas = self.generar_particulas()
        
        # Destellos en la interfaz
        self.flashes_interface = []
        
        # Eje X para concentraciones
        self.perfil_x = np.linspace(3.4, 10.6, 30)
        
    def generar_particulas(self):
        """
        Inicializa las posiciones y tipos de partículas en la solución electrolítica.
        Tipos:
          0: Especie A (Ox, Naranja)
          1: Especie B (Red, Azul)
          2: Catión M+ (Verde)
          3: Anión X- (Morado)
        """
        np.random.seed(42)  # Semilla reproducible
        particulas = []
        
        # Distribuir A (Ox)
        for _ in range(self.cfg['N_A']):
            x = np.random.uniform(self.x_sol_min + 0.2, self.x_sol_max - 0.2)
            y = np.random.uniform(self.y_sol_min + 0.2, self.y_sol_max - 0.2)
            particulas.append({'tipo': 0, 'x': x, 'y': y, 'vx': 0.0, 'vy': 0.0})
            
        # Distribuir B (Red)
        for _ in range(self.cfg['N_B']):
            x = np.random.uniform(self.x_sol_min + 0.2, self.x_sol_max - 0.2)
            y = np.random.uniform(self.y_sol_min + 0.2, self.y_sol_max - 0.2)
            particulas.append({'tipo': 1, 'x': x, 'y': y, 'vx': 0.0, 'vy': 0.0})
            
        # Distribuir M+
        for _ in range(self.cfg['N_cationes']):
            x = np.random.uniform(self.x_sol_min + 0.2, self.x_sol_max - 0.2)
            y = np.random.uniform(self.y_sol_min + 0.2, self.y_sol_max - 0.2)
            particulas.append({'tipo': 2, 'x': x, 'y': y, 'vx': 0.0, 'vy': 0.0})
            
        # Distribuir X-
        for _ in range(self.cfg['N_aniones']):
            x = np.random.uniform(self.x_sol_min + 0.2, self.x_sol_max - 0.2)
            y = np.random.uniform(self.y_sol_min + 0.2, self.y_sol_max - 0.2)
            particulas.append({'tipo': 3, 'x': x, 'y': y, 'vx': 0.0, 'vy': 0.0})
            
        return particulas

    def obtener_fase_y_tiempo(self, frame):
        """
        Retorna el tiempo actual t y la fase de la animación (1 a 6).
        Tiempos extendidos por fase (Total = 20 s):
          Fase 1: 0.0 - 3.0 s  (3.0 s) -> Estado Inicial
          Fase 2: 3.0 - 6.0 s  (3.0 s) -> Aplicación de Potencial ΔE
          Fase 3: 6.0 - 9.0 s  (3.0 s) -> Doble Capa Eléctrica
          Fase 4: 9.0 - 13.0 s (4.0 s) -> Transferencia Electrónica Interfacial
          Fase 5: 13.0 - 17.0 s(4.0 s) -> Gradientes de Concentración y Difusión
          Fase 6: 17.0 - 20.0 s(3.0 s) -> Estado Estacionario Conceptual
        """
        t = frame / self.fps
        if t < 3.0:
            fase = 1
        elif t < 6.0:
            fase = 2
        elif t < 9.0:
            fase = 3
        elif t < 13.0:
            fase = 4
        elif t < 17.0:
            fase = 5
        else:
            fase = 6
        return t, fase

    def mover_particulas(self, fase):
        """Actualiza las posiciones de las partículas en la solución."""
        D = self.cfg['coeficiente_difusion']
        v_ion = self.cfg['velocidad_iones']
        
        migracion_activa = (fase >= 2)
        difusion_gradiente_activa = (fase >= 5)
        
        for p in self.particulas:
            # 1. Movimiento browniano aleatorio
            dx = np.random.normal(0, D)
            dy = np.random.normal(0, D)
            
            # 2. Migración iónica por campo eléctrico (Fases >= 2)
            if migracion_activa:
                if p['tipo'] == 3:  # Anión X- (migra hacia Ánodo, izquierda)
                    if p['x'] > self.x_anode + 0.4:
                        dx -= v_ion
                    elif p['x'] < self.x_anode + 0.35:
                        dx += v_ion * 0.2
                elif p['tipo'] == 2:  # Catión M+ (migra hacia Cátodo, derecha)
                    if p['x'] < self.x_cathode - 0.4:
                        dx += v_ion
                    elif p['x'] > self.x_cathode - 0.35:
                        dx -= v_ion * 0.2

            # 3. Transporte por gradientes de concentración (Fases >= 5)
            if difusion_gradiente_activa:
                if p['tipo'] == 1:  # Especie B (Red) se consume en Ánodo (izq)
                    if p['x'] > self.x_anode + 0.4 and p['x'] < self.x_cathode - 2.5:
                        dx -= 0.02
                elif p['tipo'] == 0:  # Especie A (Ox) se genera en Ánodo, difunde a seno
                    if p['x'] < self.x_anode + 3.0:
                        dx += 0.02
                    elif p['x'] > self.x_cathode - 3.0:  # Especie A se consume en Cátodo
                        dx += 0.02
                if p['tipo'] == 1 and p['x'] > self.x_cathode - 3.0:  # Especie B se genera en Cátodo
                    dx -= 0.02

            # Límites del recipiente
            new_x = p['x'] + dx
            new_y = p['y'] + dy
            
            min_x_bound = self.x_anode + 0.15
            max_x_bound = self.x_cathode - 0.15
            if new_x < min_x_bound:
                new_x = min_x_bound + (min_x_bound - new_x) * 0.5
            elif new_x > max_x_bound:
                new_x = max_x_bound - (new_x - max_x_bound) * 0.5
                
            min_y_bound = self.y_sol_min + 0.15
            max_y_bound = self.y_sol_max - 0.15
            if new_y < min_y_bound:
                new_y = min_y_bound + (min_y_bound - new_y) * 0.5
            elif new_y > max_y_bound:
                new_y = max_y_bound - (max_y_bound - new_y) * 0.5
                
            p['x'] = new_x
            p['y'] = new_y

    def aplicar_potencial(self, fase):
        """Maneja el estado del generador."""
        if fase == 1:
            estado_gen = "OFF"
            activo = False
        else:
            estado_gen = "ΔE aplicado"
            activo = True
        return estado_gen, activo

    def generar_doble_capa(self, fase):
        """Indica si la doble capa eléctrica está desarrollada."""
        return fase >= 3

    def realizar_transferencia_electronica(self, fase):
        """
        Simula las reacciones redox interfaciales.
        Ánodo: B -> A + e-
        Cátodo: A + e- -> B
        """
        if fase < 4:
            return
            
        prob_rx = self.cfg['velocidad_reaccion']
        
        self.flashes_interface = [f for f in self.flashes_interface if f['life'] > 0]
        for f in self.flashes_interface:
            f['life'] -= 1

        for p in self.particulas:
            # Ánodo: B (tipo 1) -> A (tipo 0) + e-
            if p['tipo'] == 1 and p['x'] <= self.x_anode + 0.65:
                if np.random.rand() < prob_rx:
                    p['tipo'] = 0  # B se transforma en A
                    self.flashes_interface.append({'x': self.x_anode, 'y': p['y'], 'color': 'gold', 'life': 4})
                    
            # Cátodo: A (tipo 0) + e- -> B (tipo 1)
            elif p['tipo'] == 0 and p['x'] >= self.x_cathode - 0.65:
                if np.random.rand() < prob_rx:
                    p['tipo'] = 1  # A se transforma en B
                    self.flashes_interface.append({'x': self.x_cathode, 'y': p['y'], 'color': 'cyan', 'life': 4})

    def actualizar_concentraciones(self):
        """Calcula perfiles de concentración."""
        pos_A = [p['x'] for p in self.particulas if p['tipo'] == 0]
        pos_B = [p['x'] for p in self.particulas if p['tipo'] == 1]
        
        hist_A, _ = np.histogram(pos_A, bins=self.perfil_x)
        hist_B, _ = np.histogram(pos_B, bins=self.perfil_x)
        
        hist_A = np.convolve(hist_A, [0.25, 0.5, 0.25], mode='same')
        hist_B = np.convolve(hist_B, [0.25, 0.5, 0.25], mode='same')
        return hist_A, hist_B

    def simular_difusion(self, fase):
        """Implementada en mover_particulas."""
        pass

    def dibujar_circuito(self, ax, fase, t, estado_gen):
        """
        Dibuja el generador y los instrumentos de medición con electrones en movimiento.
        """
        # 1. Generador
        color_gen = '#27AE60' if fase >= 2 else '#BDC3C7'
        rect_gen = patches.FancyBboxPatch((5.4, 7.75), 3.2, 0.80,
                                          boxstyle="round,pad=0.08",
                                          facecolor=color_gen,
                                          edgecolor='black', linewidth=2.0, zorder=4)
        ax.add_patch(rect_gen)
        ax.text(7.0, 8.28, "GENERADOR / FUENTE", color='white', weight='bold', fontsize=10, ha='center', va='center', zorder=5)
        ax.text(7.0, 7.98, estado_gen, color='white', weight='bold', fontsize=11, ha='center', va='center', zorder=5)

        # 2. Cables del circuito externo
        path_left = [(2.9, 5.8), (2.9, 8.15), (5.4, 8.15)]
        path_right = [(8.6, 8.15), (11.1, 8.15), (11.1, 5.8)]
        
        for path in [path_left, path_right]:
            xs, ys = zip(*path)
            ax.plot(xs, ys, color='#2C3E50', linewidth=3.5, zorder=3)

        # 3. Instrumentos de Medición (sin agujas/flechas)
        circle_mA = patches.Circle((2.9, 7.15), 0.38, facecolor='white', edgecolor='#2C3E50', linewidth=2.0, zorder=5)
        ax.add_patch(circle_mA)
        ax.text(2.9, 7.15, "mA", fontsize=11, weight='bold', color='#C0392B', ha='center', va='center', zorder=6)

        ax.plot([2.9, 11.1], [6.60, 6.60], color='#7F8C8D', linestyle='--', linewidth=1.8, zorder=3)
        circle_mV = patches.Circle((7.0, 6.60), 0.38, facecolor='white', edgecolor='#2C3E50', linewidth=2.0, zorder=5)
        ax.add_patch(circle_mV)
        ax.text(7.0, 6.60, "mV", fontsize=11, weight='bold', color='#2980B9', ha='center', va='center', zorder=6)

        # 4. Electrones e- desplazándose lentamente por el circuito externo (Fases >= 2)
        if fase >= 2:
            num_e = 10
            offset = (t * self.cfg['velocidad_electrones'] * 0.18) % 1.0
            
            for i in range(num_e):
                pos = (i / num_e + offset) % 1.0
                dist = pos * 12.9
                
                if dist < 2.35:  # Subiendo por cable izquierdo
                    ex = 2.9
                    ey = 5.8 + dist
                elif dist < 10.55:  # Cruzando de izquierda a derecha por el generador
                    ex = 2.9 + (dist - 2.35)
                    ey = 8.15
                else:  # Bajando por cable derecho hacia el cátodo
                    ex = 11.1
                    ey = 8.15 - (dist - 10.55)
                    
                circle_e = patches.Circle((ex, ey), 0.13, facecolor='#E74C3C', edgecolor='darkred', linewidth=1.2, zorder=7)
                ax.add_patch(circle_e)
                ax.text(ex, ey + 0.24, "e⁻", color='#E74C3C', weight='bold', fontsize=8.5, ha='center', va='center', zorder=8)
                
            # Flechas del flujo de electrones e-
            ax.annotate('', xy=(2.9, 7.65), xytext=(2.9, 7.35),
                        arrowprops=dict(arrowstyle="->", color='#E74C3C', lw=2.5), zorder=6)
            ax.annotate('', xy=(4.5, 8.15), xytext=(4.0, 8.15),
                        arrowprops=dict(arrowstyle="->", color='#E74C3C', lw=2.5), zorder=6)
            ax.annotate('', xy=(9.5, 8.15), xytext=(9.0, 8.15),
                        arrowprops=dict(arrowstyle="->", color='#E74C3C', lw=2.5), zorder=6)
            ax.annotate('', xy=(11.1, 6.0), xytext=(11.1, 6.2),
                        arrowprops=dict(arrowstyle="->", color='#E74C3C', lw=2.5), zorder=6)

    def generar_frame(self, frame):
        """Genera un único cuadro de la animación y retorna la figura de Matplotlib."""
        t, fase = self.obtener_fase_y_tiempo(frame)
        
        self.mover_particulas(fase)
        self.realizar_transferencia_electronica(fase)
        estado_gen, activo = self.aplicar_potencial(fase)
        edl_formada = self.generar_doble_capa(fase)
        
        fig, ax = plt.subplots(figsize=(14, 9.8), dpi=100)
        ax.set_xlim(0, 14)
        ax.set_ylim(0, 9.8)
        ax.axis('off')
        
        fig.patch.set_facecolor('white')
        
        # Configuración visual distintiva por Fase (Colores de Banner marcados para cada Fase)
        estilos_fase = {
            1: ("FASE 1 — ESTADO INICIAL",
                "Generador OFF | Distribución homogénea de A (Ox) y B (Red) | Iones M⁺/X⁻ aleatorios | Sin doble capa",
                '#EAECEE', '#B2BABB', '#2C3E50'),
            2: ("FASE 2 — APLICACIÓN DE POTENCIAL ΔE",
                "Generador ON (ΔE aplicado) | Se establece campo eléctrico | Inicio del flujo de electrones e⁻ por circuito externo",
                '#FEF9E7', '#F1C40F', '#7D6608'),
            3: ("FASE 3 — FORMACIÓN DE LA DOBLE CAPA ELÉCTRICA",
                "Migración iónica: Aniones X⁻ → Ánodo (+) | Cationes M⁺ → Cátodo (-) | Formación de Doble Capa Eléctrica",
                '#EBF5FB', '#3498DB', '#1B4F72'),
            4: ("FASE 4 — TRANSFERENCIA ELECTRÓNICA INTERFACIAL",
                "Ánodo (Oxidación): B → A + e⁻ | Cátodo (Reducción): A + e⁻ → B | Los e⁻ cruzan únicamente la interfaz electrodo-solución",
                '#FDEDEC', '#E74C3C', '#78281F'),
            5: ("FASE 5 — GRADIENTES DE CONCENTRACIÓN Y DIFUSIÓN",
                "Consumo y generación de especies en la superficie induce gradientes | Difusión desde/hacia el seno de la solución",
                '#FBF2E9', '#E67E22', '#6E2C00'),
            6: ("FASE 6 — ESTADO ESTACIONARIO CONCEPTUAL",
                "Operación electroquímica continua: Circuito externo activo, Doble Capa estable, Transferencia e⁻ y Difusión sostenidas",
                '#EAFAF1', '#2ECC71', '#145A32')
        }
        
        titulo_f, desc_f, bg_color, border_color, text_color = estilos_fase[fase]
        
        # Banner de fase con color distintivo bien marcado
        banner_bg = patches.Rectangle((0.5, 8.85), 13.0, 0.75, facecolor=bg_color, edgecolor=border_color, linewidth=2.2, zorder=2)
        ax.add_patch(banner_bg)
        ax.text(7.0, 9.35, titulo_f, fontsize=12, weight='bold', color=text_color, ha='center', va='center', zorder=3)
        ax.text(7.0, 9.05, desc_f, fontsize=9.5, color='#2C3E50', ha='center', va='center', zorder=3)

        # CIRCUITO Y GENERADOR
        self.dibujar_circuito(ax, fase, t, estado_gen)

        # TANQUE / BEAKER Y SOLUCIÓN
        beaker_path = Path([(2.0, 5.3), (2.0, 1.6), (12.0, 1.6), (12.0, 5.3)])
        beaker_patch = patches.PathPatch(beaker_path, facecolor='#EBF5FB', edgecolor='#2980B9', linewidth=2.5, zorder=1)
        ax.add_patch(beaker_patch)
        
        ax.plot([2.0, 12.0], [5.0, 5.0], color='#3498DB', linestyle='-', linewidth=2.0, alpha=0.7, zorder=2)
        ax.text(1.8, 5.0, "Solución\nElectrolítica", fontsize=8.5, color='#2980B9', ha='right', va='center')

        # ELECTRODOS (ÁNODO Y CÁTODO)
        rect_anode = patches.Rectangle((2.5, 1.8), 0.8, 4.0, facecolor='#95A5A6', edgecolor='#2C3E50', linewidth=2.0, zorder=3)
        ax.add_patch(rect_anode)
        ax.text(2.9, 3.8, "ÁNODO\n(Oxidación)", fontsize=9.5, weight='bold', color='white', ha='center', va='center', rotation=90, zorder=4)
        
        signo_anode = "(+)" if activo else "(0)"
        ax.text(2.9, 5.5, signo_anode, fontsize=11.5, weight='bold', color='#C0392B' if activo else '#7F8C8D', ha='center', va='center', zorder=4)

        rect_cathode = patches.Rectangle((10.7, 1.8), 0.8, 4.0, facecolor='#7F8C8D', edgecolor='#2C3E50', linewidth=2.0, zorder=3)
        ax.add_patch(rect_cathode)
        ax.text(11.1, 3.8, "CÁTODO\n(Reducción)", fontsize=9.5, weight='bold', color='white', ha='center', va='center', rotation=90, zorder=4)
        
        signo_cathode = "(−)" if activo else "(0)"
        ax.text(11.1, 5.5, signo_cathode, fontsize=11.5, weight='bold', color='#2980B9' if activo else '#7F8C8D', ha='center', va='center', zorder=4)

        # Doble Capa Eléctrica (EDL)
        if edl_formada:
            rect_edl_anode = patches.Rectangle((3.3, 1.65), 0.45, 3.6, facecolor='#FADBD8', alpha=0.4, linestyle='--', edgecolor='#E74C3C', linewidth=1.5, zorder=2)
            ax.add_patch(rect_edl_anode)
            ax.annotate("DOBLE CAPA\nELÉCTRICA", xy=(3.5, 4.5), xytext=(4.3, 5.3),
                        arrowprops=dict(arrowstyle="->", color='#C0392B', lw=1.8),
                        fontsize=8.5, weight='bold', color='#C0392B', ha='center', zorder=6)

            rect_edl_cathode = patches.Rectangle((10.25, 1.65), 0.45, 3.6, facecolor='#D4E6F1', alpha=0.4, linestyle='--', edgecolor='#3498DB', linewidth=1.5, zorder=2)
            ax.add_patch(rect_edl_cathode)
            ax.annotate("DOBLE CAPA\nELÉCTRICA", xy=(10.45, 4.5), xytext=(9.7, 5.3),
                        arrowprops=dict(arrowstyle="->", color='#2980B9', lw=1.8),
                        fontsize=8.5, weight='bold', color='#2980B9', ha='center', zorder=6)

        ax.text(7.0, 4.7, "SENO DE LA SOLUCIÓN (BULK)", fontsize=9, weight='bold', color='#5D6D7E', ha='center', va='center')
        if fase >= 5:
            ax.text(4.6, 4.6, "Capa de Difusión\n(Ánodo)", fontsize=8, color='#D35400', ha='center', va='center', style='italic')
            ax.text(9.4, 4.6, "Capa de Difusión\n(Cátodo)", fontsize=8, color='#2980B9', ha='center', va='center', style='italic')

        # DIBUJO DE PARTÍCULAS EN LA SOLUCIÓN
        for p in self.particulas:
            px, py = p['x'], p['y']
            
            if p['tipo'] == 0:  # A (Ox - Naranja)
                circle = patches.Circle((px, py), 0.16, facecolor='#FF7F0E', edgecolor='black', linewidth=1.0, zorder=5)
                ax.add_patch(circle)
                ax.text(px, py, "A", fontsize=7.5, weight='bold', color='white', ha='center', va='center', zorder=6)
                
            elif p['tipo'] == 1:  # B (Red - Azul)
                circle = patches.Circle((px, py), 0.16, facecolor='#1F77B4', edgecolor='black', linewidth=1.0, zorder=5)
                ax.add_patch(circle)
                ax.text(px, py, "B", fontsize=7.5, weight='bold', color='white', ha='center', va='center', zorder=6)
                
            elif p['tipo'] == 2:  # Catión M+ (Verde)
                circle = patches.Circle((px, py), 0.13, facecolor='#2CA02C', edgecolor='darkgreen', linewidth=1.0, zorder=5)
                ax.add_patch(circle)
                ax.text(px, py, "+", fontsize=9, weight='bold', color='white', ha='center', va='center', zorder=6)
                
            elif p['tipo'] == 3:  # Anión X- (Morado)
                circle = patches.Circle((px, py), 0.13, facecolor='#9467BD', edgecolor='indigo', linewidth=1.0, zorder=5)
                ax.add_patch(circle)
                ax.text(px, py, "−", fontsize=9, weight='bold', color='white', ha='center', va='center', zorder=6)

        for flash in self.flashes_interface:
            ring = patches.Circle((flash['x'], flash['y']), 0.35, facecolor='none', edgecolor=flash['color'], linewidth=2.5, alpha=0.8, zorder=6)
            ax.add_patch(ring)

        # RECUADROS DE ECUACIONES DE ÁNODO Y CÁTODO
        ax.text(2.9, 1.05, "ÁNODO (OXIDACIÓN)\nB  →  A + e⁻", fontsize=9.5, weight='bold', color='#C0392B', ha='center', va='center',
                bbox=dict(boxstyle="round,pad=0.35", facecolor='#FDEDEC', edgecolor='#C0392B', lw=1.5))
        ax.text(11.1, 1.05, "CÁTODO (REDUCCIÓN)\nA + e⁻  →  B", fontsize=9.5, weight='bold', color='#2980B9', ha='center', va='center',
                bbox=dict(boxstyle="round,pad=0.35", facecolor='#EBF5FB', edgecolor='#2980B9', lw=1.5))

        # LEYENDA DE PARTÍCULAS
        legend_elements = [
            patches.Patch(facecolor='#FF7F0E', edgecolor='black', label='A: Especie Oxidada (Ox)'),
            patches.Patch(facecolor='#1F77B4', edgecolor='black', label='B: Especie Reducida (Red)'),
            patches.Patch(facecolor='#2CA02C', edgecolor='darkgreen', label='M⁺: Catión (Electrolito)'),
            patches.Patch(facecolor='#9467BD', edgecolor='indigo', label='X⁻: Anión (Electrolito)'),
            patches.Patch(facecolor='#E74C3C', edgecolor='darkred', label='e⁻: Electrón (Circuito Externo)')
        ]
        ax.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, 0.01),
                  fontsize=8.5, frameon=True, facecolor='white', edgecolor='#BDC3C7', title="Leyenda de Partículas", ncol=5)

        plt.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.01)
        return fig


def generar_frames(sim, output_dir='frames_temp'):
    """Genera todos los cuadros de la animación y los guarda como imágenes PNG."""
    os.makedirs(output_dir, exist_ok=True)
    frame_paths = []
    print(f"Generando {sim.total_frames} frames para {sim.duracion} s a {sim.fps} fps...", flush=True)
    
    start_time = time.time()
    for frame in range(sim.total_frames):
        fig = sim.generar_frame(frame)
        frame_path = os.path.join(output_dir, f"frame_{frame:04d}.png")
        fig.savefig(frame_path, dpi=100, bbox_inches='tight')
        plt.close(fig)
        frame_paths.append(frame_path)
        
        if (frame + 1) % 20 == 0 or frame == sim.total_frames - 1:
            elapsed = time.time() - start_time
            fps_calc = (frame + 1) / elapsed
            print(f"  Frame {frame+1}/{sim.total_frames} ({(frame+1)/sim.total_frames*100:.1f}%) - {fps_calc:.2f} fps", flush=True)
            
    return frame_paths


def exportar_gif(frame_paths, gif_filename='transferencia_electronica_doble_capa.gif', fps=20):
    """Convierte los cuadros guardados en un GIF animado optimizado."""
    print(f"Exportando GIF animado a '{gif_filename}'...", flush=True)
    images = []
    for path in frame_paths:
        img = Image.open(path)
        images.append(img.convert('P', palette=Image.ADAPTIVE))
        
    duration_ms = int(1000 / fps)
    images[0].save(
        gif_filename,
        save_all=True,
        append_images=images[1:],
        optimize=True,
        duration=duration_ms,
        loop=0
    )
    print(f"¡GIF generado exitosamente! Tamaño: {os.path.getsize(gif_filename)/1024/1024:.2f} MB", flush=True)


def exportar_mp4(frame_paths, mp4_filename='transferencia_electronica_doble_capa.mp4', fps=20):
    """Exporta la secuencia de imágenes a un archivo de video MP4 usando imageio/OpenCV."""
    print(f"Exportando video MP4 a '{mp4_filename}'...", flush=True)
    try:
        writer = imageio.get_writer(mp4_filename, fps=fps, codec='libx264', quality=8)
        for path in frame_paths:
            img = imageio.v2.imread(path)
            writer.append_data(img)
        writer.close()
        print(f"¡MP4 generado exitosamente! Tamaño: {os.path.getsize(mp4_filename)/1024/1024:.2f} MB", flush=True)
    except Exception as e:
        print(f"Advertencia: No se pudo usar imageio libx264 ({e}), intentando fallback con OpenCV...", flush=True)
        import cv2
        first_img = cv2.imread(frame_paths[0])
        height, width, _ = first_img.shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(mp4_filename, fourcc, fps, (width, height))
        for path in frame_paths:
            img = cv2.imread(path)
            out.write(img)
        out.release()
        print(f"¡MP4 generado con OpenCV! Tamaño: {os.path.getsize(mp4_filename)/1024/1024:.2f} MB", flush=True)


def main():
    print("=======================================================================", flush=True)
    print("INICIANDO SIMULACIÓN Y GENERACIÓN DE GIF DE CELDA ELECTROQUÍMICA", flush=True)
    print("=======================================================================", flush=True)
    
    sim = ElectrochemicalCellSimulation(CONFIG)
    frame_paths = generar_frames(sim)
    
    gif_out = 'transferencia_electronica_doble_capa.gif'
    mp4_out = 'transferencia_electronica_doble_capa.mp4'
    
    exportar_gif(frame_paths, gif_out, fps=CONFIG['fps'])
    exportar_mp4(frame_paths, mp4_out, fps=CONFIG['fps'])
    
    print("\nProceso completado con éxito.", flush=True)
    print(f"GIF guardado en: {os.path.abspath(gif_out)}", flush=True)
    print(f"MP4 guardado en: {os.path.abspath(mp4_out)}", flush=True)


if __name__ == '__main__':
    main()

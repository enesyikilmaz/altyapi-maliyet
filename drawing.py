"""Kanal kesitinin şematik matplotlib çizimi."""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patheffects as pe

from config import RENK_PALETI


def cizim_olustur(ic_cap_mm, dis_cap_m, derinlik, taban_genisligi, zemin_tipi):
    fig, ax = plt.subplots(figsize=(6, 8), facecolor=RENK_PALETI["arka_plan"])

    kum_h = 0.10 + dis_cap_m + 0.30

    if derinlik > 1.50:
        ust_genislik = taban_genisligi + 2 * (derinlik / 3)
        kum_ust_genislik = taban_genisligi + 2 * (kum_h / 3)
    else:
        ust_genislik = taban_genisligi
        kum_ust_genislik = taban_genisligi

    if "Sert Zemin" in zemin_tipi:
        dolgu_color = '#d3d3d3'
        dolgu_hatch = 'O'
        dolgu_label = "Kırmataş Geri Dolgu"
        zemin_cizgi = 'black'
        dolgu_text_color = RENK_PALETI["metin"]
    else:
        dolgu_color = RENK_PALETI["buton_hover"]
        dolgu_hatch = '+'
        dolgu_label = "Kazıdan Çıkan Toprak\n(Geri Dolgu)"
        zemin_cizgi = RENK_PALETI["metin"]
        dolgu_text_color = RENK_PALETI["metin"]

    dolgu_poly = patches.Polygon([
        (-kum_ust_genislik/2, kum_h), (kum_ust_genislik/2, kum_h),
        (ust_genislik/2, derinlik), (-ust_genislik/2, derinlik)
    ], closed=True, facecolor=dolgu_color, edgecolor=RENK_PALETI["metin"], hatch=dolgu_hatch, linewidth=1.5)
    ax.add_patch(dolgu_poly)

    yatak_poly = patches.Polygon([
        (-taban_genisligi/2, 0), (taban_genisligi/2, 0),
        (kum_ust_genislik/2, kum_h), (-kum_ust_genislik/2, kum_h)
    ], closed=True, facecolor=RENK_PALETI["sidebar"], edgecolor=RENK_PALETI["metin"], hatch='.', linewidth=1.5)
    ax.add_patch(yatak_poly)

    pipe_center_y = 0.10 + (dis_cap_m / 2)
    pipe_outer = patches.Circle((0, pipe_center_y), dis_cap_m/2, facecolor='#f0f0f0', edgecolor=RENK_PALETI["metin"], linewidth=2)
    pipe_inner = patches.Circle((0, pipe_center_y), (ic_cap_mm/2000), facecolor='white', edgecolor=RENK_PALETI["metin"], linewidth=1)
    ax.add_patch(pipe_outer)
    ax.add_patch(pipe_inner)

    ax.plot([-ust_genislik/2 - 0.5, ust_genislik/2 + 0.5], [derinlik, derinlik], color=zemin_cizgi, linewidth=3)

    beyaz_golge = [pe.withStroke(linewidth=4, foreground=RENK_PALETI["arka_plan"])]

    ax.text(0, derinlik + 0.15, zemin_tipi.upper(), ha='center', fontweight='bold', fontsize=12, color=zemin_cizgi)
    ax.text(0, pipe_center_y, f"Ø{ic_cap_mm}", ha='center', va='center', fontweight='bold', fontsize=11, color=RENK_PALETI["metin"], path_effects=beyaz_golge)

    yataklama_y_konumu = 0.10 + dis_cap_m + 0.15
    ax.text(0, yataklama_y_konumu, "Yataklama\n& Gömlekleme", ha='center', va='center', fontsize=10, fontweight='bold', color=RENK_PALETI["metin"], path_effects=beyaz_golge)

    dolgu_y_konumu = kum_h + (derinlik - kum_h)/2
    ax.text(0, dolgu_y_konumu, dolgu_label, ha='center', va='center', fontsize=11, fontweight='bold', color=dolgu_text_color, path_effects=beyaz_golge)

    ax.annotate('', xy=(-ust_genislik/2 - 0.2, 0), xytext=(-ust_genislik/2 - 0.2, derinlik), arrowprops=dict(arrowstyle='<->', color='red', lw=1.5))
    ax.text(-ust_genislik/2 - 0.3, derinlik/2, f"HT = {derinlik:.2f} m", va='center', ha='right', color='red', rotation=90, fontweight='bold', path_effects=beyaz_golge)

    ax.annotate('', xy=(-taban_genisligi/2, -0.15), xytext=(taban_genisligi/2, -0.15), arrowprops=dict(arrowstyle='<->', color='blue', lw=1.5))
    ax.text(0, -0.25, f"Taban = {taban_genisligi:.2f} m", ha='center', va='top', color='blue', fontweight='bold', path_effects=beyaz_golge)

    if derinlik > 1.50:
        ax.text(ust_genislik/2 + 0.1, derinlik/2, "1/3\nŞev", ha='left', va='center', color=RENK_PALETI["metin"], fontweight='bold', path_effects=beyaz_golge)

    ax.set_aspect('equal')
    ax.axis('off')
    ax.autoscale_view()

    return fig

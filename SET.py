import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import pyperclip
import os
import requests
from io import BytesIO
import threading
import time

# === Variáveis Globais ===
ultimo_link = None
imagem_atual = None

# === Conversão GPS ===
def converter_gps(dms, ref):
    if not dms or not ref:
        return None
    graus = dms[0][0] / dms[0][1]
    minutos = dms[1][0] / dms[1][1]
    segundos = dms[2][0] / dms[2][1]
    coordenada = graus + (minutos / 60.0) + (segundos / 3600.0)
    if ref in ['S', 'W']:
        coordenada = -coordenada
    return round(coordenada, 6)

# === EXIF Parser ===
def extrair_exif(imagem):
    try:
        exif_data = imagem._getexif()
        if not exif_data:
            return "[!] Nenhum dado EXIF encontrado.", None

        dados = {}
        for tag, valor in exif_data.items():
            tag_nome = TAGS.get(tag, tag)
            dados[tag_nome] = valor

        resultado = []
        link_maps = None

        if 'DateTimeOriginal' in dados:
            resultado.append(f"🗕️ Data e Hora: {dados['DateTimeOriginal']}")

        if 'Make' in dados:
            resultado.append(f"🏠 Fabricante: {dados['Make']}")

        if 'Model' in dados:
            resultado.append(f"📷 Modelo da Câmera: {dados['Model']}")

        if 'Software' in dados:
            resultado.append(f"💻 Software Usado: {dados['Software']}")

        if 'GPSInfo' in dados:
            gps_info = dados['GPSInfo']
            gps_dados = {}
            for chave in gps_info:
                nome_chave = GPSTAGS.get(chave, chave)
                gps_dados[nome_chave] = gps_info[chave]

            lat = converter_gps(gps_dados.get("GPSLatitude"), gps_dados.get("GPSLatitudeRef"))
            lon = converter_gps(gps_dados.get("GPSLongitude"), gps_dados.get("GPSLongitudeRef"))

            if lat and lon:
                link_maps = f"https://maps.google.com/?q={lat},{lon}"
                resultado.append(f"📍 Localização: {lat}, {lon}")
                resultado.append(f"🔗 Google Maps: {link_maps}")
            else:
                resultado.append("🌍 Dados de GPS incompletos.")

        return "\n".join(resultado), link_maps

    except Exception as e:
        return f"[ERRO] Falha ao processar imagem: {e}", None

# === Manipulação de Arquivo ===
def abrir_imagem_local():
    caminho = filedialog.askopenfilename(filetypes=[("Imagens", "*.jpg *.jpeg *.png")])
    if caminho:
        imagem = Image.open(caminho)
        processar(imagem, os.path.basename(caminho))

def abrir_imagem_url():
    url = campo_url.get()
    if not url.strip():
        messagebox.showerror("Erro", "Insira um link válido.")
        return
    try:
        response = requests.get(url, timeout=10)
        imagem = Image.open(BytesIO(response.content))
        processar(imagem, "imagem_baixada.jpg")
    except Exception as e:
        messagebox.showerror("Erro ao baixar", str(e))

# === Processar EXIF + Interface ===
def processar(imagem, nome):
    global ultimo_link, imagem_atual
    imagem_atual = imagem
    saida.config(state="normal")
    saida.delete(1.0, tk.END)
    texto, ultimo_link = extrair_exif(imagem)
    saida.insert(tk.END, texto + "\n\n🌐 Pesquisas online:")
    saida.insert(tk.END, f"\n🔍 Google Reverse Image: https://images.google.com/searchbyimage?image_url={nome}")
    saida.insert(tk.END, f"\n🧽 Yandex Reverse: https://yandex.com/images/search?rpt=imageview&url={nome}")
    saida.config(state="disabled")
    salvar_txt(nome, texto)

def salvar_txt(nome_arquivo, texto):
    nome = os.path.splitext(nome_arquivo)[0] + "_metadados.txt"
    with open(nome, "w", encoding="utf-8") as f:
        f.write(texto)
    messagebox.showinfo("Salvo", f"Metadados salvos como:\n{nome}")

def copiar_link():
    if ultimo_link:
        pyperclip.copy(ultimo_link)
        messagebox.showinfo("Copiado", "Link do Google Maps copiado!")
    else:
        messagebox.showwarning("Aviso", "Nenhum link disponível.")

# === Janela Principal ===
def iniciar_interface():
    splash.destroy()

    janela = tk.Tk()
    janela.title("Analisador EXIF MUZASHI")
    janela.geometry("360x680")
    janela.configure(bg="#ffffff")

    label = tk.Label(janela, text="Analisador de Metadados de Imagem", bg="#ffffff",
                     font=("Arial", 14, "bold"), wraplength=320, justify="center")
    label.pack(pady=15)

    botao = tk.Button(janela, text="📁 Escolher Imagem do Dispositivo", command=abrir_imagem_local,
                      font=("Arial", 12), bg="#007acc", fg="white", height=2, width=30)
    botao.pack(pady=10)

    global campo_url
    campo_url = tk.Entry(janela, font=("Arial", 11), width=36, justify="center")
    campo_url.insert(0, "https://")
    campo_url.pack(pady=5)

    btn_url = tk.Button(janela, text="🌐 Analisar Imagem por Link", command=abrir_imagem_url,
                        font=("Arial", 11), bg="#f57c00", fg="white", height=2, width=30)
    btn_url.pack(pady=5)

    global saida
    saida = scrolledtext.ScrolledText(janela, wrap=tk.WORD, width=42, height=18,
                                      font=("Courier", 10), state="disabled", relief="sunken", bd=2)
    saida.pack(padx=10, pady=10)

    btn_copiar = tk.Button(janela, text="📌 Copiar Link do Google Maps", command=copiar_link,
                           font=("Arial", 12), bg="#4caf50", fg="white", height=2, width=30)
    btn_copiar.pack(pady=10)

    janela.mainloop()

# === Splash com Créditos Corrigido ===
def splash_screen():
    global splash
    splash = tk.Tk()
    splash.title("Bem-vindo")
    splash.geometry("360x400")
    splash.configure(bg="#000000")

    try:
        tk.Label(splash, text="🛠️ Desenvolvido por", font=("Arial", 14), bg="#000000", fg="white").pack(pady=30)
    except:
        tk.Label(splash, text="Desenvolvido por", font=("Arial", 14), bg="#000000", fg="white").pack(pady=30)

    tk.Label(splash, text="MUZASHI 480*", font=("Arial", 22, "bold"), bg="#000000", fg="#00ffcc").pack(pady=5)
    tk.Label(splash, text="Analisador de Metadados e Localização de Imagens", font=("Arial", 10), bg="#000000", fg="gray", wraplength=300, justify="center").pack(pady=20)

    splash.after(2500, iniciar_interface)
    splash.mainloop()

# === Iniciar ===
splash_screen()

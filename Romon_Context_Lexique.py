import tkinter as tk
from tkinter import messagebox
from tkinter import ttk  
import customtkinter as ctk
import os
from pathlib import Path
from google import genai
from google.genai import types
import threading
import re
import arabic_reshaper
from bidi.algorithm import get_display

def ar(text):
    """دالة لإصلاح الحروف العربية وعرضها بشكل متصل وصحيح من اليمين لليسار"""
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)

class My_App:
    def __init__(self, master):
        self.master = master
        self.master.title("Lexique des Romans")
        self.master.geometry("1000x750") 
        self.master.minsize(850, 650)
        
        # الألوان العصرية الداكنة (Catppuccin Palette)
        self.bg_color = "#1E1E2E"       # لون الخلفية الرئيسي
        self.sidebar_color = "#181825"  # لون القائمة الجانبية والصناديق
        self.fg_color = "#CDD6F4"       # لون النصوص الأساسية
        self.btn_color = "#313244"      # لون الأزرار
        self.btn_hover = "#45475A"      # لون الأزرار عند تمرير الماوس
        self.ans_color = "#A6E3A1"      # لون الإجابة
        self.accent_color = "#5E7394"   # لون التحديد

        # إعداد ثيم CustomTkinter
        ctk.set_appearance_mode("dark")
        self.master.configure(fg_color=self.bg_color)
        
        self.hidden_answer = ""
        self.hidden_source = ""
        self.context_choices = []
        self.is_processing = False  # القفل لمنع تكرار الطلبات

        # ================== الاتصال بالـ API ==================
        home_directory = Path.home()
        api_file_path = home_directory / ".EXPLICE_ROMON_API_GEMINI"

        if api_file_path.exists():
            with open(api_file_path, "r") as file:
                self.API_KEY = file.read().strip()
        else:
            messagebox.showerror("Erreur", f"Le fichier caché est introuvable dans :\n{api_file_path}")
            self.master.destroy()
            return

        try:
            self.client = genai.Client(api_key=self.API_KEY)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur d'initialisation du client :\n{e}")
            self.master.destroy()
            return
        
        # ================== تخطيط الواجهة (Layout) ==================
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(1, weight=1)

        # 1. شريط القائمة الجانبية (Sidebar)
        self.sidebar_frame = ctk.CTkFrame(self.master, width=280, corner_radius=0, fg_color=self.sidebar_color)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        logo_label = ctk.CTkLabel(self.sidebar_frame, text="📚 Lexique\nBac Marocain", 
                                  font=ctk.CTkFont(size=24, weight="bold"), text_color=self.fg_color)
        logo_label.grid(row=0, column=0, padx=20, pady=(40, 30))

        btn_font = ctk.CTkFont(size=14, weight="bold")
        
        self.btn_boite = ctk.CTkButton(self.sidebar_frame, text="La Boîte à Merveilles", font=btn_font, height=45, cursor="hand2",
                                       fg_color=self.btn_color, hover_color=self.btn_hover, command=self.la_boite_a_merveilles)
        self.btn_boite.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.btn_antigone = ctk.CTkButton(self.sidebar_frame, text="Antigone", font=btn_font, height=45, cursor="hand2",
                                          fg_color=self.btn_color, hover_color=self.btn_hover, command=self.antigone)
        self.btn_antigone.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.btn_condamne = ctk.CTkButton(self.sidebar_frame, text="Le Dernier Jour...", font=btn_font, height=45, cursor="hand2",
                                          fg_color=self.btn_color, hover_color=self.btn_hover, command=self.le_dernier_jour_d_un_condamne)
        self.btn_condamne.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        # 2. الإطار الرئيسي (Main View)
        self.main_frame = ctk.CTkFrame(self.master, corner_radius=0, fg_color=self.bg_color)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.show_welcome_screen()

    # ================== وظائف واجهة المستخدم الديناميكية ==================

    def show_welcome_screen(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        welcome_label = ctk.CTkLabel(self.main_frame, text="👋 Bienvenue dans le Lexique", 
                                     font=ctk.CTkFont(size=30, weight="bold"), text_color=self.fg_color)
        welcome_label.pack(expand=True, pady=(0, 10))

        sub_label = ctk.CTkLabel(self.main_frame, text="Veuillez sélectionner un roman depuis le menu à gauche.", 
                                 font=ctk.CTkFont(size=16), text_color=self.accent_color)
        sub_label.pack(expand=True, pady=(0, 150))

    def build_novel_view(self, romon_name, file_name, chapters=None):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        header_label = ctk.CTkLabel(self.main_frame, text=f"📖 {romon_name}", 
                                    font=ctk.CTkFont(size=24, weight="bold"), text_color=self.fg_color)
        header_label.pack(pady=(20, 10))

        if chapters:
            chap_label = ctk.CTkLabel(self.main_frame, text="Sélectionnez un chapitre :", 
                                       font=ctk.CTkFont(size=13, weight="bold"), text_color=self.accent_color)
            chap_label.pack(anchor="w", padx=40, pady=(10, 2))

            chap_frame = ctk.CTkFrame(self.main_frame, fg_color=self.sidebar_color, corner_radius=10, height=120)
            chap_frame.pack(pady=(0, 10), fill="x", padx=40)
            chap_frame.pack_propagate(False) 

            chap_scrollbar = ctk.CTkScrollbar(chap_frame)
            chap_scrollbar.pack(side="right", fill="y", padx=5, pady=5)

            chapitre_listbox = tk.Listbox(chap_frame, font=("Arial", 12), bg=self.sidebar_color, fg=self.fg_color, 
                                          selectbackground=self.accent_color, selectforeground=self.fg_color, 
                                          bd=0, highlightthickness=0, yscrollcommand=chap_scrollbar.set)
            chapitre_listbox.pack(side="left", fill="both", expand=True, padx=15, pady=10)
            chap_scrollbar.configure(command=chapitre_listbox.yview)

            for chap in chapters:
                chapitre_listbox.insert(tk.END, chap)

        search_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        search_container.pack(pady=15, fill="x", padx=40)

        word_entry = ctk.CTkEntry(search_container, font=ctk.CTkFont(size=14), height=40,
                                  placeholder_text="Entrez le mot ou la phrase à chercher...", 
                                  fg_color=self.btn_color, border_color=self.accent_color, border_width=1)
        word_entry.pack(side="left", expand=True, fill="x", padx=(0, 15))

        search_button = ctk.CTkButton(search_container, text="🔍 Chercher", font=ctk.CTkFont(size=14, weight="bold"), cursor="hand2",
                                      height=40, fg_color=self.accent_color, hover_color=self.btn_hover,
                                      command=lambda: self.search_word_context(word_entry, result_listbox, file_name))
        search_button.pack(side="right")

        list_frame = ctk.CTkFrame(self.main_frame, fg_color=self.sidebar_color, corner_radius=10)
        list_frame.pack(pady=10, fill="both", expand=True, padx=40)

        scrollbar = ctk.CTkScrollbar(list_frame)
        scrollbar.pack(side="right", fill="y", padx=5, pady=5)

        result_listbox = tk.Listbox(list_frame, font=("Arial", 12), bg=self.sidebar_color, fg=self.fg_color, 
                                    selectbackground=self.accent_color, selectforeground=self.fg_color, 
                                    bd=0, highlightthickness=0, yscrollcommand=scrollbar.set)
        result_listbox.pack(side="left", fill="both", expand=True, padx=15, pady=15)
        scrollbar.configure(command=result_listbox.yview)

        explanation_box = ctk.CTkTextbox(self.main_frame, font=("Arial", 14), height=130,
                                         fg_color=self.sidebar_color, text_color=self.ans_color,
                                         border_width=1, border_color=self.accent_color, corner_radius=10,
                                         wrap="word")
        explanation_box.pack(pady=(10, 20), fill="x", padx=40)
        
        initial_text = ar("Sélectionnez une occurrence dans la liste ci-dessus pour l'expliquer via Gemini...")
        explanation_box.insert("1.0", initial_text)
        explanation_box.configure(state="disabled")

        result_listbox.bind("<<ListboxSelect>>", lambda event: self.on_context_select(event, result_listbox, word_entry, explanation_box, romon_name))


    # ================== استدعاء الواجهات ==================
    
    def la_boite_a_merveilles(self):
        chapitres = [f"Chapitre {i}" for i in range(1, 13)]
        self.build_novel_view("La Boîte à Merveilles", "la boite a merveilles.txt", chapitres)

    def antigone(self):
        self.build_novel_view("Antigone", "Antigone.txt", chapters=None)

    def le_dernier_jour_d_un_condamne(self):
        chapitres = [f"Chapitre {i}" for i in range(1, 50)] 
        self.build_novel_view("Le Dernier Jour d'un Condamné", "Le dernier jour d'un condamne.txt", chapitres)


    # ================== المنطق الأساسي ==================

    def update_textbox_content(self, textbox_widget, content_text, text_color):
        def action():
            textbox_widget.configure(state="normal")
            textbox_widget.delete("1.0", tk.END)
            textbox_widget.insert("1.0", content_text)
            textbox_widget.configure(text_color=text_color, state="disabled")
        self.master.after(0, action)

    def search_word_context(self, word_entry, result_listbox, file_name):
        target_phrase = word_entry.get().strip().lower()
        if not target_phrase:
            messagebox.showwarning("Attention", "Veuillez saisir un mot !")
            return

        result_listbox.delete(0, tk.END)
        self.context_choices = []

        project_path = Path("/home/anass/Documents/Programming_projects/python projects/ROMON_Apps")
        target_file_path = project_path / file_name

        if not target_file_path.exists():
            messagebox.showerror("Erreur", f"Le fichier '{file_name}' est introuvable dans :\n{project_path}")
            return

        try:
            with open(target_file_path, "r", encoding="utf-8") as file:
                full_text = file.read()

            all_words = full_text.split()
            target_words = target_phrase.split()
            n_target = len(target_words)

            cleaned_words = []
            for w in all_words:
                w_low = w.lower()
                cleaned_prefix = re.sub(r"^(l|d|j|m|t|s|qu)'", "", w_low)
                final_cleaned_word = re.sub(r'[^\w]', '', cleaned_prefix)
                cleaned_words.append(final_cleaned_word)

            i = 0
            while i <= len(cleaned_words) - n_target:
                if cleaned_words[i : i + n_target] == target_words:
                    start_index = max(0, i - 7)
                    end_index = min(len(all_words), i + n_target + 7)
                    context_chunk = all_words[start_index : end_index]
                    context_sentence = " ".join(context_chunk)
                    
                    self.context_choices.append(context_sentence)
                    result_listbox.insert(tk.END, f"Occurence {len(self.context_choices)}: {context_sentence}...")
                i += 1

            if not self.context_choices:
                result_listbox.insert(tk.END, "Aucun résultat trouvé pour ce mot.")

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur de lecture :\n{e}")

    def on_context_select(self, event, result_listbox, word_entry, explanation_box, romon_name):
        # التحقق من القفل
        if self.is_processing:
            return
            
        selection = result_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index >= len(self.context_choices):
            return

        self.is_processing = True # قفل العملية
        selected_context = self.context_choices[index]
        target_word = word_entry.get().strip()

        waiting_msg = ar("Analyse en cours par Gemini API... Veuillez patienter. | جاري التحليل، يرجى الانتظار...")
        self.update_textbox_content(explanation_box, waiting_msg, self.accent_color)

        ai_thread = threading.Thread(target=self.fetch_ai_explanation, args=(target_word, selected_context, explanation_box, romon_name))
        ai_thread.daemon = True
        ai_thread.start()

    def fetch_ai_explanation(self, word, context, explanation_box, romon):
        prompt = (
            f"Tu es un professeur de français expert du programme du bac marocain. "
            f"Explique le sens du mot ou de l'expression '{word}' basé sur ce contexte extrait du roman '{romon}' : '{context}'. "
            f"Utilise une approche pédagogique bilingue : explique principalement en français, mais intègre des mots ou des termes en arabe lorsque cela aide à mieux comprendre les nuances littéraires ou le sens profond. "
            f"Pour terminer, ajoute une brève synthèse ou une traduction claire en arabe pour confirmer ma compréhension. "
            f"Sois concis, clair et structuré (maximum 4 phrases au total)."
        )

        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            ai_response_text = ar(response.text.strip()) 
            self.update_textbox_content(explanation_box, ai_response_text, self.ans_color)

        except Exception as e:
            error_str = str(e)
        
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                user_friendly_error = ar(
                    "Trop de requêtes simultanées ! Veuillez patienter 20 à 30 secondes avant de cliquer sur un autre mot.\n\n"
                    "لقد أرسلت الكثير من الطلبات في وقت قصير! يرجى الانتظار من 20 إلى 30 ثانية قبل الضغط على كلمة أخرى."
                )
                self.update_textbox_content(explanation_box, user_friendly_error, "#F38BA8")
            else:
                error_msg = f"Impossible de récupérer l'explication :\n{e}"
                self.update_textbox_content(explanation_box, ar(error_msg), "#F38BA8")
        
        finally:
            self.is_processing = False # فتح القفل عند الانتهاء


if __name__ == "__main__":
    root = ctk.CTk()
    app = My_App(root)
    root.mainloop()
